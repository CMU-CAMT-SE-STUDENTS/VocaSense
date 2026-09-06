import { createRouter, createWebHistory } from 'vue-router'
import { supabase } from '@/utils/supabase'
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
      component: HistoryView,
      meta: { requiresAuth: true }
    },
    {
      path: '/result',
      name: 'result',
      component: ResultView
    }
  ]
})

// UC-12: History is a member-only page — the nav only links to it once
// logged in, but this guard also blocks typing /history in directly.
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const { data } = await supabase.auth.getSession()
  if (!data.session) return { path: '/login' }
  return true
})

export default router