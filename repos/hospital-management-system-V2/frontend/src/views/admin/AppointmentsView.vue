<template>
  <div class="admin-page">
    <!-- Page Header -->
    <div class="page-header-gradient">
      <div class="header-content">
        <h1>Appointments</h1>
        <p>View and manage all appointments</p>
      </div>
    </div>

    <!-- Alerts -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading appointments...</p>
    </div>

    <div v-if="message" :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']">
      {{ message }}
    </div>

    <!-- Data Table -->
    <div class="table-card" v-if="!loading">
      <table class="data-table">
        <thead>
          <tr>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Date</th>
            <th>Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="appt in appointments" :key="appt.id">
            <td>
              <div class="patient-name">{{ appt.patient_name }}</div>
            </td>
            <td>{{ appt.doctor_name }}</td>
            <td>{{ appt.date }}</td>
            <td>{{ appt.time }}</td>
            <td>
              <span :class="['badge', getStatusClass(appt.status)]">{{ appt.status }}</span>
            </td>
          </tr>
          <tr v-if="appointments.length === 0">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <p>No appointments found</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>

import { appointmentsAPI } from '../../api/appointments'

export default {
  name: 'AdminAppointmentsView',

  data() {
    return {
      appointments: [],
      loading: false,
      message: '',
      messageType: ''
    }
  },
  mounted() {
    this.loadAppointments()
  },
  methods: {
    async loadAppointments() {
      this.loading = true
      try {
        const response = await appointmentsAPI.getAllAdmin()
        this.appointments = response.data
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load appointments', 'danger')
      } finally {
        this.loading = false
      }
    },
    getStatusClass(status) {
      const s = status?.toLowerCase()
      if (s === 'completed') return 'badge-success'
      if (s === 'cancelled') return 'badge-danger'
      if (s === 'booked' || s === 'scheduled') return 'badge-warning'
      return 'badge-info'
    },
    showMessage(msg, type) {
      this.message = msg
      this.messageType = type
      setTimeout(() => { this.message = '' }, 5000)
    }
  }
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  animation: fadeIn 0.3s ease;
}

/* Gradient Header */
.page-header-gradient {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, var(--color-header-gradient-start) 0%, var(--color-header-gradient-end) 100%);
  padding: var(--space-lg) var(--space-xl);
  border-radius: var(--radius-lg);
  color: var(--color-white);
}

.header-content h1 {
  color: var(--color-white);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--space-xs);
}

.header-content p {
  margin: 0;
  opacity: 0.8;
  font-size: var(--font-size-sm);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  background: var(--color-white);
  border-radius: var(--radius-lg);
}

.loading-state .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-state p {
  margin-top: var(--space-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Table Card */
.table-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-base);
  overflow: hidden;
  animation: scaleIn 0.35s ease;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: var(--color-gray-50);
  padding: var(--space-md) var(--space-base);
  text-align: left;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--color-gray-200);
}

.data-table td {
  padding: var(--space-md) var(--space-base);
  border-bottom: 1px solid var(--color-gray-100);
}

.data-table tbody tr:hover {
  background: var(--color-gray-50);
}

.patient-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

/* Badge */
.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-sm);
}

.badge-info {
  background: var(--color-info-light);
  color: var(--color-info-dark);
}

.badge-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge-danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.badge-warning {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}

/* Empty State */
.empty-cell {
  text-align: center;
  padding: var(--space-2xl) !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  color: var(--color-text-muted);
}

.empty-state svg {
  opacity: 0.5;
}

/* Alert */
.alert {
  padding: var(--space-md) var(--space-base);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.alert-success {
  background: var(--color-success-light);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.alert-danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .page-header-gradient {
    flex-direction: column;
    gap: var(--space-md);
    text-align: center;
  }
}
</style>
