<template>

    <div class="page-header-gradient">
      <h1>My Profile</h1>
      <p class="header-subtitle">Manage your personal information and medical details</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading profile...</p>
    </div>

    <div v-else>
      <div v-if="message" :class="['alert', 'animate-fadeIn', messageType === 'success' ? 'alert-success' : 'alert-danger']">{{ message }}</div>

      <div class="card card-elevated animate-scaleIn">
      <form @submit.prevent="updateProfile">
        <div class="form-grid">
          <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" required />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" required />
          </div>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Phone</label>
            <input v-model="form.phone" />
          </div>
          <div class="form-group">
            <label>Date of Birth</label>
            <input v-model="form.dob" type="date" />
          </div>
        </div>
        <div class="form-group">
          <label>Gender</label>
          <select v-model="form.gender">
            <option value="">Select</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div class="form-group">
          <label>Address</label>
          <input v-model="form.address" />
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>City</label>
            <input v-model="form.city" />
          </div>
          <div class="form-group">
            <label>State</label>
            <input v-model="form.state" />
          </div>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Zipcode</label>
            <input v-model="form.zipcode" />
          </div>
          <div class="form-group">
            <label>Blood Type</label>
            <select v-model="form.blood_type">
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
        </div>
        <div class="form-group">
          <label>Allergies</label>
          <textarea v-model="form.allergies" placeholder="List any allergies..."></textarea>
        </div>
        <div class="form-group">
          <label>Medical Summary</label>
          <textarea v-model="form.medical_summary" placeholder="Enter your medical history..."></textarea>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Update Profile
          </button>
        </div>
      </form>
    </div>

  </div>

</template>

<script>

import { patientAPI } from '../../api/appointments'

export default {
  name: 'PatientProfileView',

  data() {
    return {
      form: {
        name: '',
        email: '',
        phone: '',
        dob: '',
        gender: '',
        address: '',
        city: '',
        state: '',
        zipcode: '',
        blood_type: '',
        allergies: '',
        medical_summary: ''
      },
      message: '',
      messageType: '',
      loading: false
    }
  },
  mounted() {
    this.loadProfile()
  },
  methods: {
    async loadProfile() {
      this.loading = true
      try {
        const response = await patientAPI.getProfile()
        const data = response.data
        this.form = {
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          dob: data.dob || '',
          gender: data.gender || '',
          address: data.address || '',
          city: data.city || '',
          state: data.state || '',
          zipcode: data.zipcode || '',
          blood_type: data.blood_type || '',
          allergies: data.allergies || '',
          medical_summary: data.medical_summary || ''
        }
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to load profile', 'danger')
      } finally {
        this.loading = false
      }
    },
    async updateProfile() {
      try {
        await patientAPI.updateProfile(this.form)
        this.showMessage('Profile updated successfully', 'success')
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to update profile', 'danger')
      }
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

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.card-elevated {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-base);
  padding: var(--space-xl);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: var(--space-md);
  border: 2px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-white);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.form-group input:disabled {
  background-color: var(--color-gray-100);
  color: var(--color-text-secondary);
  cursor: not-allowed;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-base);
  border-top: 1px solid var(--color-gray-200);
  margin-top: var(--space-lg);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
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
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.alert {
  padding: var(--space-md) var(--space-base);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-lg);
  font-weight: var(--font-weight-medium);
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

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .card-elevated {
    padding: var(--space-lg);
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>
