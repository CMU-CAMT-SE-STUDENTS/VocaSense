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
              <div class="avatar-gradient-sm">{{ firstLetter }}</div>
              <p class="user-name-display">{{ username }}</p>
            </div>
            <hr class="dropdown-divider" />

            <button class="btn-dropdown-item" @click="goToHistory">
              <img src="@/assets/icons/history-svgrepo-com.svg" class="dropdown-icon" />
              Voice history
            </button>
            <hr class="dropdown-divider" />
            <button class="btn-dropdown-logout" @click="handleLogout">
              <img src="@/assets/icons/logout-svgrepo-com.svg" class="dropdown-icon icon-logout-red" />
              Log Out
            </button>
          </div>
        </div>

        <!-- Login Button -->
        <button v-else class="btn-login" @click="goToLogin">Login</button>
      </div>

      <!-- Mobile nav right: hamburger + avatar (logged in) -->
      <div class="mobile-nav-right mobile-only">
        <!-- Hamburger -->
        <button
          class="menu-toggle"
          :class="{ 'is-active': isMenuOpen }"
          @click="toggleMenu"
          aria-label="Toggle navigation"
        >
          <span class="bar"></span>
          <span class="bar"></span>
          <span class="bar"></span>
        </button>

        <!-- Mobile Avatar -->
        <div v-if="user" class="mobile-avatar-container" v-click-outside="closeMobileProfileMenu">
          <div class="avatar-gradient" @click="toggleMobileProfileMenu">
            {{ firstLetter }}
          </div>
          <!-- Mobile Profile Dropdown -->
          <div v-if="isMobileProfileMenuOpen" class="avatar-dropdown">
            <div class="dropdown-user-info">
              <div class="avatar-gradient-sm">{{ firstLetter }}</div>
              <p class="user-name-display">{{ username }}</p>
            </div>
            <hr class="dropdown-divider" />
            <button class="btn-dropdown-item" @click="goToHistory">
              <img src="@/assets/icons/history-svgrepo-com.svg" class="dropdown-icon" />
              Voice history
            </button>
            <hr class="dropdown-divider" />
            <button class="btn-dropdown-logout" @click="handleLogout">
              <img src="@/assets/icons/logout-svgrepo-com.svg" class="dropdown-icon icon-logout-red" />
              Log Out
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div class="nav-menu-mobile mobile-only" :class="{ 'is-open': isMenuOpen }">
      <ul class="mobile-menu-list">

        <!-- Home -->
        <li class="mobile-menu-item" @click="handleScroll('top')">
          <img src="@/assets/icons/home-svgrepo-com.svg" class="menu-item-icon" />
          <span class="text-home">Home</span>
        </li>

        <!-- How it Works -->
        <li class="mobile-menu-item" @click="handleScroll('how-it-works')">
          <img src="@/assets/icons/circle-info-svgrepo-com.svg" class="menu-item-icon" />
          <span>How it works</span>
        </li>

        <!-- Login (not logged in) -->
        <li v-if="!user" class="mobile-menu-item auth-item" @click="goToLogin">
          <svg class="menu-item-icon icon-login" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M8 6C8 3.79086 9.79086 2 12 2H17.5C19.9853 2 22 4.01472 22 6.5V17.5C22 19.9853 19.9853 22 17.5 22H12C9.79086 22 8 20.2091 8 18V17C8 16.4477 8.44772 16 9 16C9.55228 16 10 16.4477 10 17V18C10 19.1046 10.8954 20 12 20H17.5C18.8807 20 20 18.8807 20 17.5V6.5C20 5.11929 18.8807 4 17.5 4H12C10.8954 4 10 4.89543 10 6V7C10 7.55228 9.55228 8 9 8C8.44772 8 8 7.55228 8 7V6ZM12.2929 8.29289C12.6834 7.90237 13.3166 7.90237 13.7071 8.29289L16.7071 11.2929C17.0976 11.6834 17.0976 12.3166 16.7071 12.7071L13.7071 15.7071C13.3166 16.0976 12.6834 16.0976 12.2929 15.7071C11.9024 15.3166 11.9024 14.6834 12.2929 14.2929L13.5858 13L5 13C4.44772 13 4 12.5523 4 12C4 11.4477 4.44772 11 5 11L13.5858 11L12.2929 9.70711C11.9024 9.31658 11.9024 8.68342 12.2929 8.29289Z" fill="currentColor"/>
          </svg>
          <span class="text-login">Login</span>
        </li>

        <!-- Sign Up (not logged in) -->
        <li v-if="!user" class="mobile-menu-item auth-item" @click="goToSignUp">
          <svg class="menu-item-icon" viewBox="0 0 32 32" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <polygon points="32 14 28 14 28 10 26 10 26 14 22 14 22 16 26 16 26 20 28 20 28 16 32 16 32 14"/>
            <path d="M12,4A5,5,0,1,1,7,9a5,5,0,0,1,5-5m0-2a7,7,0,1,0,7,7A7,7,0,0,0,12,2Z"/>
            <path d="M22,30H20V25a5,5,0,0,0-5-5H9a5,5,0,0,0-5,5v5H2V25a7,7,0,0,1,7-7h6a7,7,0,0,1,7,7Z"/>
          </svg>
          <span>Sign up</span>
        </li>

      </ul>
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
const isMobileProfileMenuOpen = ref(false)
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
  closeMobileProfileMenu()
  router.push('/history')
}

const toggleProfileMenu = (event) => {
  event.stopPropagation()
  isProfileMenuOpen.value = !isProfileMenuOpen.value
}

const closeProfileMenu = () => {
  isProfileMenuOpen.value = false
}

const toggleMobileProfileMenu = (event) => {
  event.stopPropagation()
  isMenuOpen.value = false
  isMobileProfileMenuOpen.value = !isMobileProfileMenuOpen.value
}

const closeMobileProfileMenu = () => {
  isMobileProfileMenuOpen.value = false
}

const toggleMenu = () => {
  isMobileProfileMenuOpen.value = false
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
  closeMobileProfileMenu()
  await supabase.auth.signOut()
  router.push('/?loggedOut=true')
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
  min-width: 185px;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.2s ease;
}

.dropdown-user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 10px;
}

.avatar-gradient-sm {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #A5C4F7 0%, #6594E4 100%);
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-name-display {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.dropdown-divider {
  border: 0;
  border-top: 1px solid #e8eaf0;
  margin: 2px 0;
}

.dropdown-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
  flex-shrink: 0;
}

.icon-logout-red {
  filter: invert(47%) sepia(98%) saturate(1000%) hue-rotate(314deg) brightness(105%) contrast(101%);
}

.btn-dropdown-item {
  background: transparent;
  border: none;
  color: #444444;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 16px;
  text-align: left;
  cursor: pointer;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.2s, color 0.2s;
}

.btn-dropdown-item:hover {
  background: #F4F7FF;
  color: #6594E4;
}

.btn-dropdown-item:hover .dropdown-icon {
  filter: invert(44%) sepia(53%) saturate(500%) hue-rotate(192deg) brightness(99%) contrast(93%);
}

.btn-dropdown-logout {
  background: transparent;
  border: none;
  color: #FF5C5C;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 16px;
  text-align: left;
  cursor: pointer;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.2s;
}

.btn-dropdown-logout:hover {
  background: #FFF5F5;
}

/* ── Mobile Styles ── */
.mobile-only {
  display: none !important;
}

.mobile-nav-right {
  display: none;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.mobile-avatar-container {
  position: relative;
  display: inline-block;
}

.menu-toggle {
  display: flex;
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
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(101, 148, 228, 0.12);
  opacity: 0;
  transform: translateY(-10px);
  transition: opacity 0.3s ease, transform 0.3s ease;
  pointer-events: none;
  z-index: 99;
}

.nav-menu-mobile.is-open {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.mobile-menu-list {
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
}

.mobile-menu-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 24px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 500;
  color: #333;
  line-height: 1;
}

.mobile-menu-item span {
  display: flex;
  align-items: center;
  line-height: 22px;
}

.mobile-menu-item:active,
.mobile-menu-item.is-active {
  background: #6594E4;
  color: #ffffff;
}

.mobile-menu-item:active .menu-item-icon,
.mobile-menu-item:active .menu-item-arrow,
.mobile-menu-item.is-active .menu-item-icon,
.mobile-menu-item.is-active .menu-item-arrow {
  filter: brightness(0) invert(1);
}

.menu-item-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.menu-item-icon {
  width: 22px;
  height: 22px;
  min-width: 22px;
  object-fit: contain;
  flex-shrink: 0;
}

.icon-login {
  margin-left: -4px;
}

.text-login {
  margin-left: 5px;
}

.auth-item {
  color: #6594E4;
  font-weight: 600;
}

.auth-item:active {
  background: #6594E4;
  color: #ffffff;
}

.text-home {
  padding-top: 2px;
}

.menu-item-arrow {
  width: 18px;
  height: 18px;
  opacity: 0.4;
}

.logout-item {
  color: #FF5C5C;
}

.icon-logout {
  filter: invert(47%) sepia(98%) saturate(1000%) hue-rotate(314deg) brightness(105%) contrast(101%);
  width: 26px;
  height: 26px;
  margin-left: -5px;
}

.logout-item:active {
  background: #FF5C5C;
  color: #ffffff;
}

.logout-item:active .icon-logout {
  filter: brightness(0) invert(1);
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
  .mobile-nav-right { display: flex; }
}
</style>
