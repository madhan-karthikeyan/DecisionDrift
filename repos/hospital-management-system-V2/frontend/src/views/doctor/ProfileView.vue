<template>

  <div class="page-header-gradient">
    <h1>My Profile</h1>
    <p class="header-subtitle">Manage your professional and contact information</p>
  </div>

  <div v-if="loading" class="loading-container">
    <div class="spinner"></div>
    <p>Loading profile...</p>
  </div>

  <div v-else>

    <div
      v-if="message"
      :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']"
    >
      {{ message }}
    </div>

    <div class="card card-elevated">
      <form @submit.prevent="updateProfile">

        <!-- BASIC INFO -->
        <div class="form-grid">
          <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" required />
          </div>

          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" required disabled />
          </div>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>Phone</label>
            <input v-model="form.phone" />
          </div>

          <div class="form-group">
            <label>Specialization</label>
            <input v-model="form.specialization" />
          </div>
        </div>

        <!-- PROFESSIONAL DETAILS -->
        <div class="form-grid">

          <div class="form-group">
            <label>Experience (Years)</label>
            <input type="number" v-model="form.experience" min="0" />
          </div>

          <div class="form-group">
            <label>Consultation Fee Override</label>
            <input type="number" v-model="form.dr_consultation_fee" min="0" />
          </div>

        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary">
            Update Profile
          </button>
        </div>

      </form>
    </div>

  </div>

</template>

<script>

import { doctorAPI } from '../../api/appointments'

export default {
  name: 'DoctorProfileView',

  data() {
    return {
      form: {
        name: '',
        email: '',
        phone: '',
        specialization: '',
        experience: '',
        dr_consultation_fee: ''
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

        const response = await doctorAPI.getProfile()
        const data = response.data

        this.form = {
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          specialization: data.specialization || '',
          experience: data.experience || '',
          dr_consultation_fee: data.dr_consultation_fee || ''
        }

      } catch (err) {

        this.showMessage(
          err.response?.data?.error || 'Failed to load profile',
          'danger'
        )

      } finally {

        this.loading = false

      }
    },

    async updateProfile() {

      try {

        await doctorAPI.updateProfile(this.form)

        this.showMessage(
          'Profile updated successfully',
          'success'
        )

      } catch (err) {

        this.showMessage(
          err.response?.data?.error || 'Failed to update profile',
          'danger'
        )

      }

    },

    showMessage(msg, type) {

      this.message = msg
      this.messageType = type

      setTimeout(() => {
        this.message = ''
      }, 4000)

    }

  }

}

</script>

<style scoped>

.page-header-gradient {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white;
  padding: 32px;
  border-radius: 10px;
  margin-bottom: 25px;
}

.header-subtitle {
  opacity: 0.9;
}

.loading-container {
  text-align: center;
  padding: 40px;
}

.spinner {
  width: 45px;
  height: 45px;
  border: 4px solid #ddd;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: auto;
  margin-bottom: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-elevated {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: var(--shadow-base);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2,1fr);
  gap: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 6px;
  display: block;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
}

.form-group textarea {
  min-height: 100px;
}

.form-actions {
  text-align: right;
  margin-top: 20px;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 6px;
  cursor: pointer;
}

.alert {
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 15px;
}

.alert-success {
  background: #e7f8ef;
  color: #1b7c4a;
}

.alert-danger {
  background: #ffe8e8;
  color: #a71d2a;
}

@media (max-width:768px) {

  .form-grid {
    grid-template-columns: 1fr;
  }

}

</style>