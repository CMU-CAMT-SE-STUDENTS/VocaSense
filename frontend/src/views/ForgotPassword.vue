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

        <button type="submit" class="btn-primary" :disabled="submitted">
          {{ submitted ? 'Email Sent!' : 'Send Reset Link' }}
        </button>

        <p class="back-link">
          <a href="#" class="auth-link" @click.prevent="goToLogin">Back to Login</a>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const submitted = ref(false)

const form = reactive({ email: '' })
const errors = reactive({ email: '' })

const validate = () => {
  errors.email = ''
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    return false
  }
  if (!form.email.includes('@')) {
    errors.email = 'Please enter a valid email address'
    return false
  }
  return true
}

const handleSubmit = () => {
  if (validate()) {
    console.log('Forgot password submitted:', form.email)
    // TODO: connect to Supabase auth - sendPasswordResetEmail
    submitted.value = true
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
