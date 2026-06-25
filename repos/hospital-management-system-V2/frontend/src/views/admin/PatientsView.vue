<template>
  <div class="admin-page">
    <!-- Page Header -->
    <div class="page-header-gradient">
      <div class="header-content">
        <h1>Patients</h1>
        <p>Manage patient records</p>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        Add Patient
      </button>
    </div>

    <!-- Alerts -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading patients...</p>
    </div>

    <div v-if="message" :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']">
      {{ message }}
    </div>

    <!-- Data Table -->
    <div class="table-card" v-if="!loading">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Gender</th>
            <th>Age</th>
            <th>Blood Type</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="patient in patients" :key="patient.id">
            <td>
              <div class="patient-name">{{ patient.name }}</div>
            </td>
            <td>{{ patient.email }}</td>
            <td>{{ patient.phone }}</td>
            <td>{{ patient.gender }}</td>
            <td>{{ patient.age }}</td>
            <td>
              <span v-if="patient.blood_type" class="badge badge-info">{{ patient.blood_type }}</span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="editPatient(patient)" class="btn btn-sm btn-outline">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  Edit
                </button>
                <button @click="deletePatient(patient.id)" class="btn btn-sm btn-outline-danger">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  Delete
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="patients.length === 0">
            <td colspan="7" class="empty-cell">
              <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <p>No patients found</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ showEditModal ? 'Edit' : 'Add' }} Patient</h3>
          <button @click="closeModals" class="modal-close">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <form @submit.prevent="savePatient" class="modal-form">
          <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" type="text" class="form-control" placeholder="Enter patient name" required />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Email</label>
              <input v-model="form.email" type="email" class="form-control" placeholder="Email address" required />
            </div>
            <div class="form-group">
              <label>Phone</label>
              <input v-model="form.phone" type="tel" class="form-control" placeholder="Phone number" required />
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Date of Birth</label>
              <input v-model="form.dob" type="date" class="form-control" required />
            </div>
            <div class="form-group">
              <label>Gender</label>
              <select v-model="form.gender" class="form-control" required>
                <option value="">Select</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>City</label>
              <input v-model="form.city" type="text" class="form-control" placeholder="City" />
            </div>
            <div class="form-group">
              <label>State</label>
              <input v-model="form.state" type="text" class="form-control" placeholder="State" />
            </div>
          </div>
          <div class="form-group">
            <label>Blood Type</label>
            <select v-model="form.blood_type" class="form-control">
              <option value="">Select</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
            </select>
          </div>
          <div class="form-group">
            <label>Allergies</label>
            <textarea v-model="form.allergies" class="form-control" placeholder="List any allergies" rows="2"></textarea>
          </div>
          <div class="form-group">
            <label>Medical Summary</label>
            <textarea v-model="form.medical_summary" class="form-control" placeholder="Medical history summary" rows="3"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModals" class="btn btn-secondary">Cancel</button>
            <button type="submit" class="btn btn-primary">{{ showEditModal ? 'Update' : 'Create' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>

import { patientsAPI } from '../../api/patients'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'PatientsView',

  data() {
    return {
      patients: [],
      loading: false,
      message: '',
      messageType: '',
      showAddModal: false,
      showEditModal: false,
      form: {
        id: '',
        name: '',
        email: '',
        phone: '',
        dob: '',
        gender: '',
        city: '',
        state: '',
        blood_type: '',
        allergies: '',
        medical_summary: ''
      }
    }
  },
  mounted() {
    this.loadPatients()
  },
  methods: {
    async loadPatients() {
      this.loading = true
      try {
        const response = await patientsAPI.getAll()
        this.patients = response.data
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load patients', 'danger')
      } finally {
        this.loading = false
      }
    },
    editPatient(patient) {
      this.form = {
        id: patient.id,
        name: patient.name,
        email: patient.email,
        phone: patient.phone,
        dob: patient.dob,
        gender: patient.gender,
        city: patient.city,
        state: patient.state,
        blood_type: patient.blood_type,
        allergies: patient.allergies,
        medical_summary: patient.medical_summary
      }
      this.showEditModal = true
    },
    async savePatient() {
      try {
        if (this.showEditModal) {
          await patientsAPI.update(this.form.id, this.form)
          this.showMessage('Patient updated successfully', 'success')
        } else {
          await patientsAPI.create(this.form)
          this.showMessage('Patient created successfully', 'success')
        }
        this.closeModals()
        this.loadPatients()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to save patient', 'danger')
      }
    },
    async deletePatient(id) {
      const confirmed = await dialog.confirm('Are you sure you want to delete this patient?')
      if (!confirmed) return
      try {
        await patientsAPI.delete(id)
        this.showMessage('Patient deleted successfully', 'success')
        this.loadPatients()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to delete patient', 'danger')
      }
    },
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.form = { id: '', name: '', email: '', phone: '', dob: '', gender: '', city: '', state: '', blood_type: '', allergies: '', medical_summary: '' }
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

.page-header-gradient .btn-primary {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  padding: var(--space-sm) var(--space-base);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.page-header-gradient .btn-primary:hover {
  background: var(--color-primary-hover);
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

/* Table Card */
.table-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-base);
  overflow: hidden;
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

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: var(--space-sm);
}

.btn-sm {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid var(--color-gray-300);
  background: var(--color-white);
  color: var(--color-text-secondary);
}

.btn-sm:hover {
  background: var(--color-gray-100);
}

.btn-outline-danger {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn-outline-danger:hover {
  background: var(--color-danger-light);
  color: var(--color-danger);
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

/* Modal */
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
  z-index: var(--z-modal);
  animation: fadeIn 0.2s ease;
}

.modal {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: scaleIn 0.2s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: var(--space-xs);
  display: flex;
  transition: color var(--transition-fast);
}

.modal-close:hover {
  color: var(--color-text-primary);
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.form-control {
  padding: var(--space-md);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
}

.form-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

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
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: var(--color-gray-200);
  color: var(--color-text-primary);
}

.btn-secondary:hover {
  background: var(--color-gray-300);
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

  .form-row-2 {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
