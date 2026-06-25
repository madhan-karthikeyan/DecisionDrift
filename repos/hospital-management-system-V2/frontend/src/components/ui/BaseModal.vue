<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="handleOverlayClick">
        <div class="modal" :class="[`modal--${size}`]" role="dialog" aria-modal="true">
          <div class="modal__header">
            <slot name="header">
              <h2 class="modal__title">{{ title }}</h2>
            </slot>
            <button v-if="closable" class="modal__close" @click="close" aria-label="Close">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          <div class="modal__body">
            <slot></slot>
          </div>
          <div v-if="$slots.footer" class="modal__footer">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { watch, onBeforeUnmount } from 'vue'

export default {
  name: 'BaseModal',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ''
    },
    size: {
      type: String,
      default: 'md',
      validator: (value) => ['sm', 'md', 'lg', 'xl', 'full'].includes(value)
    },
    closable: {
      type: Boolean,
      default: true
    },
    closeOnOverlay: {
      type: Boolean,
      default: true
    },
    closeOnEscape: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:modelValue', 'close'],
  setup(props, { emit }) {
    let currentEscapeHandler = null

    const close = () => {
      emit('update:modelValue', false)
      emit('close')
    }

    const handleOverlayClick = () => {
      if (props.closeOnOverlay) {
        close()
      }
    }

    const cleanup = () => {
      if (currentEscapeHandler) {
        document.removeEventListener('keydown', currentEscapeHandler)
        currentEscapeHandler = null
      }
      document.body.style.overflow = ''
    }

    watch(() => props.modelValue, (isOpen) => {
      cleanup()

      if (!isOpen) return

      const handleEscape = (e) => {
        if (e.key === 'Escape' && props.closeOnEscape) {
          close()
        }
      }

      currentEscapeHandler = handleEscape
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    })

    onBeforeUnmount(() => {
      cleanup()
    })

    return {
      close,
      handleOverlayClick
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  z-index: var(--z-modal);
}

.modal {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  animation: scaleIn 0.25s ease;
}

.modal--sm {
  width: 100%;
  max-width: 400px;
}

.modal--md {
  width: 100%;
  max-width: 560px;
}

.modal--lg {
  width: 100%;
  max-width: 720px;
}

.modal--xl {
  width: 100%;
  max-width: 960px;
}

.modal--full {
  width: 100%;
  max-width: calc(100vw - 48px);
  height: calc(100vh - 48px);
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-gray-200);
  flex-shrink: 0;
}

.modal__title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-base);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal__close:hover {
  background: var(--color-gray-100);
  color: var(--color-text-primary);
}

.modal__body {
  padding: var(--space-lg);
  overflow-y: auto;
  flex: 1;
}

.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-gray-200);
  background: var(--color-gray-50);
  flex-shrink: 0;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95);
}
</style>
