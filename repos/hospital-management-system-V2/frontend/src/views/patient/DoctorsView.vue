<template>

    <div class="page-header-gradient">
      <h1>Find Doctors</h1>
      <p class="header-subtitle">Browse and book appointments with our expert doctors</p>
    </div>

    <div class="card card-elevated search-card">
      <div class="search-wrapper">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
        <input v-model="searchQuery" @input="searchDoctors" type="text" placeholder="Search doctors by name..." class="search-input" />
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading doctors...</p>
    </div>

    <div v-else-if="doctors.length === 0" class="empty-state animate-fadeIn">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        <circle cx="9" cy="7" r="4"></circle>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
      </svg>
      <p>No doctors found matching your search.</p>
    </div>

    <div v-else class="doctors-grid">
      <div v-for="(doctor, index) in doctors" :key="doctor.id" class="card card-elevated doctor-card animate-scaleIn" :style="{ animationDelay: (index * 0.05) + 's' }">
        <div class="doctor-avatar">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
          </svg>
        </div>
        <h3>{{ doctor.name.startsWith('Dr.') || doctor.name.startsWith('Dr ') ? doctor.name : 'Dr. ' + doctor.name }}</h3>
        <p class="doctor-info"><strong>Specialization:</strong> {{ doctor.specialization }}</p>
        <p class="doctor-info"><strong>Experience:</strong> {{ doctor.experience || 0 }} years</p>
        <p class="doctor-info"><strong>Cost:</strong> ₹ {{ doctor.consultation_fee || 500 }}</p>
        <button @click="bookAppointment(doctor)" class="btn-book">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          Book Appointment
        </button>
      </div>
    </div>

    <!-- Booking Modal -->
    <div v-if="showBookingModal" class="modal-overlay" @click.self="showBookingModal = false">
      <div class="modal animate-scaleIn">
        <div class="modal-header">
          <h3>Book Appointment</h3>
          <button @click="showBookingModal = false" class="modal-close">&times;</button>
        </div>
        <form @submit.prevent="submitBooking">
          <div class="form-group">
            <label>Doctor</label>
            <input :value="selectedDoctor?.name" disabled />
          </div>
          <div class="form-group">
            <label>Date</label>
            <input v-model="booking.date" type="date" required @change="loadSlots" />
          </div>
          <div class="form-group">
            <label>Time Slot</label>
            <select v-model="booking.time" required>
              <option value="">Select time</option>
              <option v-for="slot in availableSlots" :key="slot" :value="slot">{{ slot }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Reason (optional)</label>
            <textarea v-model="booking.reason"></textarea>
          </div>
          <div v-if="booking.time" class="form-group">
            <label>Consultation Fee</label>
            <div class="consultation-fee-display">
              ₹ {{ selectedDoctor?.consultation_fee || 500 }}
            </div>
          </div>
          <button type="submit" class="btn-book" :disabled="bookingLoading">
            <svg v-if="bookingLoading" class="btn-spinner" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
            {{ bookingLoading ? 'Processing...' : 'Pay & Book Appointment' }}
          </button>
        </form>
      </div>
    </div>

</template>

<script>

import { searchDoctorsAPI, appointmentAPI } from '../../api/doctors'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'PatientDoctorsView',

  data() {
    return {
      doctors: [],
      searchQuery: '',
      loading: false,
      showBookingModal: false,
      selectedDoctor: null,
      booking: { date: '', time: '', reason: '' },
      availableSlots: [],
      bookingLoading: false
    }
  },
  mounted() {
    this.loadDoctors()
  },
  methods: {
    async loadDoctors() {
      this.loading = true
      try {
        const response = await searchDoctorsAPI.getDoctors({ search: this.searchQuery })
        this.doctors = response.data.doctors || []
      } catch (err) {
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    searchDoctors() {
      if (this._debounceTimer) clearTimeout(this._debounceTimer)
      this._debounceTimer = setTimeout(() => {
        this.loadDoctors()
      }, 300)
    },
    bookAppointment(doctor) {
      this.selectedDoctor = doctor
      this.booking = { date: '', time: '', reason: '' }
      this.availableSlots = []
      this.showBookingModal = true
    },
    async loadSlots() {
      if (!this.booking.date || !this.selectedDoctor) return
      try {
        const response = await searchDoctorsAPI.getAvailableSlots(this.selectedDoctor.id, this.booking.date)
        this.availableSlots = response.data.slots || []
      } catch (err) {
        console.error(err)
      }
    },
    async submitBooking() {
      this.bookingLoading = true
      try {
        // Step 1: Create payment order on backend
        const orderRes = await appointmentAPI.createPaymentOrder({
          doctor_id: this.selectedDoctor.id,
          appointment_date: this.booking.date,
          appointment_time: this.booking.time,
          reason: this.booking.reason
        })

        const { order_id, amount, razorpay_key } = orderRes.data

        // Step 2: Open Razorpay checkout
        const paymentResult = await this.openRazorpayCheckout({
          order_id,
          amount,
          razorpay_key
        })

        // Step 3: Verify payment on backend
        await appointmentAPI.verifyPayment({
          razorpay_order_id: paymentResult.razorpay_order_id,
          razorpay_payment_id: paymentResult.razorpay_payment_id,
          razorpay_signature: paymentResult.razorpay_signature
        })

        this.bookingLoading = false
        this.showBookingModal = false
        await dialog.success('Payment successful! Appointment booked.')
        this.$router.push('/patient/appointments')
      } catch (err) {
        // Razorpay popup closed/dismissed by user
        if (err.reason === 'payment_dismissed') {
          dialog.error('Payment was cancelled.')
        } else {
          dialog.error(err.response?.data?.error || err.message || 'Failed to book appointment')
        }
      } finally {
        this.bookingLoading = false
      }
    },

    openRazorpayCheckout({ order_id, amount, razorpay_key }) {
      return new Promise((resolve, reject) => {
        const options = {
          key: razorpay_key,
          amount: amount,
          currency: 'INR',
          name: 'Hospital Management System',
          description: `Consultation with ${this.selectedDoctor?.name || 'Doctor'}`,
          order_id: order_id,
          handler(response) {
            resolve(response)
          },
          modal: {
            ondismiss() {
              reject({ reason: 'payment_dismissed' })
            }
          },
          theme: {
            color: '#3b82f6'
          }
        }

        const rzp = new window.Razorpay(options)
        rzp.on('payment.failed', function (response) {
          reject(new Error(response.error?.description || 'Payment failed'))
        })
        rzp.open()
      })
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

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--space-md);
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-md) var(--space-md) var(--space-md) var(--space-2xl);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.search-card {
  margin-bottom: var(--space-lg);
}

.doctors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-lg);
}

.card-elevated {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-base);
  transition: transform var(--transition-bounce), box-shadow var(--transition-bounce);
}

.card-elevated:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.doctor-card {
  padding: var(--space-xl);
  text-align: center;
  border: 1px solid var(--color-gray-200);
  background: var(--color-white);
}

.doctor-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.doctor-avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-lg);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px var(--color-primary-shadow);
}

.doctor-avatar svg {
  width: 40px;
  height: 40px;
  color: var(--color-white);
}

.doctor-card h3 {
  margin-bottom: var(--space-sm);
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.doctor-info {
  margin-bottom: var(--space-xs);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.doctor-info strong {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

/* Book Appointment Button */
.btn-book {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  margin-top: var(--space-lg);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-book:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-primary-shadow-md);
}

.btn-book:active {
  transform: translateY(0);
}

.btn-book svg {
  width: 18px;
  height: 18px;
}

/* Modal Styles */
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
  max-width: 480px;
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
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  margin: -1px;
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

.modal form {
  padding: var(--space-xl);
}

.modal .form-group {
  margin-bottom: var(--space-lg);
}

.modal label {
  display: block;
  margin-bottom: var(--space-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.modal input,
.modal select,
.modal textarea {
  width: 100%;
  padding: var(--space-md);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
  background: var(--color-white);
}

.modal input:focus,
.modal select:focus,
.modal textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-shadow-sm);
}

.modal input:disabled {
  background: var(--color-gray-100);
  color: var(--color-text-secondary);
}

.consultation-fee-display {
  padding: var(--space-md);
  background: var(--color-stat-success-bg, #f0fdf4);
  border: 1px solid var(--color-success, #22c55e);
  border-radius: var(--radius-base);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-success, #16a34a);
}

.modal textarea {
  min-height: 80px;
  resize: vertical;
}

.modal .btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
}

.modal .btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-primary-shadow-md);
}

.modal .btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal .btn-primary svg {
  width: 18px;
  height: 18px;
}

/* Loading */
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

@keyframes spin {
  to { transform: rotate(360deg); }
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

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: var(--color-white);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
