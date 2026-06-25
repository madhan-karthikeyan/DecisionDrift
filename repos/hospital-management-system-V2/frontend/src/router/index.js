import { createRouter, createWebHistory } from 'vue-router'
import { authAPI } from '../api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/AuthPage.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/AuthPage.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    redirect: '/login'
  },
  // Admin routes
  {
    path: '/admin',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('../views/admin/DashboardView.vue')
      },
      {
        path: 'departments',
        name: 'AdminDepartments',
        component: () => import('../views/admin/DepartmentsView.vue')
      },
      {
        path: 'doctors',
        name: 'AdminDoctors',
        component: () => import('../views/admin/DoctorsView.vue')
      },
      {
        path: 'patients',
        name: 'AdminPatients',
        component: () => import('../views/admin/PatientsView.vue')
      },
      {
        path: 'appointments',
        name: 'AdminAppointments',
        component: () => import('../views/admin/AppointmentsView.vue')
      }
    ]
  },
  // Doctor routes
  {
    path: '/doctor',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true, role: 'doctor' },
    children: [
      {
        path: '',
        redirect: '/doctor/dashboard'
      },
      {
        path: 'dashboard',
        name: 'DoctorDashboard',
        component: () => import('../views/doctor/DashboardView.vue')
      },
      {
        path: 'appointments',
        name: 'DoctorAppointments',
        component: () => import('../views/doctor/AppointmentsView.vue')
      },
      {
        path: 'patients',
        name: 'DoctorPatients',
        component: () => import('../views/doctor/PatientsView.vue')
      },
      {
        path: 'patient/:id/history',
        name: 'DoctorPatientHistory',
        component: () => import('../views/doctor/PatientHistoryView.vue')
      },
      {
        path: 'availability',
        name: 'DoctorAvailability',
        component: () => import('../views/doctor/AvailabilityView.vue')
      },
      {
        path: 'appointment/:id/diagnosis',
        name: 'DiagnosisForm',
        component: () => import('../views/doctor/DiagnosisView.vue')
      },
      {
        path: 'profile',
        name: 'DoctorProfile',
        component: () => import('../views/doctor/ProfileView.vue')
      }
    ]
  },
  // Patient routes
  {
    path: '/patient',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true, role: 'patient' },
    children: [
      {
        path: '',
        redirect: '/patient/dashboard'
      },
      {
        path: 'dashboard',
        name: 'PatientDashboard',
        component: () => import('../views/patient/DashboardView.vue')
      },
      {
        path: 'doctors',
        name: 'PatientDoctors',
        component: () => import('../views/patient/DoctorsView.vue')
      },
      {
        path: 'appointments',
        name: 'PatientAppointments',
        component: () => import('../views/patient/AppointmentsView.vue')
      },
      {
        path: 'profile',
        name: 'PatientProfile',
        component: () => import('../views/patient/ProfileView.vue')
      }
    ]
  },
  // Legacy dashboard redirect
  {
    path: '/dashboard',
    redirect: (to) => {
      try {
        const userStr = localStorage.getItem('user')
        if (userStr) {
          const user = JSON.parse(userStr)
          if (user.role === 'admin') return '/admin/dashboard'
          if (user.role === 'doctor') return '/doctor/dashboard'
          if (user.role === 'patient') return '/patient/dashboard'
        }
      } catch (e) {
        // Invalid JSON in localStorage — fall through to login
      }
      return '/login'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')

  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!token) {
      next('/login')
      return
    }

    let user = userStr ? JSON.parse(userStr) : null
    if (!user) {
      try {
        const response = await authAPI.getCurrentUser()
        user = response.data
        localStorage.setItem('user', JSON.stringify(user))
      } catch (error) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        next('/login')
        return
      }
    }

    if (to.meta.role && user.role !== to.meta.role) {
      if (user.role === 'admin') {
        next('/admin/dashboard')
      } else if (user.role === 'doctor') {
        next('/doctor/dashboard')
      } else if (user.role === 'patient') {
        next('/patient/dashboard')
      }
      return
    }

    next()
  } else if (to.matched.some(record => record.meta.guest)) {
    if (token) {
      const user = userStr ? JSON.parse(userStr) : null
      if (user) {
        if (user.role === 'admin') {
          next('/admin/dashboard')
        } else if (user.role === 'doctor') {
          next('/doctor/dashboard')
        } else if (user.role === 'patient') {
          next('/patient/dashboard')
        }
        return
      }
    }
    next()
  } else {
    next()
  }
})

export default router
