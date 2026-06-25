import { reactive } from 'vue'

const state = reactive({
  visible: false,
  title: '',
  message: '',
  type: 'confirm', // 'confirm' | 'success' | 'error'
  resolve: null
})

function open(type, message, title) {
  // If a dialog is already open, resolve it first (prevents stacking)
  if (state.resolve) {
    state.resolve(false)
  }

  return new Promise((resolve) => {
    state.type = type
    state.message = message
    state.title = title || defaultTitle(type)
    state.resolve = resolve
    state.visible = true
  })
}

function defaultTitle(type) {
  switch (type) {
    case 'confirm': return 'Confirm'
    case 'success': return 'Success'
    case 'error': return 'Error'
    default: return ''
  }
}

function handleConfirm() {
  if (state.resolve) {
    state.resolve(true)
    state.resolve = null
  }
  state.visible = false
}

function handleCancel() {
  if (state.resolve) {
    state.resolve(false)
    state.resolve = null
  }
  state.visible = false
}

export const dialog = {
  confirm(message, title) {
    return open('confirm', message, title)
  },
  success(message, title) {
    return open('success', message, title)
  },
  error(message, title) {
    return open('error', message, title)
  }
}

export const dialogState = state
export const dialogActions = { handleConfirm, handleCancel }
