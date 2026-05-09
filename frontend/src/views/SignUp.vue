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
        <h2 class="form-title">Create Your Account</h2>
        <p class="form-subtitle">Start monitoring your voice health today</p>

        <form @submit.prevent="handleSubmit" novalidate>
          <!-- First Name -->
          <div class="field-group">
            <label class="field-label">First Name</label>
            <input
              v-model="form.firstName"
              type="text"
              class="field-input"
              :class="{ 'input-error': errors.firstName }"
              placeholder="Enter your first name"
            />
            <span v-if="errors.firstName" class="error-text">{{ errors.firstName }}</span>
          </div>

          <!-- Last Name -->
          <div class="field-group">
            <label class="field-label">Last Name</label>
            <input
              v-model="form.lastName"
              type="text"
              class="field-input"
              :class="{ 'input-error': errors.lastName }"
              placeholder="Enter your last name"
            />
            <span v-if="errors.lastName" class="error-text">{{ errors.lastName }}</span>
          </div>

          <!-- Username -->
          <div class="field-group">
            <label class="field-label">Username</label>
            <input
              v-model="form.username"
              type="text"
              class="field-input"
              :class="{ 'input-error': errors.username }"
              placeholder="Enter your username"
            />
            <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
          </div>

          <!-- Email -->
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

          <!-- Submit Button -->
          <button type="submit" class="btn-primary">Create Account</button>

          <!-- Login Link -->
          <p class="switch-auth">
            Already have an account?
            <a href="#" class="auth-link" @click.prevent="goToLogin">Log in</a>
          </p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showPassword = ref(false)

const form = reactive({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: ''
})

const errors = reactive({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: ''
})

const validate = () => {
  let valid = true

  errors.firstName = ''
  errors.lastName = ''
  errors.username = ''
  errors.email = ''
  errors.password = ''

  if (!form.firstName.trim()) {
    errors.firstName = 'First name is required'
    valid = false
  } else if (!/^[A-Za-z]+$/.test(form.firstName)) {
    errors.firstName = 'First name must contain only letters'
    valid = false
  }

  if (!form.lastName.trim()) {
    errors.lastName = 'Last name is required'
    valid = false
  } else if (!/^[A-Za-z]+$/.test(form.lastName)) {
    errors.lastName = 'Last name must contain only letters'
    valid = false
  }

  if (!form.username.trim()) {
    errors.username = 'Username is required'
    valid = false
  } else if (!/^[A-Za-z0-9_\-.*]+$/.test(form.username)) {
    errors.username = 'Username contains invalid characters'
    valid = false
  }

  if (!form.email.trim()) {
    errors.email = 'Email is required'
    valid = false
  } else if (!form.email.includes('@')) {
    errors.email = `Please include an '@' in the email address. '${form.email}' is missing an '@'`
    valid = false
  }

  if (!form.password.trim()) {
    errors.password = 'Password is required'
    valid = false
  } else if (form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    valid = false
  } else if (!/[A-Z]/.test(form.password) || !/[0-9]/.test(form.password)) {
    errors.password = 'Password must contain uppercase letters and numbers'
    valid = false
  }

  return valid
}

const handleSubmit = () => {
  if (validate()) {
    console.log('Form submitted:', form)
    // TODO: connect to Supabase auth
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

/* ── Button ── */
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
