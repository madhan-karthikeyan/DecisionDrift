<template>
  <div class="auth-root" :class="{ 'right-panel-active': showRegister }">
    <!-- Register Form -->
    <div class="form-container sign-up-container">
      <div class="form-inner">
        <RegisterForm @submit="handleRegister" @switchToLogin="showRegister = false" />
      </div>
    </div>

    <!-- Login Form -->
    <div class="form-container sign-in-container">
      <div class="form-inner">
        <LoginForm @submit="handleLogin" @signup="showRegister = true" />
      </div>
    </div>

    <!-- Overlay Panel -->
    <div class="overlay-container">
      <div class="overlay">
        <div class="overlay-panel overlay-left">
          <h1>Welcome Back</h1>
          <p>Sign in to access appointments, medical records and schedules</p>
          <button class="ghost_2" @click="showRegister = false">
            Sign In
          </button>
        </div>

        <div class="overlay-panel overlay-right">
          <h1>MediCore</h1>
          <p>Create an account to book appointments and manage healthcare</p>
          <button class="ghost" @click="showRegister = true">
            Create Account
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import LoginForm from '../components/auth/LoginForm.vue'
import RegisterForm from '../components/auth/RegisterForm.vue'
import { authAPI } from '../api/auth'

export default {
  name: 'AuthPage',
  components: {
    LoginForm,
    RegisterForm
  },
  data() {
    return {
      showRegister: false
    }
  },
  methods: {
    async handleLogin(credentials) {
      const { resolve, reject } = credentials
      try {
        const response = await authAPI.login(credentials.username, credentials.password)
        const { access_token, user } = response.data
        localStorage.setItem('token', access_token)
        localStorage.setItem('user', JSON.stringify(user))

        if (resolve) resolve()

        // Redirect based on role
        if (user.role === 'admin') {
          this.$router.push('/admin/dashboard')
        } else if (user.role === 'doctor') {
          this.$router.push('/doctor/dashboard')
        } else if (user.role === 'patient') {
          this.$router.push('/patient/dashboard')
        }
      } catch (err) {
        const error = new Error(err.response?.data?.error || 'Login failed')
        if (reject) reject(error)
        else throw error
      }
    },
    async handleRegister(formData) {
      const { resolve, reject, ...data } = formData
      try {
        await authAPI.register(data)
        if (resolve) resolve()
        this.showRegister = false
      } catch (err) {
        const error = new Error(err.response?.data?.error || 'Registration failed')
        if (reject) reject(error)
        else throw error
      }
    }
  }
}
</script>

<style scoped>
.auth-root {
  background: var(--color-white);
  border-radius: 24px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.2);
  position: relative;
  overflow: hidden;
  width: 1200px;
  max-width: 95vw;
  min-height: 800px;
  margin: 5vh auto;
}

.form-container {
  position: absolute;
  top: 0;
  height: 100%;
  width: 50%;
  transition: all 0.6s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-white);
}

.form-inner {
  width: 100%;
  max-width: 520px;
  padding: 0 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sign-in-container { left: 0; z-index: 2; }
.sign-up-container { left: 0; opacity: 0; z-index: 1; }

.auth-root.right-panel-active .sign-in-container {
  transform: translateX(100%);
  opacity: 0;
}

.auth-root.right-panel-active .sign-up-container {
  transform: translateX(100%);
  opacity: 1;
  z-index: 5;
  animation: show 0.6s;
}

@keyframes show {
  0%, 49.99% { opacity: 0; z-index: 1; }
  50%, 100% { opacity: 1; z-index: 5; }
}

.overlay-container {
  position: absolute;
  top: 0;
  left: 50%;
  width: 50%;
  height: 100%;
  overflow: hidden;
  transition: transform 0.6s ease-in-out;
  z-index: 100;
}

.auth-root.right-panel-active .overlay-container {
  transform: translateX(-100%);
}

.overlay {
  background: linear-gradient(135deg, var(--color-brand), var(--color-brand-dark));
  color: var(--color-white);
  position: relative;
  left: -100%;
  height: 100%;
  width: 200%;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
}

.auth-root.right-panel-active .overlay {
  transform: translateX(50%);
}

.overlay-panel {
  position: absolute;
  top: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 60px;
  text-align: center;
  height: 100%;
  width: 50%;
  transition: transform 0.6s ease-in-out;
}

.overlay-left { transform: translateX(-20%); }
.auth-root.right-panel-active .overlay-left { transform: translateX(0); }
.overlay-right { right: 0; transform: translateX(0); }
.auth-root.right-panel-active .overlay-right { transform: translateX(20%); }

h1 {
  font-weight: bold;
  margin: 0;
  font-size: 3.5rem;
  white-space: nowrap;
}

p {
  font-size: 18px;
  line-height: 28px;
  margin: 25px 0 40px;
  opacity: 0.9;
}

.ghost {
  position: relative;
  overflow: hidden;
  background: transparent;
  border: 2px solid var(--color-white);
  color: var(--color-white);
  padding: 15px 60px;
  border-radius: 40px;
  font-size: 14px;
  font-weight: bold;
  text-transform: uppercase;
  cursor: pointer;
  transition: transform 80ms ease-in, color 0.35s ease;
  z-index: 1;
}

.ghost::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--color-white);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.35s ease;
  z-index: -1;
}

.ghost:hover::before {
  transform: scaleX(1);
}

.ghost:hover {
  color: var(--color-brand-dark);
  border-color: var(--color-white);
}

.ghost:active {
  transform: scale(0.95);
}

.ghost_2 {
  position: relative;
  overflow: hidden;
  background: transparent;
  border: 2px solid var(--color-white);
  color: var(--color-white);
  padding: 15px 60px;
  border-radius: 40px;
  font-size: 14px;
  font-weight: bold;
  text-transform: uppercase;
  cursor: pointer;
  transition: transform 80ms ease-in, color 0.35s ease;
  z-index: 1;
}

.ghost_2::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--color-white);
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.35s ease;
  z-index: -1;
}

.ghost_2:hover::before {
  transform: scaleX(1);
}

.ghost_2:hover {
  color: var(--color-brand-dark);
  border-color: var(--color-white);
}

.ghost_2:active {
  transform: scale(0.95);
}

@media (max-width: 900px) {
  .auth-root {
    width: 100%;
    min-height: 100vh;
    margin: 0;
    border-radius: 0;
  }

  .overlay-container {
    display: none;
  }

  .form-container {
    width: 100%;
    left: 0;
    top: 0;
    height: 100%;
    transform: translateY(100%);
    opacity: 0;
    transition: transform 0.4s ease, opacity 0.4s ease;
  }

  .auth-root:not(.right-panel-active) .sign-in-container {
    transform: translateY(0);
    opacity: 1;
    z-index: 5;
  }

  .auth-root.right-panel-active .sign-up-container {
    transform: translateY(0);
    opacity: 1;
    z-index: 5;
  }

  .form-inner {
    max-width: 100%;
    padding: 24px;
  }
}
</style>
