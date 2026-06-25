<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div
        v-if="state.visible"
        class="dialog-backdrop"
        @click.self="onBackdropClick"
        @keydown.esc="onEsc"
      >
        <Transition name="dialog-scale" appear>
          <div
            v-if="state.visible"
            class="dialog-panel"
            :class="`dialog-panel--${state.type}`"
            role="alertdialog"
            aria-modal="true"
            :aria-labelledby="'dialog-title'"
            :aria-describedby="'dialog-message'"
            ref="panel"
            tabindex="-1"
          >
            <div class="dialog-icon" :class="`dialog-icon--${state.type}`">
              <!-- Confirm icon -->
              <svg v-if="state.type === 'confirm'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <!-- Success icon -->
              <svg v-else-if="state.type === 'success'" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="9 12 12 15 16 10"/>
              </svg>
              <!-- Error icon -->
              <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </div>

            <h3 id="dialog-title" class="dialog-title">{{ state.title }}</h3>
            <p id="dialog-message" class="dialog-message">{{ state.message }}</p>

            <div class="dialog-actions">
              <template v-if="state.type === 'confirm'">
                <button class="dialog-btn dialog-btn--cancel" @click="onCancel">Cancel</button>
                <button class="dialog-btn dialog-btn--confirm" @click="onConfirm" ref="confirmBtn">Confirm</button>
              </template>
              <template v-else>
                <button class="dialog-btn dialog-btn--ok" :class="`dialog-btn--${state.type}`" @click="onConfirm" ref="confirmBtn">OK</button>
              </template>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { dialogState, dialogActions } from '../../composables/useDialog'

export default {
  name: 'CustomDialog',

  setup() {
    return {
      state: dialogState,
      actions: dialogActions
    }
  },

  watch: {
    'state.visible'(val) {
      if (val) {
        document.body.style.overflow = 'hidden'
        this.$nextTick(() => {
          this.$refs.confirmBtn?.focus()
        })
      } else {
        document.body.style.overflow = ''
      }
    }
  },

  mounted() {
    document.addEventListener('keydown', this.handleKeydown)
  },

  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    document.body.style.overflow = ''
  },

  methods: {
    onConfirm() {
      this.actions.handleConfirm()
    },
    onCancel() {
      this.actions.handleCancel()
    },
    onBackdropClick() {
      // Only close on backdrop click for non-confirm dialogs
      if (this.state.type !== 'confirm') {
        this.actions.handleConfirm()
      }
    },
    onEsc() {
      this.actions.handleCancel()
    },
    handleKeydown(e) {
      if (!this.state.visible) return
      if (e.key === 'Escape') {
        e.preventDefault()
        this.actions.handleCancel()
      }
    }
  }
}
</script>

<style scoped>
/* Backdrop */
.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal-backdrop, 400);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  padding: var(--space-base, 16px);
}

/* Panel */
.dialog-panel {
  position: relative;
  z-index: var(--z-modal, 500);
  background: var(--color-white, #fff);
  border-radius: var(--radius-md, 12px);
  box-shadow: var(--shadow-xl, 0 20px 40px rgba(0, 0, 0, 0.1));
  padding: var(--space-xl, 32px);
  width: 100%;
  max-width: 400px;
  text-align: center;
  outline: none;
}

/* Icon */
.dialog-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full, 9999px);
  margin: 0 auto var(--space-base, 16px);
}

.dialog-icon--confirm {
  background: var(--color-primary-light, #DBEAFE);
  color: var(--color-primary, #2563EB);
}

.dialog-icon--success {
  background: var(--color-success-light, #dcfce7);
  color: var(--color-success, #16a34a);
}

.dialog-icon--error {
  background: var(--color-danger-light, #fee2e2);
  color: var(--color-danger, #dc2626);
}

/* Title */
.dialog-title {
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-text-primary, #212529);
  margin: 0 0 var(--space-sm, 8px);
}

/* Message */
.dialog-message {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-secondary, #6c757d);
  line-height: var(--line-height-base, 1.5);
  margin: 0 0 var(--space-lg, 24px);
}

/* Actions */
.dialog-actions {
  display: flex;
  gap: var(--space-sm, 8px);
  justify-content: center;
}

/* Buttons */
.dialog-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm, 8px) var(--space-lg, 24px);
  border-radius: var(--radius-base, 8px);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: var(--font-weight-medium, 500);
  font-family: inherit;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast, 0.15s ease);
  min-width: 100px;
}

.dialog-btn:focus-visible {
  outline: 2px solid var(--color-primary, #2563EB);
  outline-offset: 2px;
}

.dialog-btn--cancel {
  background: var(--color-gray-100, #f8f9fa);
  color: var(--color-text-secondary, #6c757d);
  border: 1px solid var(--border-color, #dee2e6);
}

.dialog-btn--cancel:hover {
  background: var(--color-gray-200, #e9ecef);
  color: var(--color-text-primary, #212529);
}

.dialog-btn--confirm {
  background: var(--color-primary, #2563EB);
  color: var(--color-white, #fff);
}

.dialog-btn--confirm:hover {
  background: var(--color-primary-hover, #1D4ED8);
  box-shadow: 0 2px 8px var(--color-primary-shadow, rgba(37, 99, 235, 0.3));
}

.dialog-btn--ok.dialog-btn--success {
  background: var(--color-success, #16a34a);
  color: var(--color-white, #fff);
}

.dialog-btn--ok.dialog-btn--success:hover {
  filter: brightness(0.9);
  box-shadow: 0 2px 8px var(--color-success-shadow, rgba(16, 185, 129, 0.3));
}

.dialog-btn--ok.dialog-btn--error {
  background: var(--color-danger, #dc2626);
  color: var(--color-white, #fff);
}

.dialog-btn--ok.dialog-btn--error:hover {
  filter: brightness(0.9);
  box-shadow: 0 2px 8px var(--color-danger-shadow, rgba(220, 38, 38, 0.3));
}

/* ===== Transitions ===== */

/* Backdrop fade */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}
.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

/* Panel scale */
.dialog-scale-enter-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.dialog-scale-leave-active {
  transition: all 0.15s ease-in;
}
.dialog-scale-enter-from {
  opacity: 0;
  transform: scale(0.9);
}
.dialog-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
