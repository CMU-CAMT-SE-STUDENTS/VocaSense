import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SignUpView from '../views/SignUp.vue'
import LoginView from '../views/LoginView.vue'
import ForgotPassword from '../views/ForgotPassword.vue'
import ResetPassword from '../views/ResetPassword.vue'
import RecordingView from '../views/RecordingView.vue'
import AnalysisView from '../views/AnalysisView.vue'
import ImproveResultView from '../views/ImproveResultView.vue'
import HistoryView from '../views/HistoryView.vue'
import ResultView from '../views/ResultView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/recording',
      name: 'recording',
      component: RecordingView
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignUpView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPassword
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPassword
    },
    {
      path: '/analysis',
      name: 'analysis',
      component: AnalysisView
    },
    {
      path: '/improve-result',
      name: 'improve-result',
      component: ImproveResultView
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView
    },
    {
      path: '/result',
      name: 'result',
      component: ResultView
    }
  ]
})

// UC-16 precondition: "About This Recording" answers a specific recording,
// so it requires one to exist. Scoped to ?form=assessment only — the bare
// page and ?form=baseline ("Set Your Baseline") stay reachable with no
// recording at all, since a member can set their baseline any time.
router.beforeEach((to) => {
  if (to.path === '/improve-result' && to.query.form === 'assessment') {
    if (!sessionStorage.getItem('vocasense:lastVoiceAnalysisAt')) {
      return { path: '/recording', query: { reason: 'needs-recording' } }
    }
  }
})

export default router