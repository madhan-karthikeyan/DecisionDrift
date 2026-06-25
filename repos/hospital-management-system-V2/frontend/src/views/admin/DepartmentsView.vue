<template>
  <div class="admin-page">
    <!-- Page Header -->
    <div class="page-header-gradient">
      <div class="header-content">
        <h1>Departments</h1>
        <p>Manage hospital departments</p>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        Add Department
      </button>
    </div>

    <!-- Alerts -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading departments...</p>
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
            <th>Phone</th>
            <th>Email</th>
            <th>Doctors</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dept in departments" :key="dept.id">
            <td>
              <div class="dept-name">{{ dept.name }}</div>
            </td>
            <td>{{ dept.phone_number }}</td>
            <td>{{ dept.email }}</td>
            <td>
              <span class="badge badge-info">{{ dept.doctor_count }} doctors</span>
            </td>
            <td>
              <div class="action-buttons">
                <button @click="editDepartment(dept)" class="btn btn-sm btn-outline">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  Edit
                </button>
                <button @click="deleteDepartment(dept.id)" class="btn btn-sm btn-outline-danger">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  Delete
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="departments.length === 0">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M3 21h18"></path>
                  <path d="M5 21V7l8-4 8 4v14"></path>
                  <path d="M9 21v-4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4"></path>
                </svg>
                <p>No departments found</p>
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
          <h3>{{ showEditModal ? 'Edit' : 'Add' }} Department</h3>
          <button @click="closeModals" class="modal-close">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <form @submit.prevent="saveDepartment" class="modal-form">
          <div class="form-group">
            <label>Department Name</label>
            <input v-model="form.name" type="text" class="form-control" placeholder="Enter department name" required />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>Phone Number</label>
              <input v-model="form.phone_number" type="tel" class="form-control" placeholder="Phone number" required />
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="form.email" type="email" class="form-control" placeholder="Email address" required />
            </div>
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" class="form-control" placeholder="Department description" rows="3"></textarea>
          </div>
          <div class="form-group" v-if="showEditModal">
            <label>Department Head (Doctor ID)</label>
            <input v-model="form.head" type="text" class="form-control" placeholder="Doctor ID" />
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
import { departmentsAPI } from '../../api/appointments'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'DepartmentsView',
  data() {
    return {
      departments: [],
      loading: false,
      message: '',
      messageType: '',
      showAddModal: false,
      showEditModal: false,
      form: {
        id: '',
        name: '',
        phone_number: '',
        email: '',
        description: '',
        head: ''
      }
    }
  },
  mounted() {
    this.loadDepartments()
  },
  methods: {
    async loadDepartments() {
      this.loading = true
      try {
        const response = await departmentsAPI.getAllAdmin()
        this.departments = response.data
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load departments', 'danger')
      } finally {
        this.loading = false
      }
    },
    editDepartment(dept) {
      this.form = { ...dept, head: dept.head_id || '' }
      this.showEditModal = true
    },
    async saveDepartment() {
      try {
        if (this.showEditModal) {
          await departmentsAPI.update(this.form.id, this.form)
          this.showMessage('Department updated successfully', 'success')
        } else {
          await departmentsAPI.create(this.form)
          this.showMessage('Department created successfully', 'success')
        }
        this.closeModals()
        this.loadDepartments()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to save department', 'danger')
      }
    },
    async deleteDepartment(id) {
      const confirmed = await dialog.confirm('Are you sure you want to delete this department?')
      if (!confirmed) return
      try {
        await departmentsAPI.delete(id)
        this.showMessage('Department deleted successfully', 'success')
        this.loadDepartments()
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to delete department', 'danger')
      }
    },
    closeModals() {
      this.showAddModal = false
      this.showEditModal = false
      this.form = { id: '', name: '', phone_number: '', email: '', description: '', head: '' }
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

.dept-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
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
