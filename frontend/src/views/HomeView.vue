<template>
  <div class="home-page">
    <!-- Navigation -->
    <div id="top"></div>
    <Navbar @scroll-to="scrollTo" />

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-badge">
        <img src="@/assets/icons/Sparkles.png" alt="" width="16" height="16" />
        <span>Voice Health Monitoring Platform</span>
      </div>

      <h1 class="hero-title">
        Monitor Your <span class="gradient-voice">Voice</span> <span class="gradient-health">Health</span> In Just 5 Seconds
      </h1>

      <p class="hero-subtitle">
        Detect early signs of vocal strain and fatigue with acoustic analysis. For voice professionals and anyone who cares about their voice.
      </p>

      <button class="btn-cta" @click="goToRecording">
        <img src="@/assets/icons/Microphone.png" alt="" class="btn-cta-mic" />
        Try Voice Test Now!
        <span class="btn-cta-arrow">→</span>
      </button>

      <div class="trust-badges">
        <div class="trust-item">
          <img src="@/assets/icons/Checkmark.png" alt="✓" width="18" height="18" />
          <span>No Audio Stored</span>
        </div>
        <div class="trust-item">
          <img src="@/assets/icons/Checkmark.png" alt="✓" width="18" height="18" />
          <span>8-Second Test</span>
        </div>
        <div class="trust-item">
          <img src="@/assets/icons/Checkmark.png" alt="✓" width="18" height="18" />
          <span>No Sign-Up Required</span>
        </div>
      </div>

      <!-- Steps Cards -->
      <div id="how-it-works" class="steps-grid">
        <!-- Step 1 -->
        <div class="step-card step-card-1">
          <div class="step-left">
            <div class="step-icon-wrapper step-icon-1">
              <img src="@/assets/icons/Microphone1.png" alt="Microphone" width="40" height="40" />
            </div>
            <div class="step-badge step-badge-1">Step 1</div>
          </div>
          <div class="step-right">
            <h3 class="step-title">Record</h3>
            <p class="step-desc">Say "Ahhhh" for 5 seconds</p>
          </div>
        </div>

        <!-- Step 2 -->
        <div class="step-card step-card-2">
          <div class="step-left">
            <div class="step-icon-wrapper step-icon-2">
              <img src="@/assets/icons/Pulse.png" alt="Pulse" width="40" height="40" />
            </div>
            <div class="step-badge step-badge-2">Step 2</div>
          </div>
          <div class="step-right">
            <h3 class="step-title">Analyze</h3>
            <p class="step-desc">Acoustic analysis instantly</p>
          </div>
        </div>

        <!-- Step 3 -->
        <div class="step-card step-card-3">
          <div class="step-left">
            <div class="step-icon-wrapper step-icon-3">
              <img src="@/assets/icons/Bar Chart.png" alt="Bar Chart" width="40" height="40" />
            </div>
            <div class="step-badge step-badge-3">Step 3</div>
          </div>
          <div class="step-right">
            <h3 class="step-title">Get Results</h3>
            <p class="step-desc">Receive health insights & tips</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Why VocaSense Section -->
    <section id="features" class="why-section">
      <h2 class="why-title">Why VocaSense?</h2>
      <p class="why-subtitle">Advanced acoustic technology for voice health monitoring</p>

      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <img src="@/assets/icons/Flash On.png" alt="Lightning" width="28" height="28" />
          </div>
          <h4 class="feature-title">Lightning Fast</h4>
          <p class="feature-desc">Results in 8 seconds</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <img src="@/assets/icons/Brain.png" alt="Brain" width="28" height="28" />
          </div>
          <h4 class="feature-title">Acoustic Analysis</h4>
          <p class="feature-desc">Advanced voice analysis</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <img src="@/assets/icons/Graph.png" alt="Graph" width="28" height="28" />
          </div>
          <h4 class="feature-title">Track Progress</h4>
          <p class="feature-desc">Monitor over time</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <img src="@/assets/icons/Light.png" alt="Light" width="28" height="28" />
          </div>
          <h4 class="feature-title">Personalized Tips</h4>
          <p class="feature-desc">Custom recommendations</p>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-mic-icon">
        <img src="@/assets/icons/Microphone1.png" alt="Microphone" width="44" height="44" />
      </div>
      <h2 class="cta-title">Start Monitoring Your Voice<br class="br-mobile" /> Health Today</h2>
      <p class="cta-subtitle">Detect early warning signs and protect your voice before it's too late</p>
      <button class="btn-cta" @click="goToRecording">
        <img src="@/assets/icons/Microphone.png" alt="" class="btn-cta-mic" />
        Try Voice Test Now!
        <span class="btn-cta-arrow">→</span>
      </button>
      <div class="cta-trust">
        <div class="cta-trust-item">
          <img src="@/assets/icons/Clock.png" alt="" width="16" height="16" />
          <span>Takes 8 seconds</span>
        </div>
        <div class="cta-trust-item">
          <img src="@/assets/icons/Shield.png" alt="" width="16" height="16" />
          <span>Audio deleted after analysis</span>
        </div>
        <div class="cta-trust-item">
          <img src="@/assets/icons/Checkmark.png" alt="" width="16" height="16" />
          <span>Login to save history</span>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <div class="footer-logo">
            <img src="@/assets/icons/logo.png" alt="VocaSense" class="footer-logo-img" />
          </div>
          <p class="footer-desc">
            Voice health monitoring platform for everyone who cares<br />
            about their voice health and vocal wellness.
          </p>
          <p class="footer-tagline">Early voice health screening and awareness platform</p>
        </div>
        <div class="footer-links">
          <div class="footer-col">
            <h5 class="footer-col-title">Product</h5>
            <a href="#features" class="footer-link" @click.prevent="scrollTo('features')">Features</a>
            <a href="#how-it-works" class="footer-link" @click.prevent="scrollTo('how-it-works')">How it Works</a>
          </div>
          <div class="footer-col">
            <h5 class="footer-col-title">Company</h5>
            <a href="#" class="footer-link">About</a>
            <a href="#" class="footer-link">Contact</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2026 VocaSense. All rights reserved.</span>
        <span>
          This platform provides preliminary voice health insights and does not replace professional
          medical diagnosis.
        </span>
      </div>
    </footer>
  </div>

  <!-- Toast Notification -->
  <transition name="toast">
    <div v-if="toastShow" class="toast-logout">
      <div class="toast-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
      </div>
      <span class="toast-message">Log out complete</span>
      <button class="toast-close" @click="toastShow = false">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Navbar from '@/components/NavBar.vue'

const router = useRouter()
const route = useRoute()
const toastShow = ref(false)

const checkLoggedOut = () => {
  if (route.query.loggedOut === 'true') {
    toastShow.value = true
    setTimeout(() => { toastShow.value = false }, 3000)
    router.replace('/')
  }
}

onMounted(checkLoggedOut)
watch(() => route.query.loggedOut, checkLoggedOut)

const goToRecording = () => router.push('/recording')

const scrollTo = (id) => {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

.toast-logout {
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
  background: #fff1f2;
  color: #9f1239;
  border: 1px solid #fecdd3;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
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

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.home-page {
  font-family: 'Poppins', sans-serif;
  min-height: 100vh;
  background: #fff;
}

.br-mobile {
  display: none;
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

/* ── Hero Section ── */
.hero-section {
  background: linear-gradient(180deg, #EEF2FF 0%, #E8EEFF 50%, #EFF3FF 100%);
  padding: 40px 24px 80px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 30px;
  border: 1px solid rgba(0, 0, 0, 0.11);
  background: #FFF;
  box-shadow: 0 4px 4px 0 rgba(0, 0, 0, 0.10);
  font-size: 13px;
  font-weight: 600;
  color: #6D96DE;
  margin-bottom: 24px;
}

.hero-title {
  font-family: 'Poppins', sans-serif;
  font-size: 2.5rem;
  font-style: normal;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.5px;
  color: #1a1a2e;
  margin-bottom: 20px;
}

.gradient-voice {
  background: var(--header-1, linear-gradient(90deg, #75A5F7 0%, #6594E4 100%));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.gradient-health {
  background: var(--header-2, linear-gradient(90deg, #78AAFF 0%, #5C7BAF 100%));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  text-align: center;
  line-height: 1.7;
  max-width: 700px;
  margin-bottom: 32px;
}

.btn-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 20px 50px;
  background: linear-gradient(102deg, #95B9F7 8.63%, #6594E4 92.33%);
  color: white;
  border: none;
  border-radius: 50px;
  font-family: 'Poppins', sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  margin-bottom: 24px;
}

.btn-cta:hover {
  opacity: 0.88;
}

.btn-cta:active {
  transform: scale(0.98);
}

.btn-cta-mic {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.btn-cta-arrow {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  line-height: 1;
  transform: translateY(-1px);
}

.trust-badges {
  display: flex;
  align-items: center;
  gap: 40px;
  margin-bottom: 48px;
  flex-wrap: wrap;
  justify-content: center;
}

.trust-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

/* ── Steps Grid ── */
#how-it-works {
  scroll-margin-top: 70px;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 900px;
  width: 100%;
}

.step-card {
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.11);
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.13);
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
}

.step-left,
.step-right {
  display: contents;
}

.step-card-1 {
  background: var(--card-1, linear-gradient(133deg, #FFF 6.83%, #F4F7FF 69.72%, #D7E3FF 102.95%));
}

.step-card-2 {
  background: var(--card-2--1, linear-gradient(133deg, #FFF 6.83%, #F4F7FF 69.72%, #DAE0FF 102.95%));
}

.step-card-3 {
  background: var(--Card3, linear-gradient(133deg, #FFF 6.83%, #EEFAFF 69.72%));
}

.step-icon-wrapper {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.14);
}

.step-icon-1 {
  background: linear-gradient(137deg, #B47AEF 6.18%, #95B9F7 94.01%);
}

.step-icon-2 {
  background: linear-gradient(137deg, #5F8FE3 6.18%, #95B9F7 94.01%);
}

.step-icon-3 {
  background: linear-gradient(137deg, #6FBDDC 6.18%, #9BE2E8 94.01%);
}

.step-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.step-badge-1 {
  background: #C3C2FB;
  color: #6649B6;
}

.step-badge-2 {
  background: rgba(149, 185, 247, 0.29);
  color: #5778B2;
}

.step-badge-3 {
  border-radius: 30px;
  background: rgba(179, 226, 228, 0.61);
  color: #4A7A93;
}

.step-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
}

.step-desc {
  font-size: 13px;
  font-weight: 500;
  color: #777;
}

/* ── Why VocaSense Section ── */
.why-section {
  background: #fff;
  padding: 64px 24px;
  text-align: center;
}

.why-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.why-subtitle {
  font-size: 14px;
  font-weight: 500;
  color: #888;
  margin-bottom: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 1fr;
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.feature-card {
  border-radius: 16px;
  border: 1px solid rgba(101, 148, 228, 0.15);
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
  min-width: 0;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-card:nth-child(1) .feature-icon {
  background: var(--card-1-detail, linear-gradient(133deg, #8AB7FF 13.11%, #DDEAFF 100%));
}

.feature-card:nth-child(2) .feature-icon {
  background: var(--Card-2-detail, linear-gradient(133deg, #6DA5FF 13.11%, #B8D3FF 100%));
  box-shadow: 0 2px 11.2px 0 rgba(0, 0, 0, 0.12);
}

.feature-card:nth-child(3) .feature-icon {
  background: var(--card-detail-3, linear-gradient(133deg, #80CCE6 13.11%, #CBDDFF 100%));
}

.feature-card:nth-child(4) .feature-icon {
  background: var(--card4-detail, linear-gradient(133deg, #ACB7FC 13.11%, #E8E7FF 100%));
  box-shadow: 0 2px 11.2px 0 rgba(0, 0, 0, 0.12);
}

.feature-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
}

.feature-desc {
  font-size: 12px;
  font-weight: 500;
  color: #888;
}

/* ── CTA Section ── */
.cta-section {
  background: linear-gradient(180deg, #EEF2FF 0%, #E8EEFF 100%);
  padding: 64px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cta-mic-icon {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: linear-gradient(137deg, #B47AEF 6.18%, #95B9F7 94.01%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.cta-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  white-space: nowrap;
  margin-bottom: 12px;
  line-height: 1.4;
}

.cta-subtitle {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  margin-bottom: 32px;
  max-width: 360px;
  text-align: center;
  line-height: 1.7;
}

.cta-trust {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
  justify-content: center;
}

.cta-trust-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

/* ── Footer ── */
.footer {
  background: #fff;
  padding: 48px 40px 24px;
}

.footer-content {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  gap: 60px;
  margin-bottom: 32px;
}

.footer-brand {
  flex: 1;
  max-width: 400px;
}

.footer-logo {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.footer-logo-img {
  height: 52px;
  width: auto;
}

.footer-desc {
  font-size: 13px;
  font-weight: 500;
  color: #555;
  line-height: 1.7;
  margin-bottom: 8px;
}

.footer-tagline {
  font-size: 12px;
  color: #888;
  white-space: nowrap;
}

.footer-links {
  display: flex;
  gap: 48px;
  margin-left: auto;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-col-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.footer-link {
  font-size: 13px;
  color: #555;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #6594E4;
}

.footer-bottom {
  max-width: 1100px;
  margin: 0 auto;
  padding-top: 20px;
  border-top: 1px solid rgba(137, 137, 137, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #888;
  flex-wrap: wrap;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .footer {
    padding: 24px 20px;
    border-top: 1px solid rgba(101, 148, 228, 0.12);
  }

  .footer-content {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
    gap: 24px;
    margin-bottom: 20px;
  }

  .footer-brand {
    max-width: 100%;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .footer-logo {
    justify-content: flex-start;
    margin-bottom: 8px;
  }

  .footer-logo-img {
    height: 44px;
  }

  .footer-desc {
    margin-bottom: 6px;
  }

  .footer-tagline {
    white-space: normal;
  }


  .footer-links {
    margin-left: 0;
    display: flex;
    width: 100%;
    gap: 0;
  }

  .footer-links .footer-col {
    flex: 1;
    align-items: flex-start;
    text-align: left;
  }

  .footer-bottom {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 8px;
    padding-top: 16px;
    width: 100%;
  }

  .nav-links {
    display: none;
  }

  .btn-login {
    margin-left: auto;
  }

  .hero-section {
    padding-top: 32px;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-subtitle {
    font-size: 13px;
    max-width: 440px;
    color: #666;
  }

  .cta-title {
    font-size: 22px;
    white-space: normal;
  }

  .br-mobile {
    display: inline;
  }

  .cta-subtitle {
    max-width: 270px;
  }

  .steps-grid {
    grid-template-columns: 1fr;
    max-width: 100%;
  }

  .step-card {
    flex-direction: row;
    align-items: center;
    text-align: left;
    gap: 20px;
    padding: 20px 24px;
  }

  .step-left {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .step-right {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-content {
    flex-direction: column;
    gap: 32px;
  }

}

@media (max-width: 480px) {
  .navbar {
    padding: 0 20px;
  }

  .trust-badges {
    gap: 16px;
    justify-content: center;
  }

  .cta-trust {
    gap: 16px;
    justify-content: center;
  }

  .features-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
