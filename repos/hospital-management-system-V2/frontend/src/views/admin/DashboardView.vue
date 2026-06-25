<template>
  <div class="dashboard">
    <!-- Page Header with Gradient -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1>Dashboard</h1>
        <p>Welcome back! Here's what's happening today.</p>
      </div>
      <div class="header-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
      </div>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading dashboard...</p>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Stats Grid -->
    <div v-if="!loading" class="stats-grid">
      <div class="stat-card-item" style="--delay: 0">
        <div class="stat-card-icon stat-card-icon--primary">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
        </div>
        <div class="stat-card-content">
          <span class="stat-label">Total Doctors</span>
          <span class="stat-value">{{ stats.doctors || 0 }}</span>
        </div>
      </div>

      <div class="stat-card-item" style="--delay: 1">
        <div class="stat-card-icon stat-card-icon--success">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        </div>
        <div class="stat-card-content">
          <span class="stat-label">Total Patients</span>
          <span class="stat-value">{{ stats.patients || 0 }}</span>
        </div>
      </div>

      <div class="stat-card-item" style="--delay: 2">
        <div class="stat-card-icon stat-card-icon--warning">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="stat-card-content">
          <span class="stat-label">Appointments</span>
          <span class="stat-value">{{ stats.appointments || 0 }}</span>
        </div>
      </div>

      <div class="stat-card-item" style="--delay: 3">
        <div class="stat-card-icon stat-card-icon--info">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 21h18"></path>
            <path d="M5 21V7l8-4 8 4v14"></path>
            <path d="M9 21v-4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4"></path>
          </svg>
        </div>
        <div class="stat-card-content">
          <span class="stat-label">Departments</span>
          <span class="stat-value">{{ stats.departments || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions for Admin -->
    <div v-if="userRole === 'admin' && !loading" class="quick-actions">
      <div class="section-header">
        <h2>Quick Actions</h2>
        <p>Manage your hospital efficiently</p>
      </div>
      <div class="actions-grid">
        <router-link to="/admin/departments" class="action-card">
          <div class="action-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 21h18"></path>
              <path d="M5 21V7l8-4 8 4v14"></path>
              <path d="M9 21v-4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4"></path>
            </svg>
          </div>
          <span>Departments</span>
        </router-link>
        <router-link to="/admin/doctors" class="action-card">
          <div class="action-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <span>Doctors</span>
        </router-link>
        <router-link to="/admin/patients" class="action-card">
          <div class="action-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
            </svg>
          </div>
          <span>Patients</span>
        </router-link>
        <router-link to="/admin/appointments" class="action-card">
          <div class="action-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
            </svg>
          </div>
          <span>Appointments</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { adminAPI } from '../../api/appointments'

export default {
  name: 'DashboardView',
  data() {
    return {
      stats: {},
      loading: false,
      error: ''
    }
  },
  computed: {
    userRole() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      return user.role
    }
  },
  mounted() {
    this.loadDashboard()
  },
  methods: {
    async loadDashboard() {
      this.loading = true
      this.error = ''
      try {
        const response = await adminAPI.getDashboard()
        this.stats = response.data
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to load dashboard'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  animation: fadeIn 0.3s ease;
}

/* Header with Gradient */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, var(--color-header-gradient-start) 0%, var(--color-header-gradient-end) 100%);
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  color: var(--color-white);
}

.header-content h1 {
  color: var(--color-white);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--space-xs);
}

.header-content p {
  margin: 0;
  opacity: 0.9;
  font-size: var(--font-size-sm);
}

.header-icon {
  opacity: 0.3;
}

.header-icon svg {
  width: 64px;
  height: 64px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  color: var(--color-text-muted);
}

.loading-state .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: var(--space-md);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}

.stat-card-item {
  display: flex;
  align-items: center;
  gap: var(--space-base);
  padding: var(--space-lg);
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-base);
  transition: all var(--transition-base);
  animation: slideInUp 0.4s ease backwards;
  animation-delay: calc(var(--delay) * 0.1s);
}

.stat-card-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.stat-card-icon--primary {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.stat-card-icon--success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.stat-card-icon--warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-card-icon--info {
  background: var(--color-info-light);
  color: var(--color-info);
}

.stat-card-content {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

/* Quick Actions */
.quick-actions {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  box-shadow: var(--shadow-base);
}

.section-header {
  margin-bottom: var(--space-lg);
}

.section-header h2 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin: 0 0 var(--space-xs);
  color: var(--color-text-primary);
}

.section-header p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-base);
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  text-decoration: none;
  color: var(--color-text-primary);
  transition: all var(--transition-base);
}

.action-card:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
  transform: translateY(-2px);
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--color-white);
  border-radius: var(--radius-base);
  box-shadow: var(--shadow-sm);
}

.action-card span {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    text-align: center;
    gap: var(--space-md);
  }

  .header-icon {
    display: none;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
