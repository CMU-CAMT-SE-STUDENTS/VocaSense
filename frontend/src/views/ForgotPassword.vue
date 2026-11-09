<template>
  <div class="page-wrapper">
    <div class="card">
      <!-- Brand Mark -->
      <img src="@/assets/icons/logo.png" alt="VocaSense" class="brand-logo" />

      <h2 class="card-title">Forgot Password</h2>
      <p class="card-subtitle">
        Enter your email address below to receive a link to reset your password.
      </p>

      <form @submit.prevent="handleSubmit" novalidate>
        <div class="field-group">
          <label class="field-label">Email</label>
          <input
            v-model="form.email"
            type="email"
            class="field-input"
            :class="{ 'input-error': errors.email }"
            placeholder="Enter your email"
          />
          <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
        </div>

        <button type="submit" class="btn-primary" :disabled="submitted || isSubmitting">
          {{ submitted ? 'Email Sent!' : retryCount > 0 ? 'Retrying...' : isSubmitting ? 'Sending...' : 'Send Reset Link' }}
        </button>

        <p class="back-link">
          <a href="#" class="auth-link" @click.prevent="goToLogin">Back to Login</a>
        </p>
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

const router = useRouter()
const submitted = ref(false)
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

const form = reactive({ email: '' })
const errors = reactive({ email: '' })

const validate = () => {
  errors.email = ''
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    return false
  }
  if (!form.email.includes('@')) {
    errors.email = `Please include an '@' in the email address. '${form.email}' is missing an '@'`
    return false
  }
  return true
}

const handleSubmit = async () => {
  if (!validate()) return
  isSubmitting.value = true

  const attemptSubmit = async () => {
    const { data: existingEmail, error: checkError } = await supabase
      .from('account')
      .select('email')
      .eq('email', form.email)
      .maybeSingle()

    if (checkError) throw checkError

    if (!existingEmail) {
      errors.email = 'Email not found'
      return false
    }

    const { error } = await supabase.auth.resetPasswordForEmail(form.email, {
      redirectTo: `${window.location.origin}/reset-password`
    })
    if (error) throw error

    return true
  }

  const withTimeout = (promise, ms = 5000) =>
    Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('network')), ms))
    ])

  try {
    retryCount.value = 0
    for (let attempt = 0; attempt < 2; attempt++) {
      if (attempt > 0) {
        retryCount.value = attempt
        await new Promise(resolve => setTimeout(resolve, 1500))
      }
      try {
        if (!navigator.onLine) throw new Error('network')
        const success = await withTimeout(attemptSubmit())
        if (!success) return
        submitted.value = true
        return
      } catch (err) {
        console.error(`Forgot password attempt ${attempt + 1} failed:`, err)
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

const goToLogin = () => {
  router.push('/login')
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
  margin-bottom: 10px;
  text-align: center;
}

.card-subtitle {
  font-size: 13px;
  font-weight: 400;
  color: #888;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 28px;
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

.error-text {
  display: block;
  font-size: 11px;
  color: #e53935;
  margin-top: 4px;
}

.server-error {
  font-size: 13px;
  margin-bottom: 8px;
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

.btn-primary:hover:not(:disabled) {
  opacity: 0.88;
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: default;
}

/* ── Back Link ── */
.back-link {
  text-align: center;
  margin-top: 18px;
}

.auth-link {
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

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

.toast-enter-active { animation: slideIn 0.3s ease; }
.toast-leave-active { animation: slideOut 0.25s ease forwards; }

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
