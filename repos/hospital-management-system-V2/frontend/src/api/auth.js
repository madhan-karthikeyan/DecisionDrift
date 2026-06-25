import api from './axios'

export const authAPI = {
  login(username, password) {
    return api.post('/auth/login', { username, password })
  },

  register(userData) {
    return api.post('/auth/register', userData)
  },

  getCurrentUser() {
    return api.get('/auth/me')
  }
}

// TODO: [L55] Remove default export of raw axios instance — consumers should use named exports only
