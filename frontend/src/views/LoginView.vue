<template>
  <div class="page-wrapper">
    <!-- Left Panel (desktop only) -->
    <div class="left-panel">
      <div class="left-content">
        <div class="icon-circle">
          <img src="@/assets/icons/Microphone.png" alt="Microphone" width="44" height="44" />
        </div>
        <h1 class="brand-title">Welcome To VocaSense</h1>
        <p class="brand-subtitle">Monitor your vocal health with AI-powered analysis</p>
      </div>
    </div>

    <!-- Right Panel -->
    <div class="right-panel">
      <div class="form-container">
        <h2 class="form-title">Welcome back!</h2>
        <p class="form-subtitle">Sign in to access your voice health history</p>

        <form @submit.prevent="handleSubmit" novalidate>
          <!-- Username or Email -->
          <div class="field-group">
            <label class="field-label">Username or Email</label>
            <input
              v-model="form.identifier"
              type="text"
              class="field-input"
              :class="{ 'input-error': errors.identifier }"
              placeholder="Enter your username or email"
            />
            <span v-if="errors.identifier" class="error-text">{{ errors.identifier }}</span>
          </div>

          <!-- Password -->
          <div class="field-group">
            <label class="field-label">Password</label>
            <div class="input-wrapper">
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="field-input password-input"
                :class="{ 'input-error': errors.password }"
                placeholder="Enter your password"
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
          </div>

          <!-- Forgot Password -->
          <p class="forgot-link">
            <a href="#" class="auth-link" @click.prevent="goToForgotPassword">Forgot Password?</a>
          </p>

          <!-- Login Button -->
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ retryCount > 0 ? 'Retrying...' : isSubmitting ? 'Logging In...' : 'Log In' }}
          </button>

          <!-- Divider -->
          <div class="divider">
            <span class="divider-line"></span>
            <span class="divider-text">or</span>
            <span class="divider-line"></span>
          </div>

          <!-- Continue without Login -->
          <button type="button" class="btn-outline" @click="continueWithoutLogin">Continue without Login</button>

          <!-- Sign Up Link -->
          <p class="switch-auth">
            Don't have an account?
            <a href="#" class="auth-link" @click.prevent="goToSignUp">Sign Up</a>
          </p>
        </form>
      </div>
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
const showPassword = ref(false)
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

const form = reactive({
  identifier: '',
  password: ''
})

const errors = reactive({
  identifier: '',
  password: ''
})

const validate = () => {
  let valid = true
  errors.identifier = ''
  errors.password = ''

  if (!form.identifier.trim()) {
    errors.identifier = 'Email or username is required'
    valid = false
  }

  if (!form.password.trim()) {
    errors.password = 'Password is required'
    valid = false
  }

  return valid
}

const handleSubmit = async () => {
  if (!validate()) return
  isSubmitting.value = true

  const attemptLogin = async () => {
    let loginEmail = form.identifier
    if (!loginEmail.includes('@')) {
      const { data, error: userError } = await supabase
        .from('account')
        .select('email')
        .eq('username', form.identifier)
        .maybeSingle()

      if (userError) throw userError
      if (!data) {
        errors.identifier = 'Invalid email/username or password'
        return false
      }
      loginEmail = data.email
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: loginEmail,
      password: form.password
    })

    if (error) {
      const msg = (error.message || '').toLowerCase()
      if (msg.includes('fetch') || msg.includes('network') || msg.includes('connect')) {
        throw error
      }
      errors.password = 'Invalid email/username or password'
      return false
    }

    return true
  }

  try {
    retryCount.value = 0
    for (let attempt = 0; attempt < 2; attempt++) {
      if (attempt > 0) {
        retryCount.value = attempt
        await new Promise(resolve => setTimeout(resolve, 3000))
      }
      try {
        const success = await attemptLogin()
        if (!success) return
        showToast('Logged in successfully!')
        setTimeout(() => router.push('/'), 700)
        return
      } catch (err) {
        console.error(`Login attempt ${attempt + 1} failed:`, err)
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

const goToSignUp = () => {
  router.push('/signup')
}

const goToForgotPassword = () => {
  router.push('/forgot-password')
}

const continueWithoutLogin = () => {
  router.push('/')
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
  font-family: 'Poppins', sans-serif;
}

/* ── Left Panel ── */
.left-panel {
  width: 40%;
  background: linear-gradient(180deg, #FFFFFF 0%, #F4F7FF 60%, #DAE0FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.left-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}

.icon-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6DA5FF 0%, #B8D3FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(93, 155, 255, 0.35);
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0.5px;
  background: linear-gradient(137deg, #5F8FE3 6.18%, #95B9F7 94.01%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-top: 8px;
}

.brand-subtitle {
  color: #717171;
  text-align: center;
  font-size: 16px;
  font-weight: 500;
  line-height: 30px;
  letter-spacing: 0.5px;
}

/* ── Right Panel ── */
.right-panel {
  width: 60%;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  overflow-y: auto;
}

.form-container {
  width: 100%;
  max-width: 460px;
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
  text-align: center;
}

.form-subtitle {
  font-size: 13px;
  font-weight: 400;
  color: #888;
  margin-bottom: 28px;
  text-align: center;
}

/* ── Fields ── */
.field-group {
  margin-bottom: 14px;
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
  border: 1.5px solid #D6E0F5;
  border-radius: 8px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  color: #333;
  background-color: #F4F7FF;
  outline: none;
  transition: border-color 0.2s, background-color 0.2s;
}

.field-input::placeholder {
  color: #aaa;
}

.field-input:focus {
  border-color: #6594E4;
  background-color: #EEF3FF;
}

.field-input.input-error {
  border-color: #e53935;
}

/* ── Password Toggle ── */
.input-wrapper {
  position: relative;
}

input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear {
  display: none;
}

input[type="password"]::-webkit-credentials-auto-fill-button {
  visibility: hidden;
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

/* ── Error Text ── */
.error-text {
  display: block;
  font-size: 11px;
  color: #e53935;
  margin-top: 4px;
}

/* ── Forgot Link ── */
.forgot-link {
  text-align: right;
  margin-top: 6px;
  margin-bottom: 4px;
}

.forgot-link .auth-link {
  font-size: 12px;
  font-weight: 500;
}

/* ── Buttons ── */
.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(102deg, #95B9F7 8.63%, #6594E4 92.33%);
  color: white;
  border: none;
  border-radius: 15px;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-primary:hover {
  opacity: 0.88;
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-outline {
  width: 100%;
  padding: 12px;
  background: transparent;
  color: #6594E4;
  border: 1.5px solid #6594E4;
  border-radius: 15px;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.btn-outline:hover {
  background-color: #f0f5ff;
}

.btn-outline:active {
  transform: scale(0.98);
}

/* ── Divider ── */
.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background-color: #e0e0e0;
}

.divider-text {
  font-size: 13px;
  color: #aaa;
}

/* ── Switch Auth ── */
.switch-auth {
  text-align: center;
  margin-top: 18px;
  font-size: 13px;
  color: #555;
}

.auth-link {
  background: linear-gradient(102deg, #95B9F7 8.63%, #6594E4 92.33%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 16px;
  font-weight: 600;
  line-height: 30px;
  letter-spacing: 0.5px;
  text-decoration: none;
  margin-left: 4px;
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

.toast.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.toast.error {
  background: #fff1f2;
  color: #9f1239;
  border: 1px solid #fecdd3;
}

.toast-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.toast-message {
  flex: 1;
  line-height: 1.4;
}

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

.toast-close:hover {
  opacity: 1;
}

.toast-enter-active {
  animation: slideIn 0.1s ease;
}

.toast-leave-active {
  animation: slideOut 0.1s ease forwards;
}

@keyframes slideIn {
  from { transform: translateX(110%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

@keyframes slideOut {
  from { transform: translateX(0);    opacity: 1; }
  to   { transform: translateX(110%); opacity: 0; }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .left-panel {
    display: none;
  }

  .right-panel {
    width: 100%;
    background: linear-gradient(180deg, #FFFFFF 0%, #F4F7FF 60%, #DAE0FF 100%);
    padding: 40px 20px;
    align-items: center;
  }

  .form-container {
    background: #fff;
    border-radius: 20px;
    padding: 32px 24px;
    box-shadow: 0 8px 32px rgba(101, 148, 228, 0.18);
  }
}

@media (max-width: 480px) {
  .right-panel {
    padding: 24px 16px;
  }

  .form-container {
    padding: 24px 18px;
  }

  .form-title {
    font-size: 22px;
  }
}
</style>
