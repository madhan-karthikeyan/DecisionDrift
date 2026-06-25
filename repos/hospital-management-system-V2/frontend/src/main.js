import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/theme.css'
import './assets/main.css'

const app = createApp(App)

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]:', err)
  console.error('[Vue Error Info]:', info)
}

app.use(router)
app.mount('#app')
