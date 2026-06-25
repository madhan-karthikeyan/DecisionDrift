<template>
  <div class="page-header-gradient animate-fadeIn">
    <h1>My Patients</h1>
    <p>View and manage your patient records</p>
  </div>

  <div v-if="loading" class="loading-container">
    <div class="spinner"></div>
    <span>Loading patients...</span>
  </div>

  <div v-else class="table-card animate-scaleIn">
    <table class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Phone</th>
          <th>Gender</th>
          <th>Age</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="patients.length === 0">
          <td colspan="6" class="empty-state">
            <div class="empty-state-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
              <p>No patients found</p>
            </div>
          </td>
        </tr>
        <tr v-for="patient in patients" :key="patient.id">
          <td>{{ patient.name }}</td>
          <td>{{ patient.email }}</td>
          <td>{{ patient.phone }}</td>
          <td>{{ patient.gender }}</td>
          <td>{{ patient.age }}</td>
          <td>
            <button @click="viewHistory(patient.id)" class="btn-history">
              <span class="btn-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2">
                  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
                  <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                </svg>
              </span>
              View History
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

</template>

<script>

import { doctorAPI } from '../../api/appointments'

export default {
  name: 'DoctorPatientsView',

  data() {
    return {
      patients: [],
      loading: false
    }
  },
  mounted() {
    this.loadPatients()
  },
  methods: {
    async loadPatients() {
      this.loading = true
      try {
        const response = await doctorAPI.getPatients()
        this.patients = response.data
      } catch (err) {
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    viewHistory(patientId) {
      this.$router.push(`/doctor/patient/${patientId}/history`)
    }
  }
}
</script>

<style scoped>
.page-header-gradient {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
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
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
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

.btn-icon {
  margin-right: var(--space-xs);
}

.btn-history {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 6px 12px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-history:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  opacity: 0.95;
}

.btn-history:active {
  transform: translateY(0);
  box-shadow: none;
}

.btn-history svg {
  width: 14px;
  height: 14px;
}

.empty-state {
  text-align: center;
  padding: var(--space-3xl) var(--space-lg) !important;
}

.empty-state-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  color: var(--color-text-secondary);
}

.empty-state-content svg {
  opacity: 0.4;
}

.empty-state-content p {
  margin: 0;
  font-size: var(--font-size-base);
}
</style>
