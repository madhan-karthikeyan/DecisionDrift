<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="`sidebar--${userRole}`">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
        </div>
        <h3 class="sidebar-title">HMS</h3>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item"
            :class="{ 'nav-item--active': isActive(item.path) }">
            <span class="nav-icon" v-html="item.icon"></span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="user-avatar">{{ userInitials }}</div>
          <div class="user-details">
            <span class="user-name">{{ userName }}</span>
            <span class="user-role">{{ userRole }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-wrapper">
      <header class="top-nav">
        <div class="nav-left">
          <h2 class="page-title">{{ currentPageTitle }}</h2>
        </div>
        <div class="nav-right">
          <div class="user-info">
            <span class="welcome-text">Welcome,</span>
            <span class="user-name-highlight">{{ userName }}</span>
            <span class="role-badge" :class="`role-badge--${userRole}`">{{ userRole }}</span>
          </div>
          <button @click="logout" class="logout-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </header>

      <div class="main-content">
        <router-view :key="$route.fullPath" />
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'AppLayout',
  data() {
    return {
      userData: null
    }
  },
  created() {
    this.loadUser()
  },
  computed: {
    user() {
      return this.userData
    },
    userName() {
      return this.user?.username || 'User'
    },
    userRole() {
      return this.user?.role || ''
    },
    userInitials() {
      const name = this.userName
      return name.charAt(0).toUpperCase()
    },
    currentPageTitle() {
      const path = this.$route.path
      if (path.includes('dashboard')) return 'Dashboard'
      if (path.includes('departments')) return 'Departments'
      if (path.includes('doctors')) return 'Doctors'
      if (path.includes('patients')) return 'Patients'
      if (path.includes('appointments')) return 'Appointments'
      if (path.includes('availability')) return 'Availability'
      if (path.includes('profile')) return 'My Profile'
      return 'HMS'
    },
    navItems() {
      const items = []

      // Common items
      items.push({
        path: `/${this.userRole}/dashboard`,
        label: 'Dashboard',
        icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
      })

      if (this.userRole === 'admin') {
        items.push(
          {
            path: '/admin/departments',
            label: 'Departments',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V7l8-4 8 4v14"></path><path d="M9 21v-4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4"></path></svg>'
          },
          {
            path: '/admin/doctors',
            label: 'Doctors',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>'
          },
          {
            path: '/admin/patients',
            label: 'Patients',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
          },
          {
            path: '/admin/appointments',
            label: 'Appointments',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
          }
        )
      } else if (this.userRole === 'doctor') {
        items.push(
          {
            path: '/doctor/appointments',
            label: 'Appointments',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
          },
          {
            path: '/doctor/patients',
            label: 'My Patients',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>'
          },
          {
            path: '/doctor/availability',
            label: 'Availability',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
          },
          {
            path: '/doctor/profile',
            label: 'My Profile',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
          }
        )
      } else if (this.userRole === 'patient') {
        items.push(
          {
            path: '/patient/doctors',
            label: 'Find Doctors',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
          },
          {
            path: '/patient/appointments',
            label: 'My Appointments',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
          },
          {
            path: '/patient/profile',
            label: 'My Profile',
            icon: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
          }
        )
      }

      return items
    }
  },
  methods: {
    loadUser() {
      const userStr = localStorage.getItem('user')
      this.userData = userStr ? JSON.parse(userStr) : null
    },
    isActive(path) {
      return this.$route.path === path || this.$route.path.startsWith(path + '/')
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    },
    applyThemeClass() {
      const role = this.userRole
      document.body.classList.remove('theme-patient', 'theme-doctor', 'theme-admin')
      if (role === 'patient') document.body.classList.add('theme-patient')
      else if (role === 'doctor') document.body.classList.add('theme-doctor')
      else if (role === 'admin') document.body.classList.add('theme-admin')
    }
  },
  mounted() {
    this.applyThemeClass()
  },
  watch: {
    userRole() {
      this.applyThemeClass()
    }
  },
  beforeUnmount() {
    document.body.classList.remove('theme-patient', 'theme-doctor', 'theme-admin')
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-body);
}

/* ===== SIDEBAR ===== */
.sidebar {
  width: 260px;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  background: var(--color-gray-900);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width var(--transition-base);
  z-index: 100;
}

.sidebar--admin {
  background: var(--sidebar-bg);
}

.sidebar--doctor {
  background: var(--sidebar-bg);
}

.sidebar--patient {
  background: var(--sidebar-bg);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  border-radius: var(--radius-base);
  color: var(--color-white);
}

.sidebar-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-white);
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-md);
  overflow-y: auto;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-base);
  color: var(--color-gray-400);
  text-decoration: none;
  border-radius: var(--radius-base);
  transition: all var(--transition-base);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--color-white);
}

.nav-item--active {
  background: var(--color-primary);
  color: var(--color-white);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.sidebar-footer {
  padding: var(--space-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-white);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-sm);
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-details .user-name {
  color: var(--color-white);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.user-details .user-role {
  color: var(--color-gray-400);
  font-size: var(--font-size-xs);
  text-transform: capitalize;
}

/* ===== MAIN CONTENT ===== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: 260px;
  min-height: 100vh;
}

/* ===== TOP NAV ===== */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-base) var(--space-xl);
  background: var(--color-white);
  border-bottom: 1px solid var(--border-color);
  min-height: 65px;
  box-sizing: border-box;
}

/* ===== MAIN CONTENT AREA ===== */
.main-content {
  flex: 1;
  padding: var(--space-xl);
  overflow-y: auto;
  height: calc(100vh - 65px);
  box-sizing: border-box;
}

.nav-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.welcome-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.user-name-highlight {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}

.role-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: capitalize;
}

.role-badge--admin {
  background: var(--color-badge-admin-bg);
  color: var(--color-badge-admin-text);
}

.role-badge--doctor {
  background: var(--color-badge-doctor-bg);
  color: var(--color-badge-doctor-text);
}

.role-badge--patient {
  background: var(--color-badge-patient-bg);
  color: var(--color-badge-patient-text);
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-base);
  background: transparent;
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.logout-btn:hover {
  background: var(--color-danger-light);
  border-color: var(--color-danger);
  color: var(--color-danger);
}

/* Page Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 992px) {
  .sidebar {
    width: 80px;
  }

  .main-wrapper {
    margin-left: 80px;
  }

  .sidebar-header {
    justify-content: center;
    padding: var(--space-md);
  }

  .sidebar-title {
    display: none;
  }

  .nav-label {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: var(--space-md);
  }

  .sidebar-user {
    justify-content: center;
  }

  .user-details {
    display: none;
  }
}

@media (max-width: 768px) {
  .top-nav {
    flex-direction: column;
    gap: var(--space-md);
    align-items: stretch;
  }

  .nav-right {
    justify-content: space-between;
  }
}
</style>
