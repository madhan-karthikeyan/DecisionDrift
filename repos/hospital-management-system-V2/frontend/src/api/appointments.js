import api from './axios'

export const departmentsAPI = {
  getAll() {
    return api.get('/public/departments')
  },

  // Admin only
  getAllAdmin() {
    return api.get('/admin/departments')
  },

  getById(id) {
    return api.get(`/admin/departments/${id}`)
  },

  create(data) {
    return api.post('/admin/departments', data)
  },

  update(id, data) {
    return api.put(`/admin/departments/${id}`, data)
  },

  delete(id) {
    return api.delete(`/admin/departments/${id}`)
  }
}

export const appointmentsAPI = {
  // Admin
  getAllAdmin() {
    return api.get('/admin/appointments')
  },

  // Doctor
  getDoctorAppointments() {
    return api.get('/doctor/appointments')
  },

  completeAppointment(appointmentId) {
    return api.post(`/doctor/appointments/${appointmentId}/complete`)
  },

  cancelAppointment(appointmentId) {
    return api.post(`/doctor/appointments/${appointmentId}/cancel`)
  },

  getDiagnosis(appointmentId) {
    return api.get(`/doctor/appointments/${appointmentId}/diagnosis`)
  },

  saveDiagnosis(appointmentId, data) {
    return api.post(`/doctor/appointments/${appointmentId}/diagnosis`, data)
  },

  // Patient
  getPatientAppointments() {
    return api.get('/patient/appointments')
  },

  getPatientAppointmentDetail(appointmentId) {
    return api.get(`/patient/appointments/${appointmentId}`)
  },

  cancelPatientAppointment(appointmentId) {
    return api.post(`/patient/appointments/${appointmentId}/cancel`)
  }
}

export const adminAPI = {
  getDashboard() {
    return api.get('/admin/dashboard')
  }
}

export const doctorAPI = {
  getDashboard() {
    return api.get('/doctor/dashboard')
  },

  getPatients() {
    return api.get('/doctor/patients')
  },

  getPatientHistory(patientId) {
    return api.get(`/doctor/patients/${patientId}/history`)
  },

  getAvailability() {
    return api.get('/doctor/availability')
  },

  saveAvailability(data) {
    return api.post('/doctor/availability', data)
  },

  // Doctor profile
  getProfile() {
    return api.get('/doctor/profile')
  },

  updateProfile(data) {
    return api.put('/doctor/profile', data)
  }
}

export const patientAPI = {
  getDashboard() {
    return api.get('/patient/dashboard')
  },

  getProfile() {
    return api.get('/patient/profile')
  },

  updateProfile(data) {
    return api.put('/patient/profile', data)
  }
}

export default api
