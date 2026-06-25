<template>
  <div class="page-header-gradient animate-fadeIn">
    <h1>Manage Availability</h1>
    <p>Set your weekly schedule and appointment slots</p>
  </div>

  <div v-if="message" :class="['alert', 'animate-fadeIn', messageType === 'success' ? 'alert-success' : 'alert-danger']">{{ message }}</div>

  <div class="content-card animate-scaleIn">
    <p class="card-description">Set your weekly availability for the upcoming week.</p>

    <div v-for="(day, index) in days" :key="index" class="day-card">
      <div class="day-header">
        <input type="checkbox" v-model="availability[index].available" :id="'day_' + index" class="day-checkbox" />
        <label :for="'day_' + index" class="day-label">{{ day }}</label>
      </div>

      <div v-if="availability[index].available" class="time-grid">
        <div class="form-group">
          <label>Start Time</label>
          <input type="time" v-model="availability[index].start_time" class="form-control" />
        </div>
        <div class="form-group">
          <label>End Time</label>
          <input type="time" v-model="availability[index].end_time" class="form-control" />
        </div>
        <div class="form-group">
          <label>Slot Duration (minutes)</label>
          <select v-model="availability[index].slot_duration" class="form-control">
            <option value="15">15</option>
            <option value="30">30</option>
            <option value="45">45</option>
            <option value="60">60</option>
          </select>
        </div>
        <div class="form-group">
          <label>Break Start</label>
          <input type="time" v-model="availability[index].break_start" class="form-control" />
        </div>
        <div class="form-group">
          <label>Break End</label>
          <input type="time" v-model="availability[index].break_end" class="form-control" />
        </div>
      </div>
    </div>

    <div class="action-bar">
      <button @click="saveAvailability" class="btn-save">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
          <polyline points="17 21 17 13 7 13 7 21"></polyline>
          <polyline points="7 3 7 8 15 8"></polyline>
        </svg>
        Save Availability
      </button>
    </div>
  </div>

</template>

<script>

import { doctorAPI } from '../../api/appointments'

export default {
  name: 'DoctorAvailabilityView',

  data() {
    return {
      days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
      availability: Array(7).fill().map(() => ({
        available: false,
        start_time: '09:00',
        end_time: '17:00',
        slot_duration: '30',
        break_start: '',
        break_end: ''
      })),
      message: '',
      messageType: ''
    }
  },
  mounted() {
    this.loadAvailability()
  },
  methods: {
    async loadAvailability() {
      try {
        const response = await doctorAPI.getAvailability()
        const data = response.data
        // Map existing availability to form
        data.forEach(item => {
          const dayIndex = this.days.indexOf(item.day_of_week)
          if (dayIndex !== -1) {
            this.availability[dayIndex] = {
              available: true,
              start_time: item.start_time || '09:00',
              end_time: item.end_time || '17:00',
              slot_duration: String(item.slot_duration || 30),
              break_start: item.break_start || '',
              break_end: item.break_end || ''
            }
          }
        })
      } catch (err) {
        console.error('Failed to load availability', err)
      }
    },
    async saveAvailability() {
      try {
        const data = {}
        this.availability.forEach((av, i) => {
          if (av.available) {
            data[`available_${i}`] = true
            data[`start_time_${i}`] = av.start_time
            data[`end_time_${i}`] = av.end_time
            data[`slot_duration_${i}`] = av.slot_duration
            data[`break_start_${i}`] = av.break_start
            data[`break_end_${i}`] = av.break_end
          }
        })
        await doctorAPI.saveAvailability(data)
        this.showMessage('Availability saved successfully', 'success')
      } catch (err) {
        this.showMessage(err.response?.data?.error || 'Failed to save availability', 'danger')
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
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-xl);
  color: var(--color-white);
}

.page-header-gradient h1 {
  color: var(--color-white);
  margin-bottom: var(--space-xs);
}

.page-header-gradient p {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: var(--font-size-base);
}

.content-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-xl);
}

.card-description {
  margin-bottom: var(--space-xl);
  color: var(--color-text-secondary);
}

.day-card {
  padding: var(--space-lg);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
  transition: all var(--transition-base);
}

.day-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-base);
}

.day-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-base);
}

.day-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.day-label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-lg);
  padding-left: var(--space-xl);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.form-group label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.form-control {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
}

.form-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--shadow-focus);
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-gray-200);
}

.btn-save {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 2px 8px var(--color-primary-shadow);
}

.btn-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--color-primary-shadow-md);
}

.btn-save:active {
  transform: translateY(0);
}

.btn-save svg {
  width: 18px;
  height: 18px;
}

.btn-icon {
  margin-right: var(--space-sm);
}

.alert {
  padding: var(--space-base) var(--space-lg);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-lg);
}

.alert-success {
  background: var(--color-success-light);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.alert-danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}
</style>
