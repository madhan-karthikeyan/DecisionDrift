<template>
  <div class="page-header-gradient animate-fadeIn">
    <h1>Diagnosis & Treatment</h1>
    <p>Complete the diagnosis form for the patient</p>
  </div>

  <div class="diagnosis-container animate-scaleIn">
    <div class="form-card">
      <div class="appointment-header">
        <h2>Patient: {{ appointment?.patient?.name || 'N/A' }}</h2>
        <p class="appointment-meta">
          {{ appointment?.date }} at {{ appointment?.time }}
        </p>
      </div>

      <form @submit.prevent="saveDiagnosis" class="diagnosis-form">
        <!-- Diagnosis Section -->
        <fieldset class="form-section">
          <legend>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
            </svg>
            Diagnosis
          </legend>
          <div class="form-group">
            <label>Diagnosis</label>
            <textarea v-model="form.diagnosis" placeholder="Enter diagnosis details..." required></textarea>
          </div>
          <div class="form-group">
            <label>Symptoms Observed</label>
            <textarea v-model="form.symptoms" placeholder="List symptoms..." required></textarea>
          </div>
          <div class="form-group">
            <label>Severity Level</label>
            <select v-model="form.severity" required>
              <option value="">Select severity</option>
              <option value="mild">Mild</option>
              <option value="moderate">Moderate</option>
              <option value="severe">Severe</option>
            </select>
          </div>
        </fieldset>

        <!-- Treatment Section -->
        <fieldset class="form-section">
          <legend>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
            </svg>
            Treatment Plan
          </legend>
          <div class="form-group">
            <label>Treatment Plan</label>
            <textarea v-model="form.treatment_plan" placeholder="Describe treatment plan..." required></textarea>
          </div>
          <div class="form-group">
            <label>Follow-up Required</label>
            <select v-model="form.follow_up">
              <option value="no">No</option>
              <option value="1_week">1 Week</option>
              <option value="2_weeks">2 Weeks</option>
              <option value="1_month">1 Month</option>
              <option value="3_months">3 Months</option>
            </select>
          </div>
        </fieldset>

        <!-- Prescriptions Section -->
        <fieldset class="form-section">
          <legend>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
              <path d="m8.5 8.5 7 7"></path>
            </svg>
            Prescriptions
          </legend>
          <div class="prescriptions-list">
            <div v-for="(med, index) in form.medicines" :key="index" class="prescription-item">
              <div class="prescription-fields">
                <div class="form-group">
                  <label>Medicine Name</label>
                  <input v-model="med.medicine" type="text" placeholder="e.g., Aspirin" />
                </div>
                <div class="form-group">
                  <label>Dosage</label>
                  <input v-model="med.dosage" type="text" placeholder="e.g., 500mg" />
                </div>
                <div class="form-group">
                  <label>Frequency</label>
                  <input v-model="med.frequency" type="text" placeholder="e.g., Twice daily" />
                </div>
                <div class="form-group">
                  <label>Duration</label>
                  <input v-model="med.duration" type="text" placeholder="e.g., 7 days" />
                </div>
              </div>
              <button type="button" @click="removeMedicine(index)" class="btn-remove">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
          <button type="button" @click="addMedicine" class="btn-add">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Add Medicine
          </button>
        </fieldset>

        <!-- Notes Section -->
        <fieldset class="form-section">
          <legend>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"></path>
            </svg>
            Additional Notes
          </legend>
          <div class="form-group">
            <label>Notes</label>
            <textarea v-model="form.notes" placeholder="Any additional notes..."></textarea>
          </div>
        </fieldset>

        <!-- Actions -->
        <div class="form-actions">
          <button type="button" @click="goBack" class="btn-cancel">
            Cancel
          </button>
          <button type="submit" class="btn-save" :disabled="saving">
            <svg v-if="!saving" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            <span v-if="saving" class="spinner-small"></span>
            {{ saving ? 'Saving...' : 'Save Diagnosis' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { appointmentsAPI } from '../../api/appointments'
import { dialog } from '../../composables/useDialog'

export default {
  name: 'DiagnosisFormView',

  data() {
    return {
      appointmentId: null,
      appointment: null,
      loading: false,
      saving: false,
      form: {
        diagnosis: '',
        symptoms: '',
        severity: '',
        treatment_plan: '',
        follow_up: 'no',
        notes: '',
        medicines: []
      }
    }
  },

  mounted() {
    this.appointmentId = this.$route.params.id || this.$route.params.appointmentId
    if (this.appointmentId) {
      this.loadDiagnosis()
    }
  },

  methods: {
    async loadDiagnosis() {
      this.loading = true
      try {
        const response = await appointmentsAPI.getDiagnosis(this.appointmentId)
        this.appointment = response.data.appointment

        // API returns flat fields, not nested in treatment
        this.form = {
          diagnosis: response.data.diagnosis || '',
          symptoms: response.data.symptoms || '',
          severity: response.data.severity || '',
          treatment_plan: response.data.treatment_plan || '',
          follow_up: response.data.follow_up || 'no',
          notes: response.data.notes || '',
          medicines: response.data.prescription || []
        }
      } catch (err) {
        console.error('Failed to load diagnosis', err)
      } finally {
        this.loading = false
      }
    },

    addMedicine() {
      this.form.medicines.push({
        medicine: '',
        dosage: '',
        frequency: '',
        duration: ''
      })
    },

    removeMedicine(index) {
      this.form.medicines.splice(index, 1)
    },

    async saveDiagnosis() {
      this.saving = true
      try {
        // Filter out empty medicines
        const medicines = this.form.medicines.filter(m => m.medicine.trim())

        await appointmentsAPI.saveDiagnosis(this.appointmentId, {
          diagnosis: this.form.diagnosis,
          symptoms: this.form.symptoms,
          severity: this.form.severity,
          treatment_plan: this.form.treatment_plan,
          follow_up: this.form.follow_up,
          notes: this.form.notes,
          medicines: medicines
        })

        await dialog.success('Diagnosis saved successfully!')
        this.$router.push('/doctor/appointments')
      } catch (err) {
        dialog.error(err.response?.data?.error || 'Failed to save diagnosis')
      } finally {
        this.saving = false
      }
    },

    goBack() {
      this.$router.push('/doctor/appointments')
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

.diagnosis-container {
  max-width: 800px;
  margin: 0 auto;
}

.form-card {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.appointment-header {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  padding: var(--space-xl);
  color: var(--color-white);
}

.appointment-header h2 {
  margin: 0 0 var(--space-xs);
  font-size: var(--font-size-xl);
}

.appointment-meta {
  margin: 0;
  opacity: 0.9;
  font-size: var(--font-size-base);
}

.diagnosis-form {
  padding: var(--space-xl);
}

.form-section {
  border: none;
  padding: 0;
  margin-bottom: var(--space-xl);
}

.form-section legend {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-sm);
  border-bottom: 2px solid var(--color-primary);
}

.form-section legend svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary);
}

.form-group {
  margin-bottom: var(--space-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: var(--space-md);
  border: 2px solid var(--color-gray-200);
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
  background: var(--color-white);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-shadow-sm);
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

/* Prescriptions */
.prescriptions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.prescription-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-gray-50);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
}

.prescription-fields {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.btn-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--color-danger-light);
  color: var(--color-danger);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.btn-remove:hover {
  background: var(--color-danger);
  color: var(--color-white);
}

.btn-remove svg {
  width: 18px;
  height: 18px;
}

.btn-add {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: transparent;
  color: var(--color-primary);
  border: 2px dashed var(--color-primary);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-add:hover {
  background: var(--color-primary-light);
}

.btn-add svg {
  width: 18px;
  height: 18px;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding-top: var(--space-xl);
  border-top: 1px solid var(--color-gray-200);
}

.btn-cancel {
  padding: var(--space-md) var(--space-xl);
  background: var(--color-gray-200);
  color: var(--color-text-primary);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-cancel:hover {
  background: var(--color-gray-300);
}

.btn-save {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 4px 12px var(--color-primary-shadow);
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--color-primary-shadow-md);
}

.btn-save:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-save svg {
  width: 18px;
  height: 18px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--color-white);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease forwards;
}

.animate-scaleIn {
  animation: scaleIn 0.35s ease forwards;
}

@media (max-width: 768px) {
  .prescription-fields {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions button {
    width: 100%;
  }
}
</style>
