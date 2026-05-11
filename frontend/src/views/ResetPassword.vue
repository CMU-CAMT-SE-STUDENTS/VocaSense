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

        <button type="submit" class="btn-primary">Confirm</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

const router = useRouter()
const showPassword = ref(false)

const form = reactive({ password: '' })
const errors = reactive({ password: '' })

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
  return true
}

const handleSubmit = async () => {
  if (validate()) {
    console.log('Reset password submitted')
    // TODO: connect to Supabase auth - updateUser({ password })
    try{
      const { data, error } = await supabase.auth.updateUser({ password: form.password })
      if (error) throw error

      console.log('Password updated successfully:', data)
    } catch (error) {
      console.error('Error updating password:', error)
      alert('An error occurred while updating the password. Please try again.')
    }
    router.push('/login')
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

.btn-primary:hover {
  opacity: 0.88;
}

.btn-primary:active {
  transform: scale(0.98);
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
