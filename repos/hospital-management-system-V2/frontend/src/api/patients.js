import api from './axios'

// Admin - Patients
export const patientsAPI = {
  getAll() {
    return api.get('/admin/patients')
  },

  getById(id) {
    return api.get(`/admin/patients/${id}`)
  },

  create(patientData) {
    return api.post('/admin/patients', patientData)
  },

  update(id, patientData) {
    return api.put(`/admin/patients/${id}`, patientData)
  },

  delete(id) {
    return api.delete(`/admin/patients/${id}`)
  }
}

export default api
