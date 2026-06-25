import api from './axios'

// Public endpoints (no auth required)
export const publicAPI = {
  getDepartments() {
    return api.get('/public/departments')
  },

  getSpecializations(params = {}) {
    return api.get('/public/specializations', { params })
  },

  getDoctors(params = {}) {
    return api.get('/public/doctors', { params })
  }
}

// Admin - Doctors
export const doctorsAPI = {
  getAll() {
    return api.get('/admin/doctors')
  },

  getById(id) {
    return api.get(`/admin/doctors/${id}`)
  },

  create(doctorData) {
    return api.post('/admin/doctors', doctorData)
  },

  update(id, doctorData) {
    return api.put(`/admin/doctors/${id}`, doctorData)
  },

  delete(id) {
    return api.delete(`/admin/doctors/${id}`)
  },

  blacklist(id) {
    return api.post(`/admin/doctors/${id}/blacklist`)
  }
}

// Patient - Search Doctors
export const searchDoctorsAPI = {
  getDoctors(params = {}) {
    return api.get('/patient/doctors', { params })
  },

  getAvailableSlots(doctorId, date) {
    return api.get(`/patient/doctors/${doctorId}/slots`, { params: { date } })
  }
}

// Patient - Appointment Payment & Booking
export const appointmentAPI = {
  createPaymentOrder(data) {
    return api.post('/patient/appointments/create-payment-order', data)
  },

  verifyPayment(data) {
    return api.post('/patient/appointments/verify-payment', data)
  },

  cancel(appointmentId) {
    return api.post(`/patient/appointments/${appointmentId}/cancel`)
  },

  reschedule(data) {
    return api.post('/patient/appointments/reschedule', data)
  }
}

export default api
