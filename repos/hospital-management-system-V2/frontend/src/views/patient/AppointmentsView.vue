<template>

    <div class="page-header-gradient">
      <h1>My Appointments</h1>
      <p class="header-subtitle">View and manage your upcoming and past appointments</p>
    </div>

    <div class="tabs-wrapper">
      <div class="tabs">
        <button @click="activeTab = 'upcoming'" :class="['tab', activeTab === 'upcoming' ? 'active' : '']">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          Upcoming
        </button>
        <button @click="activeTab = 'past'" :class="['tab', activeTab === 'past' ? 'active' : '']">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          Past
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading appointments...</p>
    </div>

    <template v-else>
      <div v-if="message" :class="['alert', 'animate-fadeIn', messageType === 'success' ? 'alert-success' : 'alert-danger']">{{ message }}</div>

      <div v-if="activeTab === 'upcoming'" class="card card-elevated animate-fadeIn">
        <table v-if="upcomingAppointments.length > 0" class="data-table">
          <thead>
            <tr>
              <th>Doctor</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="appt in upcomingAppointments" :key="appt.id">
              <td>
                <div class="doctor-cell">
                  <div class="doctor-avatar-small">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                    </svg>
                  </div>
                  {{ appt.doctor?.name }}
                </div>
              </td>
              <td>{{ appt.date }}</td>
              <td>{{ appt.time }}</td>
              <td><span :class="['badge', getStatusClass(appt.status)]">{{ appt.status }}</span></td>
              <td>
                <button @click="cancelAppointment(appt.id)" class="btn btn-sm btn-danger">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                  </svg>
                  Cancel
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          <p>No upcoming appointments</p>
          <router-link to="/patient/doctors" class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Book an Appointment
          </router-link>
        </div>
      </div>

      <div v-if="activeTab === 'past'" class="card card-elevated animate-fadeIn">
        <table v-if="pastAppointments.length > 0" class="data-table">
          <thead>
            <tr>
              <th>Doctor</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="appt in pastAppointments" :key="appt.id">
              <td>
                <div class="doctor-cell">
                  <div class="doctor-avatar-small">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                    </svg>
                  </div>
                  {{ appt.doctor?.name }}
                </div>
              </td>
              <td>{{ appt.date }}</td>
              <td>{{ appt.time }}</td>
              <td><span :class="['badge', getStatusClass(appt.status)]">{{ appt.status }}</span></td>
              <td>
                <button @click="viewAppointmentDetail(appt.id)" class="btn btn-sm btn-detail">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <p>No past appointments</p>
        </div>
      </div>
    </template>

    <!-- Appointment Detail Modal -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal animate-scaleIn">
        <div class="modal-header">
          <h3>Appointment Details</h3>
          <button @click="showDetailModal = false" class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="detailLoading" class="loading-container">
            <div class="spinner"></div>
            <p>Loading details...</p>
          </div>
          <div v-else-if="appointmentDetail" class="detail-content">
            <div class="detail-section">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                Appointment Info
              </h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Date</span>
                  <span class="detail-value">{{ appointmentDetail.date }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Time</span>
                  <span class="detail-value">{{ appointmentDetail.start_time || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Status</span>
                  <span :class="['badge', getStatusClass(appointmentDetail.status)]">{{ appointmentDetail.status }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.reason">
                  <span class="detail-label">Reason</span>
                  <span class="detail-value">{{ appointmentDetail.reason }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                </svg>
                Doctor
              </h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Name</span>
                  <span class="detail-value">{{ appointmentDetail.doctor?.name }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Specialization</span>
                  <span class="detail-value">{{ appointmentDetail.doctor?.specialization }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Department</span>
                  <span class="detail-value">{{ appointmentDetail.doctor?.department }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="appointmentDetail.treatment">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                Diagnosis & Treatment
              </h4>
              <div class="detail-grid">
                <div class="detail-item" v-if="appointmentDetail.treatment.diagnosis">
                  <span class="detail-label">Diagnosis</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.diagnosis }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.treatment.symptoms">
                  <span class="detail-label">Symptoms</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.symptoms }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.treatment.severity">
                  <span class="detail-label">Severity</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.severity }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.treatment.treatment_plan">
                  <span class="detail-label">Treatment Plan</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.treatment_plan }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.treatment.notes">
                  <span class="detail-label">Notes</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.notes }}</span>
                </div>
                <div class="detail-item" v-if="appointmentDetail.treatment.follow_up">
                  <span class="detail-label">Follow-up</span>
                  <span class="detail-value">{{ appointmentDetail.treatment.follow_up }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section" v-if="appointmentDetail.prescription && appointmentDetail.prescription.length > 0">
              <h4>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
                  <path d="m8.5 8.5 7 7"></path>
                </svg>
                Prescription
              </h4>
              <div class="prescription-list">
                <div v-for="(med, index) in appointmentDetail.prescription" :key="index" class="prescription-item">
                  <span class="med-name">{{ med.medicine }}</span>
                  <span class="med-detail" v-if="med.dosage">{{ med.dosage }}</span>
                  <span class="med-detail" v-if="med.frequency">{{ med.frequency }}</span>
                  <span class="med-detail" v-if="med.duration">{{ med.duration }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

</template>

<script>

import { appointmentsAPI } from '../../api/appointments'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'PatientAppointmentsView',

  data() {
    return {
      upcomingAppointments: [],
      pastAppointments: [],
      activeTab: 'upcoming',
      loading: false,
      message: '',
      messageType: '',
      showDetailModal: false,
      appointmentDetail: null,
      detailLoading: false
    }
  },
  mounted() {
    this.loadAppointments()
  },
  updated() {
  },
  methods: {
    async loadAppointments() {
      this.loading = true
      try {
        const response = await appointmentsAPI.getPatientAppointments()
        this.upcomingAppointments = response.data.upcoming || []
        this.pastAppointments = response.data.past || []
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load appointments', 'danger')
      } finally {
        this.loading = false
      }
    },
    async cancelAppointment(id) {
      const confirmed = await dialog.confirm('Cancel this appointment?')
      if (!confirmed) return
      try {
        await appointmentsAPI.cancelPatientAppointment(id)
        this.showMessage('Appointment cancelled', 'success')
        this.loadAppointments()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to cancel appointment', 'danger')
      }
    },
    async viewAppointmentDetail(id) {
      this.showDetailModal = true
      this.detailLoading = true
      this.appointmentDetail = null
      try {
        const response = await appointmentsAPI.getPatientAppointmentDetail(id)
        this.appointmentDetail = response.data
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load appointment details', 'danger')
        this.showDetailModal = false
      } finally {
        this.detailLoading = false
      }
    },
    getStatusClass(status) {
      const s = status?.toLowerCase()
      if (s === 'completed') return 'badge-success'
      if (s === 'cancelled') return 'badge-danger'
      return 'badge-warning'
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
.page-header-gradient {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  padding: var(--space-2xl) var(--space-lg);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-xl);
  box-shadow: var(--shadow-lg);
}

.page-header-gradient h1 {
  color: var(--color-white);
  margin-bottom: var(--space-xs);
}

.header-subtitle {
  opacity: 0.9;
  margin: 0;
  font-size: var(--font-size-base);
}

.tabs-wrapper {
  margin-bottom: var(--space-lg);
}

.tabs {
  display: flex;
  gap: var(--space-sm);
  background: var(--color-white);
  padding: var(--space-xs);
  border-radius: var(--radius-base);
  box-shadow: var(--shadow-sm);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
}

.tab svg {
  width: 18px;
  height: 18px;
}

.tab:hover {
  background: var(--color-gray-100);
  color: var(--color-text-primary);
}

.tab.active {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
}

.card-elevated {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-base);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: var(--color-gray-100);
  padding: var(--space-md) var(--space-base);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: var(--space-md) var(--space-base);
  border-bottom: 1px solid var(--color-gray-200);
  vertical-align: middle;
}

.data-table tr:last-child td {
  border-bottom: none;
}

.data-table tr:hover td {
  background: var(--color-gray-100);
}

.doctor-cell {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-weight: var(--font-weight-medium);
}

.doctor-avatar-small {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.doctor-avatar-small svg {
  width: 18px;
  height: 18px;
  color: var(--color-white);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  color: var(--color-text-secondary);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-gray-300);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-base);
}

.empty-state {
  text-align: center;
  padding: var(--space-3xl);
  color: var(--color-text-secondary);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: var(--space-base);
  opacity: 0.5;
}

.empty-state p {
  margin-bottom: var(--space-lg);
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.btn-sm {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-size: var(--font-size-sm);
}

.btn-sm svg {
  width: 14px;
  height: 14px;
}

.btn-danger {
  background-color: var(--color-danger);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-danger:hover {
  background-color: var(--color-danger);
  filter: brightness(0.85);
}

.alert {
  padding: var(--space-md) var(--space-base);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-lg);
}

.alert-success {
  background-color: var(--color-success-light);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.alert-danger {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-full);
  text-transform: capitalize;
}

.badge-success {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.badge-warning {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.badge-danger {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.btn-detail {
  background-color: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.btn-detail:hover {
  opacity: 0.9;
}

.btn-detail svg {
  width: 14px;
  height: 14px;
}

/* Detail Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-lg);
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--color-gray-200);
  background: var(--color-primary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.modal-header h3 {
  margin: 0;
  color: var(--color-white);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.modal-close {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: var(--color-white);
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xl);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-base);
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body {
  padding: var(--space-xl);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 2px solid var(--color-primary);
}

.detail-section h4 svg {
  width: 18px;
  height: 18px;
  color: var(--color-primary);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.detail-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: var(--font-weight-medium);
}

.detail-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

.prescription-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.prescription-item {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-gray-50);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-primary);
  align-items: center;
}

.med-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.med-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  padding: 2px var(--space-sm);
  background: var(--color-gray-200);
  border-radius: var(--radius-sm);
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-scaleIn {
  animation: scaleIn 0.3s ease-out forwards;
}

@media (max-width: 768px) {
  .data-table {
    font-size: var(--font-size-sm);
  }

  .data-table th,
  .data-table td {
    padding: var(--space-sm);
  }

  .tabs {
    flex-direction: column;
  }

  .tab {
    justify-content: flex-start;
  }
}
</style>
