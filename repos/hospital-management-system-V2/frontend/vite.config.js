import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

/**
 * Derives a clean chunk name from the module's file path.
 *
 * - Views   → "views/admin/DashboardView", "views/doctor/AppointmentsView", etc.
 * - Shared API helpers (src/api/*) → "core/appointments", "core/doctors", etc.
 * - Components → "components/AppLayout", "components/ui/BaseModal", etc.
 * - Router  → "core/router"
 * - node_modules → "vendor/<package-name>"
 * - Anything else → file's base name
 *
 * Because the folder path is baked into the name, files like
 *   views/admin/DashboardView.js
 *   views/doctor/DashboardView.js
 *   views/patient/DashboardView.js
 * never collide.
 */
function deriveChunkName(moduleId) {
  // Vendor / node_modules
  if (moduleId.includes('node_modules')) {
    const parts = moduleId.split('node_modules/')
    const pkg = parts[parts.length - 1].split('/')[0].replace('@', '')
    return `vendor/${pkg}`
  }

  // Normalise to forward slashes and grab the part after src/
  const normalised = moduleId.split('?')[0].replace(/\\/g, '/')
  const srcIndex = normalised.indexOf('/src/')
  if (srcIndex === -1) return path.basename(normalised, path.extname(normalised))

  // e.g. "views/admin/DashboardView.vue" or "api/doctors.js"
  let relative = normalised.slice(srcIndex + '/src/'.length)
  const ext = path.extname(relative)
  relative = relative.slice(0, -ext.length) // strip extension

  // Map src/api/* → core/*
  if (relative.startsWith('api/')) {
    return `core/${relative.slice('api/'.length)}`
  }
  // Map src/router/* → core/router
  if (relative.startsWith('router/')) {
    return `core/${relative.slice('router/'.length)}`
  }
  // Map src/composables/* → core/*
  if (relative.startsWith('composables/')) {
    return `core/${relative.slice('composables/'.length)}`
  }

  // views/*, components/* keep their path as-is
  return relative
}

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        // Entry point (main.js)
        entryFileNames: 'assets/js/[name].js',

        // Dynamic-import / route chunks
        chunkFileNames(chunkInfo) {
          const name = chunkInfo.name || 'chunk'

          // If Rollup already assigned a meaningful name (from the router
          // dynamic imports), try to enrich it with folder context.
          if (chunkInfo.facadeModuleId) {
            const clean = deriveChunkName(chunkInfo.facadeModuleId)
            return `assets/js/${clean}.js`
          }

          // Shared chunks split out by Rollup (e.g. common code between routes)
          if (name.startsWith('vendor')) {
            return `assets/${name}.js`
          }

          return `assets/js/${name}.js`
        },

        // CSS & static assets
        assetFileNames(assetInfo) {
          const name = assetInfo.name || ''
          const ext = name.split('.').pop()

          if (/css/.test(ext)) {
            return 'assets/css/[name].[ext]'
          }
          if (/png|jpe?g|gif|svg|webp|ico/.test(ext)) {
            return 'assets/images/[name].[ext]'
          }
          if (/woff2?|eot|ttf|otf/.test(ext)) {
            return 'assets/fonts/[name].[ext]'
          }
          return 'assets/[name].[ext]'
        },

        // Split vendor libs into their own chunk so app code stays lean
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue-router')) return 'vendor/vue-router'
            if (id.includes('vue'))        return 'vendor/vue'
            if (id.includes('axios'))      return 'vendor/axios'
            // Catch-all for other deps
            const parts = id.split('node_modules/')
            const pkg = parts[parts.length - 1].split('/')[0].replace('@', '')
            return `vendor/${pkg}`
          }
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
