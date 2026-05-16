<template>
  <nav class="navbar">
    <div class="nav-content">
      <!-- logo -->
      <div class="nav-logo">
        <img src="@/assets/icons/logo.png" alt="VocaSense Logo" class="nav-logo-img" />
      </div>

      <!-- menu for Desktop -->
      <div class="nav-links desktop-only">
        <a href="#" class="nav-link active" @click.prevent="handleScroll('top')">Home</a>
        <a href="#how-it-works" class="nav-link" @click.prevent="handleScroll('how-it-works')">How it Works</a>
        <a v-if="!user" href="#" class="nav-link" @click.prevent="goToSignUp">Sign up</a>
      </div>

      <!-- auth zone for Desktop -->
      <div class="desktop-only auth-zone-desktop">
        <!-- Avatar Container -->
        <div v-if="user" class="avatar-container" v-click-outside="closeProfileMenu">
          <div class="avatar-gradient" @click="toggleProfileMenu">
            {{ firstLetter }}
          </div>
          <!-- Profile Dropdown -->
          <div v-if="isProfileMenuOpen" class="avatar-dropdown">
            <div class="dropdown-user-info">
              <p class="user-name-display">{{ username }}</p>
            </div>
            <hr class="dropdown-divider" />

            <!-- History Button -->
            <button class="btn-dropdown-item" @click="goToHistory">History</button>
            <hr class="dropdown-divider" />
            <button class="btn-dropdown-logout" @click="handleLogout">Logout</button>
          </div>
        </div>

        <!-- Login Button -->
        <button v-else class="btn-login" @click="goToLogin">Login</button>
      </div>

      <!-- Mobile Menu Toggle -->
      <button
        class="menu-toggle mobile-only"
        :class="{ 'is-active': isMenuOpen }"
        @click="toggleMenu"
        aria-label="Toggle navigation"
      >
        <span class="bar"></span>
        <span class="bar"></span>
        <span class="bar"></span>
      </button>
    </div>

    <!-- Mobile Menu -->
    <div class="nav-menu-mobile mobile-only" :class="{ 'is-open': isMenuOpen }">


      <!-- Auth Zone for Mobile -->
      <div class="auth-zone-mobile">
        <div v-if="user" class="mobile-user-menu">
          <div class="mobile-user-info">
            <div class="avatar-gradient-mobile">{{ firstLetter }}</div>
            <span class="mobile-username">{{ username }}</span>
          </div>

          <hr class="mobile-menu-divider" />

          <a href="#" class="nav-link-mobile" @click.prevent="goToHistory">History</a>
          <button class="nav-link-mobile btn-logout-mobile-stacked" @click="handleLogout">Logout</button>
        </div>
        <template v-else>
          <a href="#" class="nav-link-mobile" @click.prevent="goToSignUp">Sign up</a>
          <button class="btn-login-mobile" @click="goToLogin">Login</button>
        </template>
      </div>
       <a href="#" class="nav-link-mobile" @click.prevent="handleScroll('top')">Home</a>
      <a href="#how-it-works" class="nav-link-mobile" @click.prevent="handleScroll('how-it-works')">How it Works</a>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

const emit = defineEmits(['scroll-to'])
const router = useRouter()

const isMenuOpen = ref(false)
const isProfileMenuOpen = ref(false)
const user = ref(null)

const username = computed(() => {
  if (!user.value) return ''
  return user.value.user_metadata?.username || user.value.email|| 'User'
})

const firstLetter = computed(() => {
  return username.value.charAt(0).toUpperCase()
})

const goToHistory = () => {
  closeMenu()
  closeProfileMenu()
  router.push('/history')
}

const toggleProfileMenu = (event) => {
  event.stopPropagation()
  isProfileMenuOpen.value = !isProfileMenuOpen.value
}

const closeProfileMenu = () => {
  isProfileMenuOpen.value = false
}

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

const goToLogin = () => { closeMenu(); router.push('/login') }
const goToSignUp = () => { closeMenu(); router.push('/signup') }
const handleScroll = (id) => { closeMenu(); emit('scroll-to', id) }

const handleLogout = async () => {
  closeMenu()
  closeProfileMenu()
  await supabase.auth.signOut()
  router.push('/')
}

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  user.value = data.session?.user ?? null

  supabase.auth.onAuthStateChange((_event, session) => {
    user.value = session?.user ?? null
  })
})

const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value()
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(101, 148, 228, 0.12);
  padding: 0 40px;
}

.nav-content {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 64px;
  gap: 32px;
}

.nav-logo {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.nav-logo-img {
  height: 38px;
  width: auto;
  object-fit: contain;
}

/* ── Desktop Styles ── */
.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-left: auto;
}

.auth-zone-desktop {
  margin-left: 0;
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  text-decoration: none;
  transition: color 0.2s;
}

.nav-link:hover,
.nav-link.active {
  color: #6594E4;
}

.btn-login {
  padding: 8px 24px;
  background: linear-gradient(102deg, #95B9F7 8.63%, #6594E4 92.33%);
  color: white;
  border: none;
  border-radius: 20px;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.btn-login:hover {
  opacity: 0.88;
}

/* ── Profile Avatar Gradient ── */
.avatar-container {
  position: relative;
  display: inline-block;
}

.avatar-gradient {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #A5C4F7 0%, #6594E4 100%);
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(101, 148, 228, 0.25);
  transition: transform 0.2s, box-shadow 0.2s;
  user-select: none;
}

.avatar-gradient:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(101, 148, 228, 0.35);
}

.avatar-dropdown {
  position: absolute;
  top: 50px;
  right: 0;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(101, 148, 228, 0.15);
  min-width: 160px;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.2s ease;
}

.dropdown-user-info {
  padding: 6px 16px 6px;
}

.user-name-display {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  border: 0;
  border-top: 1px solid #b4b3d8;
  margin: 4px 0;
}

/* สไตล์ปุ่มทั่วไปใน Dropdown (เช่น ปุ่ม History) */
.btn-dropdown-item {
  background: transparent;
  border: none;
  color: #444444;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 16px;
  text-align: left;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s, color 0.2s;
}

.btn-dropdown-item:hover {
  background: #F4F7FF;
  color: #6594E4;
}

.btn-dropdown-logout {
  background: transparent;
  border: none;
  color: #FF5C5C;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 16px;
  text-align: left;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}

.btn-dropdown-logout:hover {
  background: #FFF5F5;
}

/* ── Mobile Styles ── */
.mobile-only {
  display: none !important;
}

.menu-toggle {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  z-index: 101;
}

.menu-toggle .bar {
  height: 3px;
  width: 100%;
  background-color: #555;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.menu-toggle.is-active .bar:nth-child(1) { transform: translateY(7.5px) rotate(45deg); }
.menu-toggle.is-active .bar:nth-child(2) { opacity: 0; }
.menu-toggle.is-active .bar:nth-child(3) { transform: translateY(-7.5px) rotate(-45deg); }

.nav-menu-mobile {
  position: absolute;
  top: 64px;
  left: 0;
  width: 100%;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(101, 148, 228, 0.12);
  padding: 24px;
  flex-direction: column;
  gap: 16px;
  align-items: center;
  opacity: 0;
  transform: translateY(-10px);
  transition: opacity 0.3s ease, transform 0.3s ease;
  pointer-events: none;
}

.nav-menu-mobile.is-open {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.nav-link-mobile {
  font-size: 16px;
  font-weight: 500;
  color: #555;
  text-decoration: none;
  width: 100%;
  text-align: center;
  padding: 10px 0;
  display: block;
  transition: color 0.2s;
}

.nav-link-mobile:hover {
  color: #6594E4;
}

.auth-zone-mobile {
  width: 80%;
  border: solid 3px rgba(101, 148, 228, 0.486);
  border-radius: 1rem;
  padding: 10px;
}

.btn-login-mobile {
  width: 100%;
  max-width: 200px;
  padding: 10px 24px;
  background: linear-gradient(102deg, #95B9F7 8.63%, #6594E4 92.33%);
  color: white;
  border: none;
  border-radius: 20px;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin: 8px auto 0;
  display: block;
}

.mobile-user-menu {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mobile-user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 0;
  width: 100%;
}

.avatar-gradient-mobile {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #A5C4F7 0%, #6594E4 100%);
  color: #FFFFFF;
  font-size: 30px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mobile-username {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-menu-divider {
  border: 0;
  border-top: 2px solid #c0d4f8;
  width: 60%;
  margin: 12px 0 4px;
}

.btn-logout-mobile-stacked {
  background: transparent;
  border: none;
  color: #FF5C5C;
  font-family: 'Poppins', sans-serif;
  cursor: pointer;
}

.btn-logout-mobile-stacked:hover {
  color: #e04444;
}

/* Helper Classes */
.desktop-only { display: flex; }
.mobile-only { display: none !important; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Responsive Media Queries ── */
@media (max-width: 768px) {
  .navbar { padding: 0 20px; }
  .desktop-only { display: none !important; }
  .mobile-only { display: flex !important; }
  .menu-toggle { display: flex; margin-left: auto; }
}
</style>
