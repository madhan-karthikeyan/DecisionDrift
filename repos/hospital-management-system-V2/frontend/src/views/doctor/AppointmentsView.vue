<template>
  <div class="page-header-gradient animate-fadeIn">
    <h1>My Appointments</h1>
    <p>View and manage your scheduled appointments</p>
  </div>

  <div class="stats-grid animate-scaleIn">
    <div class="stat-card">
      <div class="stat-icon stat-icon-primary">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="3" y1="10" x2="21" y2="10"></line>
        </svg>
      </div>
      <div class="stat-content">
        <h4>Today</h4>
        <div class="value">{{ stats.today || 0 }}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon stat-icon-warning">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      </div>
      <div class="stat-content">
        <h4>Pending</h4>
        <div class="value">{{ stats.pending || 0 }}</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon stat-icon-success">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      </div>
      <div class="stat-content">
        <h4>Completed</h4>
        <div class="value">{{ stats.completed || 0 }}</div>
      </div>
    </div>
  </div>

  <div v-if="loading" class="loading-container">
    <div class="spinner"></div>
    <span>Loading appointments...</span>
  </div>

  <div v-if="message" :class="['alert', 'animate-fadeIn', messageType === 'success' ? 'alert-success' : 'alert-danger']">{{ message }}</div>

  <div v-if="!loading" class="table-card animate-scaleIn">
    <table class="data-table">
      <thead>
        <tr>
          <th>Patient</th>
          <th>Date</th>
          <th>Time</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="appt in appointments" :key="appt.id">
          <td>{{ appt.patient_name }}</td>
          <td>{{ appt.date }}</td>
          <td>{{ appt.time_range }}</td>
          <td>
            <span :class="['badge', getStatusClass(appt.status)]">{{ appt.status }}</span>
          </td>
          <td class="actions-cell">
            <button v-if="appt.status === 'booked'" @click="viewDiagnosis(appt.id)" class="btn-diagnosis">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              Add Diagnosis
            </button>
            <button v-if="appt.status === 'booked'" @click="cancelAppointment(appt.id)" class="btn-cancel">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
              Cancel
            </button>
            <button v-if="appt.status === 'completed'" @click="viewDiagnosis(appt.id)" class="btn-diagnosis">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              View Diagnosis
            </button>
            <button @click="viewPatientHistory(appt.patient_id, appt.patient_name)" class="btn-history">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              View History
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Patient History Modal -->
  <BaseModal v-model="showHistoryModal" title="" size="xl">
    <template #header>
      <div class="history-modal-header">
        <div class="header-content">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
          <h2>Patient History: {{ selectedPatientName }}</h2>
        </div>
      </div>
    </template>

    <div v-if="historyLoading" class="history-loading">
      <div class="spinner"></div>
      <span>Loading patient history...</span>
    </div>

    <div v-else-if="patientHistory" class="history-content">
      <!-- Patient Info -->
      <div class="patient-info-card">
        <h3>Patient Information</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Name</span>
            <span class="info-value">{{ patientHistory.patient?.name || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Age</span>
            <span class="info-value">{{ patientHistory.patient?.age || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Blood Type</span>
            <span class="info-value">{{ patientHistory.patient?.blood_type || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Gender</span>
            <span class="info-value">{{ patientHistory.patient?.gender || 'N/A' }}</span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="history-tabs">
        <button
          :class="['tab-btn', { active: activeTab === 'visits' }]"
          @click="activeTab = 'visits'"
        >
          Past Visits
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'diagnoses' }]"
          @click="activeTab = 'diagnoses'"
        >
          Diagnoses
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'prescriptions' }]"
          @click="activeTab = 'prescriptions'"
        >
          Prescriptions
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Visits -->
        <div v-if="activeTab === 'visits'" class="tab-pane">
          <div v-if="patientHistory.visits?.length === 0" class="no-records">
            No visits recorded
          </div>
          <div v-else class="records-list">
            <div v-for="(visit, index) in patientHistory.visits" :key="index" class="record-card">
              <div class="record-header">
                <span class="record-date">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  {{ visit.date }} at {{ visit.time }}
                </span>
                <span :class="['badge', getStatusClass(visit.status)]">{{ visit.status }}</span>
              </div>
              <div class="record-body">
                <p><strong>Type:</strong> {{ visit.type || 'N/A' }}</p>
                <p><strong>Diagnosis:</strong> {{ visit.diagnosis || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Diagnoses -->
        <div v-if="activeTab === 'diagnoses'" class="tab-pane">
          <div v-if="patientHistory.diagnoses?.length === 0" class="no-records">
            No diagnoses recorded
          </div>
          <div v-else class="records-list">
            <div v-for="(diagnosis, index) in patientHistory.diagnoses" :key="index" class="record-card diagnosis-card">
              <div class="record-header">
                <span class="record-date">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  {{ diagnosis.date }}
                </span>
              </div>
              <div class="record-body">
                <p><strong>Diagnosis:</strong> {{ diagnosis.diagnosis }}</p>
                <p><strong>Severity:</strong> {{ diagnosis.severity || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Prescriptions -->
        <div v-if="activeTab === 'prescriptions'" class="tab-pane">
          <div v-if="patientHistory.prescriptions?.length === 0" class="no-records">
            No prescriptions issued
          </div>
          <div v-else class="records-list">
            <div v-for="(prescription, index) in patientHistory.prescriptions" :key="index" class="record-card prescription-card">
              <div class="record-header">
                <span class="record-date">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  {{ prescription.date }}
                </span>
              </div>
              <div class="record-body">
                <p><strong>Medicine:</strong> {{ prescription.medicine || 'N/A' }}</p>
                <p><strong>Dosage:</strong> {{ prescription.dosage || 'N/A' }}</p>
                <p><strong>Frequency:</strong> {{ prescription.frequency || 'N/A' }}</p>
                <p><strong>Duration:</strong> {{ prescription.duration || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="no-records">
      Unable to load patient history
    </div>
  </BaseModal>

</template>

<script>

import { appointmentsAPI, doctorAPI } from '../../api/appointments'
import BaseModal from '../../components/ui/BaseModal.vue'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'DoctorAppointmentsView',
  components: {
    BaseModal
  },

  data() {
    return {
      appointments: [],
      stats: {},
      loading: false,
      message: '',
      messageType: '',
      // Modal state
      showHistoryModal: false,
      selectedPatientName: '',
      patientHistory: null,
      historyLoading: false,
      activeTab: 'visits'
    }
  },
  mounted() {
    this.loadAppointments()
  },
  methods: {
    async loadAppointments() {
      this.loading = true
      try {
        const response = await appointmentsAPI.getDoctorAppointments()
        this.appointments = response.data
        // Calculate stats
        const today = new Date().toISOString().split('T')[0]
        this.stats.today = this.appointments.filter(a => a.date === today).length
        this.stats.pending = this.appointments.filter(a => a.status === 'booked').length
        this.stats.completed = this.appointments.filter(a => a.status === 'completed').length
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load appointments', 'danger')
      } finally {
        this.loading = false
      }
    },
    async completeAppointment(id) {
      try {
        await appointmentsAPI.completeAppointment(id)
        this.showMessage('Appointment marked as completed', 'success')
        this.loadAppointments()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to complete appointment', 'danger')
      }
    },
    async cancelAppointment(id) {
      const confirmed = await dialog.confirm('Cancel this appointment?')
      if (!confirmed) return
      try {
        await appointmentsAPI.cancelAppointment(id)
        this.showMessage('Appointment cancelled', 'success')
        this.loadAppointments()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to cancel appointment', 'danger')
      }
    },
    viewDiagnosis(id) {
      this.$router.push(`/doctor/appointment/${id}/diagnosis`)
    },
    async viewPatientHistory(patientId, patientName) {
      this.selectedPatientName = patientName
      this.showHistoryModal = true
      this.historyLoading = true
      this.patientHistory = null
      this.activeTab = 'visits'

      try {
        const response = await doctorAPI.getPatientHistory(patientId)
        this.patientHistory = response.data
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load patient history', 'danger')
      } finally {
        this.historyLoading = false
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
  background: var(--color-primary);
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-xl);
  color: var(--color-white);
}

.page-header-gradient h1 {
  color: var(--color-white);
  margin-bottom: var(--space-xs);
}

.page-header-gradient p {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: var(--font-size-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}

.stat-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon-primary {
  background: var(--color-primary-light);
}

.stat-icon-warning {
  background: var(--color-warning-light);
}

.stat-icon-success {
  background: var(--color-success-light);
}

.stat-content h4 {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-content .value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  gap: var(--space-lg);
  color: var(--color-text-secondary);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-gray-300);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease forwards;
}

.animate-scaleIn {
  animation: scaleIn 0.35s ease forwards;
}

.table-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--bg-secondary);
}

.data-table th {
  padding: var(--space-base);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-color);
}

.data-table td {
  padding: var(--space-base);
  border-bottom: 1px solid var(--color-gray-200);
}

.data-table tbody tr {
  transition: background var(--transition-base);
}

.data-table tbody tr:hover {
  background: var(--color-gray-100);
}

.actions-cell {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

/* Complete Button */
.btn-complete {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-success);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 6px var(--color-success-shadow);
}

.btn-complete:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px var(--color-success-shadow-md);
}

.btn-complete svg {
  width: 14px;
  height: 14px;
}

/* Cancel Button */
.btn-cancel {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-danger);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 6px var(--color-danger-shadow);
}

.btn-cancel:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px var(--color-danger-shadow-md);
}

.btn-cancel svg {
  width: 14px;
  height: 14px;
}

/* Diagnosis Button */
.btn-diagnosis {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 6px var(--color-primary-shadow);
}

.btn-diagnosis:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px var(--color-primary-shadow-md);
}

.btn-diagnosis svg {
  width: 14px;
  height: 14px;
}

.btn-icon {
  margin-right: var(--space-xs);
}

.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge-warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.badge-danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

/* History Button */
.btn-history {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-teal);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 6px var(--color-teal-shadow);
}

.btn-history:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px var(--color-teal-shadow-md);
  background: var(--color-teal-dark);
}

.btn-history svg {
  width: 14px;
  height: 14px;
}

/* Modal Styles */
.history-modal-header {
  background: linear-gradient(135deg, var(--color-teal), var(--color-teal-dark));
  padding: var(--space-lg) var(--space-xl);
  margin: calc(-1 * var(--space-lg)) calc(-1 * var(--space-lg)) var(--space-lg);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  color: var(--color-white);
}

.history-modal-header .header-content {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.history-modal-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-white);
}

.history-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  gap: var(--space-lg);
  color: var(--color-text-secondary);
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.patient-info-card {
  background: var(--color-gray-50);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  border-left: 4px solid var(--color-teal);
}

.patient-info-card h3 {
  margin: 0 0 var(--space-md) 0;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-md);
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

/* Tabs */
.history-tabs {
  display: flex;
  gap: var(--space-sm);
  border-bottom: 2px solid var(--color-gray-200);
}

.tab-btn {
  padding: var(--space-md) var(--space-lg);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
}

.tab-btn:hover {
  color: var(--color-teal);
}

.tab-btn.active {
  color: var(--color-teal);
  border-bottom-color: var(--color-teal);
}

.tab-content {
  padding: var(--space-lg) 0;
}

.tab-pane {
  animation: fadeIn 0.2s ease;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.record-card {
  background: var(--color-gray-50);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  border-left: 4px solid var(--color-teal);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.record-date {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.record-body p {
  margin: var(--space-xs) 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.record-body strong {
  color: var(--color-text-secondary);
}

.diagnosis-card {
  border-left-color: var(--color-amber);
}

.prescription-card {
  border-left-color: var(--color-violet);
}

.no-records {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-secondary);
}

.alert {
  padding: var(--space-base) var(--space-lg);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-lg);
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
</style>
