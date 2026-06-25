<template>
  <div class="auth-form-wrapper">
    <h2 class="form-title">Create Account</h2>
    <p class="form-subtitle">
      Join MediCore to manage your healthcare
    </p>

    <form @submit.prevent="handleSubmit">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input
            v-model="form.username"
            type="text"
            class="form-input"
            placeholder="Choose username"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <input
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="Create password"
            required
            minlength="8"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input
          v-model="form.name"
          type="text"
          class="form-input"
          placeholder="Enter your full name"
          required
        />
      </div>

      <div class="form-group">
        <label class="form-label">Email</label>
        <input
          v-model="form.email"
          type="email"
          class="form-input"
          placeholder="Enter your email"
          required
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Phone</label>
          <input
            v-model="form.phone"
            type="tel"
            class="form-input"
            placeholder="10 digit number"
            required
            maxlength="10"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Date of Birth</label>
          <input
            v-model="form.dob"
            type="date"
            class="form-input"
            required
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Gender</label>
        <select v-model="form.gender" class="form-input" required>
          <option value="">Select gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <button type="submit" class="submit-btn" :disabled="loading">
        <span v-if="loading" class="btn-loader"></span>
        <span v-else>Create Account</span>
      </button>
    </form>

    <p class="switch-text">
      Already have an account?
      <a @click.prevent="$emit('switchToLogin')">Sign in</a>
    </p>
  </div>
</template>

<script>
export default {
  name: 'RegisterForm',
  emits: ['submit', 'switchToLogin'],
  data() {
    return {
      form: {
        username: '',
        password: '',
        name: '',
        email: '',
        phone: '',
        dob: '',
        gender: ''
      },
      errorMessage: '',
      successMessage: '',
      loading: false
    }
  },
  methods: {
    async handleSubmit() {
      this.errorMessage = ''
      this.successMessage = ''
      this.loading = true

      try {
        await new Promise((resolve, reject) => {
          this.$emit('submit', {
            ...this.form,
            resolve,
            reject
          })
        })
        this.successMessage = 'Registration successful! Please sign in.'
        this.form = {
          username: '',
          password: '',
          name: '',
          email: '',
          phone: '',
          dob: '',
          gender: ''
        }
      } catch (err) {
        this.errorMessage = err.message || 'Registration failed'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-form-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

form {
  width: 100%;
}

.form-title {
  font-size: 44px;
  font-weight: 800;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.form-subtitle {
  font-size: 20px;
  color: var(--color-text-secondary);
  margin-bottom: 35px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  width: 100%;
  margin-bottom: 20px;
  text-align: left;
}

.form-label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--color-text-primary);
}

.form-input {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  border: 2px solid var(--color-gray-200);
  border-radius: 12px;
  background: var(--color-white);
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 3px var(--color-brand-shadow-sm);
}

select.form-input {
  cursor: pointer;
}

.error-message {
  color: var(--color-danger);
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
  text-align: left;
  animation: shake 0.3s ease;
}

.success-message {
  color: var(--color-success);
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
  text-align: left;
}

.submit-btn {
  width: 100%;
  padding: 18px;
  font-size: 18px;
  background: linear-gradient(135deg, var(--color-brand), var(--color-brand-dark));
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 15px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 56px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px var(--color-brand-shadow);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-loader {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.switch-text {
  margin-top: 18px;
  font-size: 16px;
  color: var(--color-text-secondary);
}

.switch-text a {
  color: var(--color-brand);
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.switch-text a:hover {
  text-decoration: underline;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 500px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
