<template>
  <div class="patient-history-page">
    <!-- Page Header -->
    <div class="page-header-gradient animate-fadeIn">
      <button @click="goBack" class="btn-back">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        Back
      </button>
      <div class="header-content">
        <h1>Patient Medical History</h1>
        <p v-if="patientName">View medical records for {{ patientName }}</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <span>Loading patient history...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <p>{{ error }}</p>
      <button @click="goBack" class="btn btn-primary">Go Back</button>
    </div>

    <!-- Patient Info & History Tabs -->
    <div v-else class="history-container animate-scaleIn">
      <!-- Patient Info Card -->
      <div class="patient-info-card" v-if="patientInfo">
        <div class="patient-avatar">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div class="patient-details">
          <h2>{{ patientInfo.name }}</h2>
          <div class="patient-meta">
            <span v-if="patientInfo.age">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              </svg>
              Age: {{ patientInfo.age }}
            </span>
            <span v-if="patientInfo.gender">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              {{ patientInfo.gender }}
            </span>
            <span v-if="patientInfo.blood_type" class="blood-badge">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
                <path d="M12 6v6l4 2"></path>
              </svg>
              Blood: {{ patientInfo.blood_type }}
            </span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-container">
        <div class="tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            <span class="tab-icon" v-html="tab.icon"></span>
            {{ tab.label }}
            <span class="tab-count" v-if="getTabCount(tab.id) > 0">{{ getTabCount(tab.id) }}</span>
          </button>
        </div>
      </div>

      <!-- Tab Contents -->
      <div class="tab-content">
        <!-- Visits Tab -->
        <div v-show="activeTab === 'visits'" class="tab-pane">
          <div v-if="visits.length === 0" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            <p>No visits recorded</p>
          </div>
          <table v-else class="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Type</th>
                <th>Diagnosis</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(visit, index) in visits" :key="index">
                <td>{{ visit.date || 'N/A' }}</td>
                <td>{{ visit.time || 'N/A' }}</td>
                <td>{{ visit.type || 'Consultation' }}</td>
                <td>{{ visit.diagnosis || 'No diagnosis recorded' }}</td>
                <td>
                  <span :class="['status-badge', getStatusClass(visit.status)]">
                    {{ visit.status || 'Unknown' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Diagnoses Tab -->
        <div v-show="activeTab === 'diagnoses'" class="tab-pane">
          <div v-if="diagnoses.length === 0" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
            </svg>
            <p>No diagnoses recorded</p>
          </div>
          <div v-else class="diagnoses-grid">
            <div v-for="(diagnosis, index) in diagnoses" :key="index" class="diagnosis-card">
              <div class="diagnosis-header">
                <span class="diagnosis-date">{{ diagnosis.date || 'N/A' }}</span>
                <span :class="['severity-badge', getSeverityClass(diagnosis.severity)]">
                  {{ diagnosis.severity || 'Unknown' }}
                </span>
              </div>
              <p class="diagnosis-text">{{ diagnosis.diagnosis }}</p>
            </div>
          </div>
        </div>

        <!-- Prescriptions Tab -->
        <div v-show="activeTab === 'prescriptions'" class="tab-pane">
          <div v-if="prescriptions.length === 0" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
              <path d="m8.5 8.5 7 7"></path>
            </svg>
            <p>No prescriptions issued</p>
          </div>
          <div v-else class="prescriptions-grid">
            <div v-for="(prescription, index) in prescriptions" :key="index" class="prescription-card">
              <div class="prescription-header">
                <span class="prescription-date">{{ prescription.date || 'N/A' }}</span>
                <span class="medicine-name">{{ prescription.medicine || 'N/A' }}</span>
              </div>
              <div class="prescription-details">
                <div class="detail-item" v-if="prescription.dosage">
                  <span class="label">Dosage:</span>
                  <span class="value">{{ prescription.dosage }}</span>
                </div>
                <div class="detail-item" v-if="prescription.frequency">
                  <span class="label">Frequency:</span>
                  <span class="value">{{ prescription.frequency }}</span>
                </div>
                <div class="detail-item" v-if="prescription.duration">
                  <span class="label">Duration:</span>
                  <span class="value">{{ prescription.duration }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { doctorAPI } from '../../api/appointments'

export default {
  name: 'PatientHistoryView',

  data() {
    return {
      patientId: null,
      patientName: '',
      patientInfo: null,
      visits: [],
      diagnoses: [],
      prescriptions: [],
      loading: false,
      error: '',
      activeTab: 'visits',
      tabs: [
        {
          id: 'visits',
          label: 'Past Visits',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
        },
        {
          id: 'diagnoses',
          label: 'Diagnoses',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>'
        },
        {
          id: 'prescriptions',
          label: 'Prescriptions',
          icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path><path d="m8.5 8.5 7 7"></path></svg>'
        }
      ]
    }
  },

  mounted() {
    this.patientId = this.$route.params.id
    if (this.patientId) {
      this.loadPatientHistory()
    }
  },

  methods: {
    async loadPatientHistory() {
      this.loading = true
      this.error = ''

      try {
        const response = await doctorAPI.getPatientHistory(this.patientId)
        const data = response.data

        this.patientName = data.patient_name || ''
        this.patientInfo = data.patient || null
        this.visits = data.visits || []
        this.diagnoses = data.diagnoses || []
        this.prescriptions = data.prescriptions || []
      } catch (err) {
        console.error('Failed to load patient history:', err)
        this.error = err.response?.data?.error || 'Failed to load patient history'
      } finally {
        this.loading = false
      }
    },

    getTabCount(tabId) {
      switch (tabId) {
        case 'visits':
          return this.visits.length
        case 'diagnoses':
          return this.diagnoses.length
        case 'prescriptions':
          return this.prescriptions.length
        default:
          return 0
      }
    },

    getStatusClass(status) {
      if (!status) return ''
      const s = status.toLowerCase()
      if (s === 'completed') return 'status-completed'
      if (s === 'cancelled') return 'status-cancelled'
      if (s === 'booked' || s === 'scheduled') return 'status-pending'
      return ''
    },

    getSeverityClass(severity) {
      if (!severity) return 'severity-unknown'
      const s = severity.toLowerCase()
      if (s === 'mild') return 'severity-mild'
      if (s === 'moderate') return 'severity-moderate'
      if (s === 'severe') return 'severity-severe'
      return 'severity-unknown'
    },

    goBack() {
      this.$router.push('/doctor/patients')
    }
  }
}
</script>

<style scoped>
.patient-history-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* Header */
.page-header-gradient {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  color: var(--color-white);
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: var(--color-white);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  cursor: pointer;
  margin-bottom: var(--space-md);
  transition: all var(--transition-base);
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
}

.header-content h1 {
  color: var(--color-white);
  margin: 0 0 var(--space-xs);
  font-size: var(--font-size-xl);
}

.header-content p {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: var(--font-size-base);
}

/* Loading */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  gap: var(--space-lg);
  background: var(--color-white);
  border-radius: var(--radius-lg);
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

/* Error */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  gap: var(--space-md);
  background: var(--color-white);
  border-radius: var(--radius-lg);
  color: var(--color-danger);
}

.error-container svg {
  opacity: 0.7;
}

/* History Container */
.history-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

/* Patient Info Card */
.patient-info-card {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-xl);
  background: linear-gradient(135deg, var(--color-gray-100) 0%, var(--color-gray-200) 100%);
  border-bottom: 1px solid var(--color-gray-200);
}

.patient-avatar {
  width: 64px;
  height: 64px;
  background: var(--color-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-white);
  flex-shrink: 0;
}

.patient-details h2 {
  margin: 0 0 var(--space-sm);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.patient-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.patient-meta span {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.blood-badge {
  background: var(--color-danger-light);
  color: var(--color-danger);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
}

/* Tabs */
.tabs-container {
  border-bottom: 1px solid var(--color-gray-200);
  padding: 0 var(--space-lg);
}

.tabs {
  display: flex;
  gap: var(--space-xs);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-count {
  background: var(--color-gray-200);
  color: var(--color-text-secondary);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: var(--font-size-xs);
}

.tab-btn.active .tab-count {
  background: var(--color-primary);
  color: var(--color-white);
}

/* Tab Content */
.tab-content {
  padding: var(--space-xl);
}

.tab-pane {
  animation: fadeIn 0.3s ease;
}

/* Table */
.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: var(--space-md);
  background: var(--color-gray-50);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.history-table td {
  padding: var(--space-md);
  border-bottom: 1px solid var(--color-gray-100);
}

.history-table tbody tr:hover {
  background: var(--color-gray-50);
}

/* Status Badge */
.status-badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: capitalize;
}

.status-completed {
  background: var(--color-status-completed-bg);
  color: var(--color-status-completed);
}

.status-cancelled {
  background: var(--color-status-cancelled-bg);
  color: var(--color-status-cancelled);
}

.status-pending {
  background: var(--color-status-pending-bg);
  color: var(--color-status-pending);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  color: var(--color-text-muted);
}

.empty-state svg {
  opacity: 0.5;
  margin-bottom: var(--space-md);
}

/* Diagnoses Grid */
.diagnoses-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.diagnosis-card {
  padding: var(--space-lg);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
}

.diagnosis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.diagnosis-date {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.severity-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.severity-mild {
  background: var(--color-severity-mild-bg);
  color: var(--color-severity-mild);
}

.severity-moderate {
  background: var(--color-severity-moderate-bg);
  color: var(--color-severity-moderate);
}

.severity-severe {
  background: var(--color-severity-severe-bg);
  color: var(--color-severity-severe);
}

.severity-unknown {
  background: var(--color-gray-200);
  color: var(--color-text-secondary);
}

.diagnosis-text {
  margin: 0;
  color: var(--color-text-primary);
}

/* Prescriptions Grid */
.prescriptions-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.prescription-card {
  padding: var(--space-lg);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
}

.prescription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.prescription-date {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.medicine-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  font-size: var(--font-size-base);
}

.prescription-details {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.detail-item {
  display: flex;
  gap: var(--space-xs);
}

.detail-item .label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.detail-item .value {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease;
}

.animate-scaleIn {
  animation: scaleIn 0.35s ease;
}

/* Button */
.btn {
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
}

/* Responsive */
@media (max-width: 768px) {
  .patient-info-card {
    flex-direction: column;
    text-align: center;
  }

  .patient-meta {
    justify-content: center;
  }

  .tabs {
    flex-wrap: wrap;
  }

  .tab-btn {
    flex: 1;
    justify-content: center;
  }

  .history-table {
    font-size: var(--font-size-sm);
  }

  .history-table th,
  .history-table td {
    padding: var(--space-sm);
  }
}
</style>
