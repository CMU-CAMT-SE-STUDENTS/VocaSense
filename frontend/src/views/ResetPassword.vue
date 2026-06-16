<template>
  <div class="page-wrapper">
    <div class="card">
      <!-- Brand Mark -->
      <img src="@/assets/icons/logo.png" alt="VocaSense" class="brand-logo" />

      <h2 class="card-title">Reset Password</h2>

      <form @submit.prevent="handleSubmit" novalidate>
        <div class="field-group">
          <label class="field-label">New Password</label>
          <div class="input-wrapper">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="field-input password-input"
              :class="{ 'input-error': errors.password }"
              placeholder="Enter your new password"
              @focus="touched = true"
            />
            <button type="button" class="toggle-eye" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
          <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
          <div v-if="form.password" class="password-requirements">
            <div class="req-item" :class="{ met: passwordChecks.length }">
              <span class="req-icon">{{ passwordChecks.length ? '✓' : '○' }}</span>
              At least 8 characters
            </div>
            <div class="req-item" :class="{ met: passwordChecks.uppercase }">
              <span class="req-icon">{{ passwordChecks.uppercase ? '✓' : '○' }}</span>
              At least 1 uppercase letter
            </div>
            <div class="req-item" :class="{ met: passwordChecks.number }">
              <span class="req-icon">{{ passwordChecks.number ? '✓' : '○' }}</span>
              At least 1 number
            </div>
          </div>
        </div>

        <button type="submit" class="btn-primary" :disabled="isSubmitting">
          {{ retryCount > 0 ? 'Retrying...' : isSubmitting ? 'Updating...' : 'Confirm' }}
        </button>
      </form>
    </div>
  </div>

  <!-- Toast Notification -->
  <transition name="toast">
    <div v-if="toast.show" class="toast" :class="toast.type">
      <div class="toast-icon">
        <svg v-if="toast.type === 'success'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <span class="toast-message">{{ toast.message }}</span>
      <button class="toast-close" @click="toast.show = false">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </transition>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

const router = useRouter()
const showPassword = ref(false)
const touched = ref(false)
const isSubmitting = ref(false)
const retryCount = ref(0)

const toast = reactive({ show: false, message: '', type: 'success' })
let toastTimer = null

const showToast = (message, type = 'success', duration = 3000) => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.message = message
  toast.type = type
  toast.show = true
  toastTimer = setTimeout(() => { toast.show = false }, duration)
}

const form = reactive({ password: '' })
const errors = reactive({ password: '' })

const passwordChecks = computed(() => ({
  length:    form.password.length >= 8,
  uppercase: /[A-Z]/.test(form.password),
  number:    /[0-9]/.test(form.password)
}))

const validate = () => {
  errors.password = ''
  if (!form.password.trim()) {
    errors.password = 'Password is required'
    return false
  }
  if (form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    return false
  }
  if (!/[A-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
    errors.password = 'Password must contain uppercase letters and numbers'
    return false
  }
  return true
}

watch(() => form.password, () => {
  if (touched.value) validate()
})

const handleSubmit = async () => {
  touched.value = true
  if (!validate()) return
  isSubmitting.value = true

  try {
    retryCount.value = 0
    for (let attempt = 0; attempt < 2; attempt++) {
      if (attempt > 0) {
        retryCount.value = attempt
        await new Promise(resolve => setTimeout(resolve, 3000))
      }
      try {
        const { error } = await supabase.auth.updateUser({ password: form.password })
        if (error) throw error

        showToast('Password updated successfully!')
        setTimeout(() => router.push('/login'), 2000)
        return
      } catch (err) {
        console.error(`Reset password attempt ${attempt + 1} failed:`, err)
        if (err?.message?.toLowerCase().includes('new password should be different')) {
          errors.password = 'New password must be different from your current password'
          return
        }
        if (attempt === 1) {
          showToast('The system cannot connect to the database. Please try again later.', 'error')
        }
      }
    }
  } finally {
    isSubmitting.value = false
    retryCount.value = 0
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.page-wrapper {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #ffffff 0%, #f4f7ff 60%, #dae0ff 100%);
  font-family: 'Poppins', sans-serif;
  padding: 24px 16px;
}

.card {
  background: #ffffff;
  border-radius: 20px;
  padding: 40px 36px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 8px 32px rgba(101, 148, 228, 0.18);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ── Brand Logo ── */
.brand-logo {
  height: 36px;
  width: auto;
  margin-bottom: 20px;
  object-fit: contain;
}

/* ── Card Text ── */
.card-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 24px;
  text-align: center;
}

/* ── Form ── */
form {
  width: 100%;
}

.field-group {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
}

.field-input {
  width: 100%;
  padding: 10px 14px;
  border: 1.5px solid #d6e0f5;
  border-radius: 8px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  color: #333;
  background-color: #f4f7ff;
  outline: none;
  transition: border-color 0.2s, background-color 0.2s;
}

.field-input::placeholder {
  color: #aaa;
}

.field-input:focus {
  border-color: #6594e4;
  background-color: #eef3ff;
}

.field-input.input-error {
  border-color: #e53935;
}

/* ── Password Toggle ── */
input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear {
  display: none;
}

.input-wrapper {
  position: relative;
}

.password-input {
  padding-right: 42px;
}

.toggle-eye {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  opacity: 0.5;
}

.toggle-eye:hover {
  opacity: 0.8;
}

.error-text {
  display: block;
  font-size: 11px;
  color: #e53935;
  margin-top: 4px;
}

.password-requirements {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.req-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #aaa;
  transition: color 0.2s;
}

.req-item.met {
  color: #16a34a;
}

.req-icon {
  width: 14px;
  text-align: center;
  font-size: 12px;
}


/* ── Button ── */
.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: white;
  border: none;
  border-radius: 15px;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 6px;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-primary:hover:not(:disabled) { opacity: 0.88; }
.btn-primary:active:not(:disabled) { transform: scale(0.98); }
.btn-primary:disabled { opacity: 0.7; cursor: default; }

/* ── Toast ── */
.toast {
  position: fixed;
  top: 28px;
  right: 28px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  min-width: 260px;
  max-width: 360px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 9999;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 500;
}

.toast.success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.toast.error   { background: #fff1f2; color: #9f1239; border: 1px solid #fecdd3; }

.toast-icon { flex-shrink: 0; display: flex; align-items: center; }
.toast-message { flex: 1; line-height: 1.4; }

.toast-close {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  opacity: 0.5;
  color: inherit;
}

.toast-close:hover { opacity: 1; }

.toast-enter-active { animation: slideIn 0.1s ease; }
.toast-leave-active { animation: slideOut 0.1s ease forwards; }

@keyframes slideIn {
  from { transform: translateX(110%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

@keyframes slideOut {
  from { transform: translateX(0);    opacity: 1; }
  to   { transform: translateX(110%); opacity: 0; }
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .card {
    padding: 32px 20px;
  }

  .card-title {
    font-size: 20px;
  }
}
</style>
