<template>
  <div class="assess-page">
    <!-- Loading auth state -->
    <div v-if="loading" class="loading-state"></div>

    <!-- Base page: always visible underneath, the popup opens on top of this -->
    <template v-else>
      <div class="page-topbar">
        <button class="btn-back" @click="router.push('/result')">
          <span class="back-arrow">&larr;</span> Back To Result Dashboard
        </button>
      </div>

      <div class="page-inner" :class="{ 'page-inner-wide': isMember }">
      <h1 class="assess-title">Voice Self-Assessment</h1>
      <p class="assess-subtitle">
        <template v-if="isMember">Two short forms. Both make your voice analysis more accurate.</template>
        <template v-else>Seven quick questions &mdash; about 1 minute.</template>
      </p>

      <!-- Guest: single card, the 7-section wizard below -->
      <div v-if="!isMember" class="card intro-card">
        <div class="card-head">
          <div class="icon-wrap sm"><img src="@/assets/icons/test_passed.png" alt="" class="header-icon-img" /></div>
          <div>
            <strong>About This Recording</strong>
            <span>Recording from {{ recordingLabel }}</span>
          </div>
        </div>

        <h3 class="why-title">Why these questions matter</h3>
        <ul class="why-list">
          <li>
            <span class="why-icon"><InsightIcon kind="pulse" /></span>
            We can tell an off day from a real change
          </li>
          <li>
            <span class="why-icon"><InsightIcon kind="scale" /></span>
            We compare your recordings fairly
          </li>
          <li>
            <span class="why-icon"><InsightIcon kind="trend" /></span>
            You see what affects your voice over time
          </li>
        </ul>

        <button class="btn-primary" type="button" @click="openAssessment">Start assessment</button>
        <p class="intro-footnote">We'll update your result as soon as you're done.</p>
      </div>

      <!-- Member: two entry points — the same per-recording wizard the guest
           uses, plus the one-time baseline form -->
      <div v-else class="member-card-grid">
        <div class="card member-task-card">
          <div class="task-card-head">
            <div class="icon-wrap md"><img src="@/assets/icons/test_passed.png" alt="" class="task-icon-img" /></div>
            <span v-if="assessmentDoneForRecording" class="task-badge task-badge-done">
              <span aria-hidden="true">&#10003;</span> Answered
            </span>
            <span v-else class="task-badge task-badge-accent">Every recording &middot; 1 min</span>
          </div>
          <h3 class="task-title">About This Recording</h3>
          <p class="task-desc">A rough morning could be bad sleep, or something more. This tells us which.</p>
          <button class="btn-primary sm" type="button" @click="openAssessment">
            <template v-if="assessmentDoneForRecording">Edit your answers <span aria-hidden="true">&rarr;</span></template>
            <template v-else>Answer for this recording <span aria-hidden="true">&rarr;</span></template>
          </button>
        </div>

        <div class="card member-task-card">
          <div class="task-card-head">
            <div class="icon-wrap md icon-wrap-muted"><img src="@/assets/icons/user.png" alt="" class="task-icon-img" /></div>
            <span v-if="hasBaseline" class="task-badge task-badge-done">
              <span aria-hidden="true">&#10003;</span> Set
            </span>
            <span v-else class="task-badge">Once &middot; 3 min</span>
          </div>
          <h3 class="task-title">Set Your Baseline</h3>
          <p class="task-desc">What counts as a normal voice differs per person. This sets yours.</p>
          <button class="btn-outline" type="button" @click="openBaseline">
            <template v-if="hasBaseline">Edit your baseline <span aria-hidden="true">&rarr;</span></template>
            <template v-else>Set your baseline <span aria-hidden="true">&rarr;</span></template>
          </button>
        </div>
      </div>
      </div>
    </template>

    <!-- Popup: question wizard, opens on top of the page above -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop">
        <div class="modal-panel" role="dialog" aria-modal="true" aria-label="Voice self-assessment questions">
          <button class="modal-close" type="button" @click="requestClose" aria-label="Close">
            <CloseIcon />
          </button>

          <div class="card-head">
            <div class="icon-wrap sm"><img src="@/assets/icons/test_passed.png" alt="" class="header-icon-img" /></div>
            <div>
              <strong>About This Recording</strong>
              <span>Recording from {{ recordingLabel }}</span>
            </div>
          </div>

          <Transition :name="direction > 0 ? 'slide-forward' : 'slide-back'" mode="out-in">
            <div :key="step" class="step-panel">
              <!-- complete -->
              <template v-if="step === 'complete'">
                <div class="progress-row">
                  <span class="section-pill">Section {{ sections.length }} of {{ sections.length }}</span>
                  <span class="section-name">Complete</span>
                </div>
                <div class="progress-track"><div class="progress-fill" style="width: 100%"></div></div>

                <div class="complete-body">
                  <div class="icon-wrap lg complete-icon-wrap">
                    <img src="@/assets/icons/test_passed.png" alt="" class="complete-icon-img" />
                  </div>
                  <h2>Thank you for your answers!</h2>
                  <p>Your data helps us improve voice health care.</p>

                  <div class="privacy-box">
                    <div v-for="line in privacyLines" :key="line" class="privacy-line">
                      <CheckIcon /> {{ line }}
                    </div>
                  </div>

                  <button class="btn-primary" type="button" @click="router.push('/result')">
                    See my updated result <span aria-hidden="true">&rarr;</span>
                  </button>
                  <button
                    v-if="isMember && !hasBaseline"
                    class="btn-outline complete-secondary-btn"
                    type="button"
                    @click="openBaseline"
                  >
                    Set your baseline for better accuracy <span aria-hidden="true">&rarr;</span>
                  </button>
                  <div class="complete-links">
                    <button type="button" class="link-plain" @click="step = 1">Edit my answers</button>
                  </div>
                </div>
              </template>

              <!-- section N -->
              <template v-else>
                <div class="progress-row">
                  <span class="section-pill">Section {{ step }} of {{ sections.length }}</span>
                  <span class="section-name">{{ currentSection.title }}</span>
                </div>
                <div class="progress-track"><div class="progress-fill" :style="{ width: (step / sections.length) * 100 + '%' }"></div></div>

                <div class="questions" @change="sectionTouched = true" @input="sectionTouched = true">
                  <div v-for="q in currentSection.questions" :key="q.key" class="question-block" :class="{ incomplete: sectionTouched && !isAnswered(q) }">
                    <p class="question-label">
                      {{ q.label }}
                      <span v-if="sectionTouched && !isAnswered(q)" class="required-badge">Required</span>
                    </p>
                    <p v-if="q.sublabel" class="question-sublabel">{{ q.sublabel }}</p>
                    <p v-if="q.hint" class="question-hint">{{ q.hint }}</p>

                    <!-- radio -->
                    <div v-if="q.type === 'radio'" class="option-list">
                      <label v-for="opt in q.options" :key="opt.value" class="option-row" :class="{ selected: answers[q.key] === opt.value }">
                        <input type="radio" :name="q.key" :value="opt.value" v-model="answers[q.key]" />
                        <span class="radio-dot"></span>
                        {{ opt.label }}
                      </label>
                    </div>

                    <!-- number, with a tappable stepper since native spin buttons are
                         unreliable on mobile (iOS Safari hides them entirely) -->
                    <div v-else-if="q.type === 'number'" class="number-stepper">
                      <button
                        type="button"
                        class="stepper-btn"
                        :disabled="Number(answers[q.key]) <= 0"
                        aria-label="Decrease"
                        @click="stepNumber(q.key, -1, q.max)"
                      >&minus;</button>
                      <input
                        type="number"
                        min="0"
                        :max="q.max"
                        inputmode="numeric"
                        class="number-input"
                        :placeholder="q.placeholder"
                        :value="answers[q.key]"
                        @input="sanitizeNumberInput(q.key, $event, q.max)"
                      />
                      <button
                        type="button"
                        class="stepper-btn"
                        :disabled="q.max != null && Number(answers[q.key]) >= q.max"
                        aria-label="Increase"
                        @click="stepNumber(q.key, 1, q.max)"
                      >+</button>
                    </div>

                    <!-- checkbox group -->
                    <div v-else-if="q.type === 'checkbox-group'" class="option-list">
                      <label
                        v-for="opt in q.options"
                        :key="opt"
                        class="option-row"
                        :class="{ selected: answers[q.key].includes(opt) }"
                      >
                        <input
                          type="checkbox"
                          :checked="answers[q.key].includes(opt)"
                          @change="toggleCheckbox(q.key, opt, q.exclusiveOption)"
                        />
                        <span class="checkbox-box">
                          <svg viewBox="0 0 24 24" fill="none" class="check-svg"><path d="m5 12.5 4.5 4.5L19 7" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        </span>
                        {{ opt }}
                      </label>
                    </div>

                    <!-- severity table -->
                    <div v-else-if="q.type === 'severity-table'" class="severity-table-wrap">
                      <table class="severity-table">
                        <thead>
                          <tr>
                            <th class="symptom-col">Symptom</th>
                            <th v-for="n in 6" :key="n">{{ n - 1 }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in q.items" :key="item">
                            <td class="symptom-col">{{ item }}</td>
                            <td v-for="n in 6" :key="n">
                              <input
                                type="radio"
                                :name="q.key + '-' + item"
                                :value="n - 1"
                                v-model="answers[q.key][item]"
                              />
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                <div class="nav-row">
                  <button class="btn-outline" type="button" @click="goBack">
                    <span aria-hidden="true">&larr;</span> Back
                  </button>
                  <button v-if="step < sections.length" class="btn-primary sm" type="button" :disabled="!isSectionComplete" @click="step++">
                    Next <span aria-hidden="true">&rarr;</span>
                  </button>
                  <button v-else class="btn-primary sm" type="button" :disabled="!isSectionComplete" @click="submitAssessment">Submit</button>
                </div>
              </template>
            </div>
          </Transition>
        </div>
      </div>
    </Teleport>

    <!-- Popup: one-time baseline wizard -->
    <Teleport to="body">
      <div v-if="baselineOpen" class="modal-backdrop">
        <div class="modal-panel" role="dialog" aria-modal="true" aria-label="Set your baseline questions">
          <button class="modal-close" type="button" @click="requestClose" aria-label="Close">
            <CloseIcon />
          </button>

          <div class="card-head">
            <div class="icon-wrap sm icon-wrap-muted"><img src="@/assets/icons/user.png" alt="" class="header-icon-img" /></div>
            <div>
              <strong>Set Your Baseline</strong>
              <span>One-time &middot; about 3 minutes</span>
            </div>
          </div>

          <Transition :name="baselineDirection > 0 ? 'slide-forward' : 'slide-back'" mode="out-in">
            <div :key="baselineStep" class="step-panel">
              <!-- complete -->
              <template v-if="baselineStep === 'complete'">
                <div class="progress-row">
                  <span class="section-pill">Section {{ visibleBaselineSections.length }} of {{ visibleBaselineSections.length }}</span>
                  <span class="section-name">Complete</span>
                </div>
                <div class="progress-track"><div class="progress-fill" style="width: 100%"></div></div>

                <div class="complete-body">
                  <div class="icon-wrap lg complete-icon-wrap icon-wrap-muted">
                    <img src="@/assets/icons/user.png" alt="" class="complete-icon-img" />
                  </div>
                  <h2>Your baseline is set!</h2>
                  <p>You won't need to fill this in again.</p>

                  <div class="privacy-box">
                    <div v-for="line in baselinePrivacyLines" :key="line" class="privacy-line">
                      <CheckIcon /> {{ line }}
                    </div>
                  </div>

                  <button class="btn-primary" type="button" @click="openAssessment">
                    Next: about this recording <span aria-hidden="true">&rarr;</span>
                  </button>
                  <div class="complete-links">
                    <button type="button" class="link-plain" @click="baselineStep = 1">Edit my answers</button>
                    <button type="button" class="link-plain link-muted" @click="closeForm">Do this later</button>
                  </div>
                </div>
              </template>

              <!-- section N -->
              <template v-else>
                <div class="progress-row">
                  <span class="section-pill">Section {{ baselineStep }} of {{ visibleBaselineSections.length }}</span>
                  <span class="section-name">{{ currentBaselineSection.title }}</span>
                </div>
                <div class="progress-track"><div class="progress-fill" :style="{ width: (baselineStep / visibleBaselineSections.length) * 100 + '%' }"></div></div>

                <div class="questions" @change="baselineSectionTouched = true" @input="baselineSectionTouched = true">
                  <div v-for="q in currentBaselineQuestions" :key="q.key" class="question-block" :class="{ incomplete: baselineSectionTouched && !isBaselineAnswered(q) }">
                    <p class="question-label">
                      {{ q.label }}
                      <span v-if="baselineSectionTouched && !isBaselineAnswered(q)" class="required-badge">Required</span>
                    </p>
                    <p v-if="q.hint" class="question-hint">{{ q.hint }}</p>

                    <!-- radio -->
                    <div v-if="q.type === 'radio'" class="option-list">
                      <label v-for="opt in q.options" :key="opt.value" class="option-row" :class="{ selected: baselineAnswers[q.key] === opt.value }">
                        <input type="radio" :name="q.key" :value="opt.value" v-model="baselineAnswers[q.key]" />
                        <span class="radio-dot"></span>
                        {{ opt.label }}
                      </label>
                    </div>

                    <!-- text -->
                    <input
                      v-else-if="q.type === 'text'"
                      type="text"
                      class="number-input text-input"
                      :placeholder="q.placeholder"
                      v-model="baselineAnswers[q.key]"
                    />

                    <!-- number, with a tappable stepper -->
                    <div v-else-if="q.type === 'number'" class="number-stepper">
                      <button
                        type="button"
                        class="stepper-btn"
                        :disabled="Number(baselineAnswers[q.key]) <= 0"
                        aria-label="Decrease"
                        @click="stepBaselineNumber(q.key, -1, q.max)"
                      >&minus;</button>
                      <input
                        type="number"
                        min="0"
                        :max="q.max"
                        inputmode="numeric"
                        class="number-input"
                        :placeholder="q.placeholder"
                        :value="baselineAnswers[q.key]"
                        @input="sanitizeBaselineNumberInput(q.key, $event, q.max)"
                      />
                      <button
                        type="button"
                        class="stepper-btn"
                        :disabled="q.max != null && Number(baselineAnswers[q.key]) >= q.max"
                        aria-label="Increase"
                        @click="stepBaselineNumber(q.key, 1, q.max)"
                      >+</button>
                    </div>

                    <!-- checkbox group, optionally with a trailing free-text "Other" field -->
                    <div v-else-if="q.type === 'checkbox-group'">
                      <div class="option-list">
                        <label
                          v-for="opt in q.options"
                          :key="opt"
                          class="option-row"
                          :class="{ selected: baselineAnswers[q.key].includes(opt) }"
                        >
                          <input
                            type="checkbox"
                            :checked="baselineAnswers[q.key].includes(opt)"
                            @change="toggleBaselineCheckbox(q.key, opt, q.exclusiveOption)"
                          />
                          <span class="checkbox-box">
                            <svg viewBox="0 0 24 24" fill="none" class="check-svg"><path d="m5 12.5 4.5 4.5L19 7" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                          </span>
                          {{ opt }}
                        </label>
                      </div>
                      <input
                        v-if="q.otherKey"
                        type="text"
                        class="number-input text-input other-input"
                        placeholder="Other:"
                        v-model="baselineAnswers[q.otherKey]"
                      />
                    </div>
                  </div>
                </div>

                <div class="nav-row">
                  <button class="btn-outline" type="button" @click="baselineGoBack">
                    <span aria-hidden="true">&larr;</span> Back
                  </button>
                  <button v-if="baselineStep < visibleBaselineSections.length" class="btn-primary sm" type="button" :disabled="!isBaselineSectionComplete" @click="baselineNext">
                    Next <span aria-hidden="true">&rarr;</span>
                  </button>
                  <button v-else class="btn-primary sm" type="button" :disabled="!isBaselineSectionComplete" @click="baselineNext">Submit</button>
                </div>
              </template>
            </div>
          </Transition>
        </div>
      </div>
    </Teleport>

    <!-- Close confirmation: only shown when there's actually progress to lose -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showCloseConfirm" class="modal-overlay" @click="cancelClose">
          <div class="modal-card" role="alertdialog" aria-modal="true" aria-label="Close assessment?" @click.stop>
            <img src="@/assets/icons/notcomplete.png" alt="" class="modal-leave-icon" />
            <h3 class="modal-title">Close this assessment?</h3>
            <p class="modal-desc">Your answers won't be saved &mdash; you'll need to start over next time.</p>
            <button class="modal-btn modal-btn-red" type="button" @click="confirmClose">Close &amp; Discard</button>
            <button class="modal-dismiss" type="button" @click="cancelClose">Keep Answering</button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const isMember = ref(false)
const step = ref(1) // 1..7 | 'complete', only meaningful while the popup is open
const direction = ref(1) // 1 = moving forward (Next/Submit), -1 = moving back

// No backend endpoint exists yet for either questionnaire, so submitted
// answers are saved to localStorage instead — enough to (a) know a form was
// already completed and (b) let "Edit my answers" actually show what was
// submitted, without waiting on the API.
const LS_BASELINE_KEY = 'vocasense:baselineAnswers'
function assessmentStorageKey(key) { return `vocasense:assessmentAnswers:${key}` }
function loadJSON(key) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
function saveJSON(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* storage unavailable, e.g. private mode */ }
}

const hasBaseline = ref(false)
const assessmentDoneForRecording = ref(false)

watch(step, (next, prev) => {
  const toNum = (v) => (v === 'complete' ? 8 : v)
  direction.value = toNum(next) >= toNum(prev) ? 1 : -1
})

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  isMember.value = !!data.session?.user

  const savedBaseline = loadJSON(LS_BASELINE_KEY)
  if (savedBaseline) {
    Object.assign(baselineAnswers, savedBaseline)
    hasBaseline.value = true
  }
  const savedAssessment = loadJSON(assessmentStorageKey(recordingKey.value))
  if (savedAssessment) {
    Object.assign(answers, savedAssessment)
    assessmentDoneForRecording.value = true
  }

  loading.value = false
})

// The popup's open/closed state lives in the URL (/improve-result/assessment)
// so back/refresh keeps it open instead of dropping the user onto a blank page.
// Driven by a query param (not a separate route record) so the component
// never unmounts/remounts when the popup opens — that remount was the cause
// of the choppy transition and the font flashing to a fallback.
// Both guest and member can open this wizard now (member's "About This
// Recording" card links to the same per-recording form as the guest one).
// A single query param picks which of the two wizards is open, so they're
// mutually exclusive by construction and both survive back/refresh.
const modalOpen = computed(() => route.query.form === 'assessment')
const baselineOpen = computed(() => route.query.form === 'baseline')

function openAssessment() {
  router.push({ path: '/improve-result', query: { form: 'assessment' } })
}

function openBaseline() {
  router.push({ path: '/improve-result', query: { form: 'baseline' } })
}

function closeForm() {
  router.push({ path: '/improve-result' })
}

const showCloseConfirm = ref(false)

// In-progress answers only live in memory until Submit writes them to
// localStorage — closing mid-way genuinely loses whatever's been changed
// since the last submit, so only ask for confirmation when there's
// something un-submitted to lose.
function hasProgressIn(answersObj) {
  return Object.values(answersObj).some((v) => {
    if (Array.isArray(v)) return v.length > 0
    if (v && typeof v === 'object') return Object.values(v).some((x) => x !== null && x !== '')
    return v !== '' && v !== null
  })
}

function requestClose() {
  // Already submitted this popup session (step === 'complete') — the
  // answers on screen are exactly what's saved, so there's nothing to warn about.
  if (modalOpen.value && step.value === 'complete') return closeForm()
  if (baselineOpen.value && baselineStep.value === 'complete') return closeForm()

  const activeAnswers = modalOpen.value ? answers : baselineOpen.value ? baselineAnswers : null
  if (activeAnswers && hasProgressIn(activeAnswers)) {
    showCloseConfirm.value = true
  } else {
    closeForm()
  }
}

function cancelClose() {
  showCloseConfirm.value = false
}

function confirmClose() {
  showCloseConfirm.value = false
  // Discarding restores the last submitted snapshot (if any) rather than a
  // blank form — "discard changes" shouldn't also erase an earlier submit.
  if (modalOpen.value) {
    Object.assign(answers, loadJSON(assessmentStorageKey(recordingKey.value)) || createInitialAnswers())
  } else if (baselineOpen.value) {
    Object.assign(baselineAnswers, loadJSON(LS_BASELINE_KEY) || createInitialBaselineAnswers())
  }
  closeForm()
}

watch([modalOpen, baselineOpen], ([assessmentIsOpen, baselineIsOpen]) => {
  document.body.style.overflow = (assessmentIsOpen || baselineIsOpen) ? 'hidden' : ''
  if (assessmentIsOpen) step.value = 1
  if (baselineIsOpen) baselineStep.value = 1
})

function handleKeydown(e) {
  if (e.key !== 'Escape') return
  if (showCloseConfirm.value) cancelClose()
  else if (modalOpen.value || baselineOpen.value) requestClose()
}
onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})

// Identifies "this recording" for the per-recording assessment — stable
// across popup open/close so re-opening after Submit shows the same saved
// answers instead of a blank form.
const recordingKey = computed(() => sessionStorage.getItem('vocasense:lastVoiceAnalysisAt') || 'unknown')

const recordingLabel = computed(() => {
  const date = recordingKey.value !== 'unknown' ? new Date(recordingKey.value) : new Date()
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) +
    ', ' + date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
})

function yesNo(key, label) {
  return { type: 'radio', key, label, options: [{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }] }
}

const sections = [
  {
    title: 'When You Recorded',
    questions: [
      {
        type: 'radio',
        key: 'recordingType',
        label: 'Type of recording',
        options: [
          { value: 'before', label: 'Before heavy voice use' },
          { value: 'after', label: 'After heavy voice use' },
          { value: 'daily', label: 'Daily routine recording' }
        ]
      }
    ]
  },
  {
    title: 'Current Symptoms',
    questions: [
      {
        type: 'severity-table',
        key: 'symptoms',
        label: 'Rate the severity of your current symptoms',
        sublabel: '0 = no symptoms | 5 = very severe',
        items: [
          'Hoarseness', 'Voice breaks / tremor', 'Sore throat', 'Dry throat',
          'Fatigue after speaking', 'Voice loss or weakening', 'Cough', 'Throat clearing',
          'Sticky phlegm', 'Lump-in-throat feeling', 'Difficulty swallowing',
          'Burning throat or chest', 'Sour or bitter taste'
        ]
      }
    ]
  },
  {
    title: 'Behavior within 2 hours before recording',
    questions: [
      yesNo('caffeine', 'Within 2 hours, did you drink coffee or caffeinated beverages?'),
      yesNo('soda', 'Within 2 hours, did you drink soda?'),
      yesNo('spicyFood', 'Within 2 hours, did you eat spicy food?'),
      yesNo('friedFood', 'Within 2 hours, did you eat fried or fatty food?'),
      yesNo('irregularMeal', 'Within 2 hours, did you eat at an irregular time?'),
      yesNo('smoked', 'Within 2 hours, did you smoke?')
    ]
  },
  {
    title: 'Behavior within 6 hours before recording',
    questions: [
      yesNo('alcohol', 'Within 6 hours, did you drink alcohol?')
    ]
  },
  {
    title: 'Water Intake',
    questions: [
      { type: 'number', key: 'glassesToday', label: 'How many glasses of water have you had today?', placeholder: 'Enter number of glasses', max: 20 },
      {
        type: 'radio',
        key: 'recentWater',
        label: 'Within 15 minutes before recording, did you drink or sip water?',
        options: [
          { value: 'none', label: 'Did not drink' },
          { value: 'sips', label: '1-2 sips' },
          { value: 'less_half', label: 'Less than half a glass' },
          { value: 'half', label: 'About half a glass' },
          { value: 'one', label: 'About 1 glass' },
          { value: 'more_than_one', label: 'More than 1 glass' }
        ]
      }
    ]
  },
  {
    title: 'Sleep',
    questions: [
      { type: 'number', key: 'hoursSlept', label: 'How many hours did you sleep last night?', placeholder: 'Enter number of hours', max: 24 }
    ]
  },
  {
    title: 'Voice Usage',
    questions: [
      {
        type: 'checkbox-group',
        key: 'regularVoiceUse',
        label: 'Which of these do you do regularly?',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: [
          'Speak loudly', 'Speak quickly', 'Speak continuously for long periods', 'Mimic voices',
          'Cut off speech abruptly', 'Speak in noisy environments', 'Speak curtly', 'Talk a lot',
          'Cough often', 'Clear throat often', 'Sing', 'Talk on the phone for long periods',
          'Strain or tense neck while speaking', 'Shout or yell', 'None of the above'
        ]
      },
      { type: 'number', key: 'continuousMinutes', label: 'How many minutes did you use your voice continuously before recording?', placeholder: 'Enter number of minutes', max: 300 },
      {
        type: 'checkbox-group',
        key: 'environment',
        label: 'Environment before recording',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: ['Noisy', 'Dusty or polluted air', 'In an air-conditioned room', 'None of the above']
      }
    ]
  }
]

const currentSection = computed(() => sections[(typeof step.value === 'number' ? step.value : 1) - 1])

function isAnswered(q) {
  const v = answers[q.key]
  if (q.type === 'checkbox-group') return v.length > 0
  if (q.type === 'severity-table') return q.items.every((item) => v[item] !== null)
  return v !== '' && v !== null && v !== undefined
}

const isSectionComplete = computed(() =>
  typeof step.value !== 'number' || currentSection.value.questions.every(isAnswered)
)

// Required-field hints only appear once the user has started answering this
// section — showing them on a blank, untouched section reads as an error
// before anyone did anything wrong.
const sectionTouched = ref(false)
watch(step, () => { sectionTouched.value = false })

function createInitialAnswers() {
  const initial = {}
  for (const section of sections) {
    for (const q of section.questions) {
      if (q.type === 'checkbox-group') initial[q.key] = []
      else if (q.type === 'severity-table') {
        initial[q.key] = {}
        for (const item of q.items) initial[q.key][item] = null
      } else {
        initial[q.key] = ''
      }
    }
  }
  return initial
}

const answers = reactive(createInitialAnswers())

function toggleCheckboxIn(target, key, option, exclusiveOption) {
  const list = target[key]
  const idx = list.indexOf(option)

  if (option === exclusiveOption) {
    target[key] = idx === -1 ? [exclusiveOption] : []
    return
  }

  if (idx === -1) {
    target[key] = [...list.filter((o) => o !== exclusiveOption), option]
  } else {
    target[key] = list.filter((o) => o !== option)
  }
}

function toggleCheckbox(key, option, exclusiveOption) {
  toggleCheckboxIn(answers, key, option, exclusiveOption)
}

function stepNumberIn(target, key, delta, max) {
  let next = Math.max(0, (Number(target[key]) || 0) + delta)
  if (max != null) next = Math.min(next, max)
  target[key] = String(next)
}

function stepNumber(key, delta, max) {
  stepNumberIn(answers, key, delta, max)
  sectionTouched.value = true
}

// Typed input can't be trusted to stay numeric — IME text entry (e.g. Thai)
// slips past the browser's own type="number" filtering, and a bare `min`/
// `max` attribute only marks the field :invalid without blocking the
// keystroke. Strip anything non-digit and clamp in JS instead.
function sanitizeNumberInputIn(target, key, event, max) {
  let digits = event.target.value.replace(/[^0-9]/g, '')
  if (digits && max != null) digits = String(Math.min(Number(digits), max))
  target[key] = digits
  event.target.value = digits
}

function sanitizeNumberInput(key, event, max) {
  sanitizeNumberInputIn(answers, key, event, max)
  sectionTouched.value = true
}

function goBack() {
  if (step.value > 1) step.value--
  else requestClose()
}

function submitAssessment() {
  saveJSON(assessmentStorageKey(recordingKey.value), answers)
  assessmentDoneForRecording.value = true
  step.value = 'complete'
}

const privacyLines = [
  'Your data is kept confidential',
  'Used only for voice health research',
  'Audio is not stored after analysis'
]

// ═══════════════════════════════════════════════════════════════════
// "Set Your Baseline" — one-time demographic/lifestyle questionnaire.
// Smoking and alcohol each ask a status question, then a follow-up
// section whose questions (and existence) depend on that answer.
// ═══════════════════════════════════════════════════════════════════
const baselineStep = ref(1) // 1..N | 'complete', N depends on branches taken
const baselineDirection = ref(1)

watch(baselineStep, (next, prev) => {
  const toNum = (v) => (v === 'complete' ? 999 : v)
  baselineDirection.value = toNum(next) >= toNum(prev) ? 1 : -1
})

const baselineSections = [
  {
    title: 'General Information',
    questions: [
      {
        type: 'radio',
        key: 'sex',
        label: 'Sex assigned at birth',
        options: [
          { value: 'male', label: 'Male' },
          { value: 'female', label: 'Female' },
          { value: 'prefer_not_say', label: 'Prefer not to say' }
        ]
      },
      { type: 'number', key: 'age', label: 'Age', placeholder: 'Enter your age', max: 120 },
      { type: 'text', key: 'occupation', label: 'Occupation', placeholder: 'Enter your occupation' }
    ]
  },
  {
    title: 'Home Environment',
    questions: [
      {
        type: 'checkbox-group',
        key: 'homeEnvironment',
        label: 'What best describes your home?',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: ['Noisy', 'Dusty or polluted air', 'In an air-conditioned room', 'None of the above']
      }
    ]
  },
  {
    title: 'Work Environment',
    questions: [
      {
        type: 'checkbox-group',
        key: 'workEnvironment',
        label: 'What best describes your workplace or school?',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: ['Noisy', 'Dusty or polluted air', 'In an air-conditioned room', 'None of the above']
      }
    ]
  },
  {
    title: 'Smoking',
    questions: [
      {
        type: 'radio',
        key: 'smokingStatus',
        label: 'Do you smoke regularly?',
        options: [
          { value: 'never', label: 'Never smoked' },
          { value: 'current', label: 'Currently smoking' },
          { value: 'quit', label: 'Quit smoking' }
        ]
      }
    ]
  },
  {
    title: 'Smoking',
    showIf: (a) => a.smokingStatus !== 'never',
    questions: (a) => a.smokingStatus === 'current'
      ? [
          { type: 'number', key: 'cigarettesPerDay', label: 'On average, how many cigarettes do you smoke per day?', placeholder: 'Enter number of cigarettes', max: 200 },
          { type: 'number', key: 'yearsSmoking', label: 'How many years have you been smoking?', placeholder: 'Enter number of years', max: 100 }
        ]
      : [
          { type: 'number', key: 'yearsSinceQuitSmoking', label: 'How many years since you quit smoking?', placeholder: 'Enter number of years', max: 100 }
        ]
  },
  {
    title: 'Alcohol Consumption',
    questions: [
      {
        type: 'radio',
        key: 'alcoholStatus',
        label: 'Do you drink alcohol regularly?',
        options: [
          { value: 'no', label: "Don't drink" },
          { value: 'yes', label: 'Drink' },
          { value: 'quit', label: 'Quit drinking' }
        ]
      }
    ]
  },
  {
    title: 'Alcohol Consumption',
    showIf: (a) => a.alcoholStatus !== 'no',
    questions: (a) => a.alcoholStatus === 'yes'
      ? [
          { type: 'number', key: 'drinksPerWeek', label: 'On average, how many drinks per week?', placeholder: 'Enter number of drinks', max: 100 },
          { type: 'number', key: 'drinksPerDay', label: 'On average, how many drinks per day?', placeholder: 'Enter number of drinks', max: 50 },
          { type: 'number', key: 'yearsDrinking', label: 'How many years have you been drinking?', placeholder: 'Enter number of years', max: 100 }
        ]
      : [
          { type: 'number', key: 'yearsSinceQuitDrinking', label: 'How many years since you quit drinking?', placeholder: 'Enter number of years', max: 100 }
        ]
  },
  {
    title: 'Eating Behavior',
    questions: [
      { type: 'number', key: 'glassesWaterPerDay', label: 'On average, how many glasses of water do you drink per day?', placeholder: 'Enter number of glasses', max: 20 },
      {
        type: 'checkbox-group',
        key: 'eatingHabits',
        label: 'Which of these do you do regularly?',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: [
          'Drink soda regularly', 'Drink coffee or caffeinated beverages regularly', 'Eat spicy food regularly',
          'Eat fried or fatty food regularly', 'Eat at irregular times', 'Eat then lie down within 3-4 hours regularly',
          'None of the above'
        ]
      }
    ]
  },
  {
    title: 'Voice Use Behavior',
    questions: [
      {
        type: 'checkbox-group',
        key: 'regularVoiceUse',
        label: 'Which of these do you do regularly?',
        hint: '(select all that apply)',
        exclusiveOption: 'None of the above',
        options: [
          'Speak loudly', 'Speak quickly', 'Speak continuously for long periods', 'Mimic voices',
          'Cut off speech abruptly', 'Speak in noisy environments', 'Speak curtly', 'Talk a lot',
          'Cough often', 'Clear throat often', 'Sing', 'Talk on the phone for long periods',
          'Strain or tense neck while speaking', 'Shout or yell', 'None of the above'
        ]
      }
    ]
  },
  {
    title: 'Voice Usage at Home',
    questions: [
      { type: 'number', key: 'hoursVoiceHome', label: 'On average, how many hours per day do you use your voice at home?', placeholder: 'Enter number of hours', max: 24 },
      {
        type: 'checkbox-group',
        key: 'reasonsVoiceHome',
        label: 'Main reasons you use your voice at home',
        hint: '(select all that apply)',
        exclusiveOption: 'No special voice use',
        otherKey: 'reasonsVoiceHomeOther',
        options: [
          'Talking with family members', 'Caring for children', 'Caring for elderly', 'Phone or video calls',
          'Online meetings', 'Gaming or streaming', 'Singing', 'Practicing speech/voice',
          'Making content or recording audio', 'No special voice use'
        ]
      }
    ]
  },
  {
    title: 'Voice Usage at Work/School',
    questions: [
      { type: 'number', key: 'hoursVoiceWork', label: 'On average, how many hours per day do you use your voice at work/school?', placeholder: 'Enter number of hours', max: 24 },
      {
        type: 'checkbox-group',
        key: 'reasonsVoiceWork',
        label: 'Main reasons you use your voice at work/school',
        hint: '(select all that apply)',
        otherKey: 'reasonsVoiceWorkOther',
        options: [
          'Teaching', 'Meetings', 'Presenting', 'Answering customer calls', 'Selling products',
          'Talking with customers or clients', 'General conversation', 'Singing', 'Voice acting/dubbing',
          'Live streaming', 'Recording audio or making content', 'Attending class'
        ]
      }
    ]
  }
]

function createInitialBaselineAnswers() {
  return {
    sex: '', age: '', occupation: '',
    homeEnvironment: [], workEnvironment: [],
    smokingStatus: '', cigarettesPerDay: '', yearsSmoking: '', yearsSinceQuitSmoking: '',
    alcoholStatus: '', drinksPerWeek: '', drinksPerDay: '', yearsDrinking: '', yearsSinceQuitDrinking: '',
    glassesWaterPerDay: '', eatingHabits: [],
    regularVoiceUse: [],
    hoursVoiceHome: '', reasonsVoiceHome: [], reasonsVoiceHomeOther: '',
    hoursVoiceWork: '', reasonsVoiceWork: [], reasonsVoiceWorkOther: ''
  }
}

// Declared before visibleBaselineSections below, which reads it inside a
// watch() source — that source is evaluated immediately at registration
// time (not lazily), so baselineAnswers must already exist by then.
const baselineAnswers = reactive(createInitialBaselineAnswers())

// Only the sections relevant to this person's branch answers — e.g. someone
// who never smoked never sees the smoking follow-up at all, and the "Section
// X of N" count reflects that real, shorter path instead of a fixed number.
const visibleBaselineSections = computed(() =>
  baselineSections.filter((s) => !s.showIf || s.showIf(baselineAnswers))
)

function questionsOf(section) {
  return typeof section.questions === 'function' ? section.questions(baselineAnswers) : section.questions
}

const currentBaselineSection = computed(() => {
  const list = visibleBaselineSections.value
  const idx = typeof baselineStep.value === 'number' ? baselineStep.value - 1 : list.length - 1
  return list[Math.min(Math.max(idx, 0), list.length - 1)]
})

const currentBaselineQuestions = computed(() => questionsOf(currentBaselineSection.value))

function isBaselineAnswered(q) {
  const v = baselineAnswers[q.key]
  if (q.type === 'checkbox-group') return v.length > 0
  return v !== '' && v !== null && v !== undefined
}

const isBaselineSectionComplete = computed(() =>
  typeof baselineStep.value !== 'number' || currentBaselineQuestions.value.every(isBaselineAnswered)
)

const baselineSectionTouched = ref(false)
watch(baselineStep, () => { baselineSectionTouched.value = false })

// If the user backs up and changes a branch answer (e.g. smoking status)
// after already passing the now-removed detail section, keep the step
// pointer inside the shrunk list instead of past the end of it.
watch(visibleBaselineSections, (list) => {
  if (typeof baselineStep.value === 'number' && baselineStep.value > list.length) {
    baselineStep.value = list.length
  }
})

function toggleBaselineCheckbox(key, option, exclusiveOption) {
  toggleCheckboxIn(baselineAnswers, key, option, exclusiveOption)
}

function stepBaselineNumber(key, delta, max) {
  stepNumberIn(baselineAnswers, key, delta, max)
  baselineSectionTouched.value = true
}

function sanitizeBaselineNumberInput(key, event, max) {
  sanitizeNumberInputIn(baselineAnswers, key, event, max)
  baselineSectionTouched.value = true
}

function baselineGoBack() {
  if (typeof baselineStep.value === 'number' && baselineStep.value > 1) baselineStep.value--
  else requestClose()
}

function baselineNext() {
  if (typeof baselineStep.value !== 'number') return
  if (baselineStep.value < visibleBaselineSections.value.length) {
    baselineStep.value++
  } else {
    saveJSON(LS_BASELINE_KEY, baselineAnswers)
    hasBaseline.value = true
    baselineStep.value = 'complete'
  }
}

const baselinePrivacyLines = [
  'Your data is kept confidential',
  'Used only for voice health research'
]

// ── Icons ────────────────────────────────────────────────────────────
const CloseIcon = () => h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
  h('path', { d: 'M6 6l12 12M18 6 6 18', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round' })
])

const CheckIcon = () => h('svg', { viewBox: '0 0 24 24', fill: 'none', class: 'check-icon' }, [
  h('circle', { cx: '12', cy: '12', r: '10', fill: '#22c55e' }),
  h('path', { d: 'm7.5 12.5 3 3 6-6.5', stroke: '#fff', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
])

const InsightIcon = (props) => {
  const paths = {
    pulse: 'M3 12h4l2-6 4 12 2-6h6',
    scale: 'M12 3v18M6 7l-3 6a3 3 0 0 0 6 0l-3-6ZM18 7l-3 6a3 3 0 0 0 6 0l-3-6ZM5 7h14',
    trend: 'M3 17l6-6 4 4 8-8M15 7h6v6'
  }
  return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
    h('path', { d: paths[props.kind], stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
  ])
}

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; }

.assess-page {
  min-height: 100dvh;
  background: linear-gradient(180deg, #eef2ff 0%, #eff3ff 40%, #fafbff 100%);
  font-family: 'Poppins', sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 84px 20px 32px;
}

.loading-state { min-height: 60vh; }

.page-inner {
  flex: 1;
  width: 100%;
  max-width: 620px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 6vh;
  gap: 16px;
}

.page-inner-wide {
  max-width: 760px;
}

/* ── Shared bits ── */
.page-topbar {
  position: fixed;
  top: 24px;
  left: 24px;
  z-index: 10;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(101, 148, 228, 0.35);
  border-radius: 20px;
  background: #fff;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #6594e4;
  cursor: pointer;
}

.back-arrow { font-size: 15px; }

.card {
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 2px 16px rgba(101, 148, 228, 0.08);
  padding: 24px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #eef1f8;
}

.card-head strong { display: block; font-size: 14px; color: #1a1a2e; }
.card-head span { display: block; font-size: 11.5px; color: #8b96ad; margin-top: 1px; }

.icon-wrap {
  border-radius: 12px;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-wrap.sm { width: 38px; height: 38px; }
.icon-wrap.sm svg { width: 19px; height: 19px; }
.header-icon-img { width: 20px; height: 20px; object-fit: contain; }
.icon-wrap.lg { width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 6px; }
.icon-wrap.lg svg { width: 28px; height: 28px; }
.complete-icon-img { width: 32px; height: 32px; object-fit: contain; }

/* ── Intro ── */
.assess-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  text-align: center;
  margin: 6px 0 0;
}

.assess-subtitle {
  font-size: 13px;
  color: #8b96ad;
  text-align: center;
  margin: 0 0 4px;
}

.why-title {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px;
}

.why-list {
  list-style: none;
  margin: 0 0 20px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.why-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #444;
}

.why-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #eaf1ff;
  color: #6594e4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.why-icon svg { width: 14px; height: 14px; }

.intro-footnote {
  text-align: center;
  font-size: 11.5px;
  color: #8b96ad;
  margin: 10px 0 0;
}

/* ── Member: two-card layout ── */
.member-card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.member-task-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  padding: 26px;
}

.task-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-wrap.md { width: 52px; height: 52px; border-radius: 15px; }
.task-icon-img { width: 26px; height: 26px; object-fit: contain; }

/* A darker gray than the page's usual muted tone — the icon reads as white
   on white otherwise, since it's a light PNG rather than a currentColor SVG. */
.icon-wrap-muted { background: #c7cdd9; }

.task-badge {
  background: #eef1f6;
  color: #6b7690;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 20px;
}

.task-badge-accent { background: #eaf1ff; color: #3d6fd1; }
.task-badge-done {
  background: #e8f6ec;
  color: #2f9e52;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.task-title { font-size: 17px; font-weight: 700; color: #1a1a2e; margin: 0; }
.task-desc { font-size: 13px; color: #8b96ad; line-height: 1.6; margin: 0; flex: 1; }

.member-task-card .btn-primary.sm,
.member-task-card .btn-outline {
  width: 100%;
  justify-content: center;
  margin-top: 4px;
}

/* ── Buttons ── */
.btn-primary {
  width: 100%;
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
  border-radius: 20px;
  padding: 13px;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-primary.sm { width: auto; padding: 10px 22px; font-size: 13px; }
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary:disabled:hover { opacity: 0.4; }

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(101, 148, 228, 0.35);
  background: #fff;
  border-radius: 20px;
  padding: 10px 20px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
}

.btn-outline:hover { background: #f4f7ff; }

.complete-secondary-btn { width: 100%; justify-content: center; margin-top: 10px; }

.link-plain {
  border: none;
  background: transparent;
  color: #6594e4;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  padding: 2px;
}

.link-muted { color: #9aa4bd; }
.link-muted:hover { color: #7b869e; }

/* ── Progress ── */
.progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.section-pill {
  background: #eaf1ff;
  color: #6594e4;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
}

.section-name {
  font-size: 12px;
  font-weight: 500;
  color: #8b96ad;
}

.progress-track {
  height: 5px;
  background: #eef1f8;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #95b9f7, #6594e4);
  border-radius: 4px;
  transition: width 0.25s ease;
}

/* ── Questions ── */
.questions {
  display: flex;
  flex-direction: column;
  gap: 22px;
  margin-bottom: 24px;
}

.question-label {
  font-size: 13.5px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.required-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #c83d3d;
  background: #fdeaea;
  padding: 2px 8px;
  border-radius: 10px;
}

.question-block.incomplete .option-row {
  border-color: rgba(200, 61, 61, 0.35);
}

.question-block.incomplete .number-stepper,
.question-block.incomplete .text-input {
  border-color: rgba(200, 61, 61, 0.4);
}

.question-block.incomplete .severity-table-wrap {
  border-color: rgba(200, 61, 61, 0.35);
}

.question-sublabel, .question-hint {
  font-size: 11.5px;
  color: #8b96ad;
  margin: 0 0 10px;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(101, 148, 228, 0.2);
  border-radius: 12px;
  padding: 11px 14px;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.option-row:hover { background: #f8faff; }
.option-row.selected { border-color: #6594e4; background: #f4f7ff; color: #1a1a2e; font-weight: 500; }

.option-row input { position: absolute; opacity: 0; width: 0; height: 0; }

.radio-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid #c3cee3;
  flex-shrink: 0;
  position: relative;
}

.option-row.selected .radio-dot { border-color: #6594e4; }
.option-row.selected .radio-dot::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  background: #6594e4;
}

.checkbox-box {
  width: 16px;
  height: 16px;
  border-radius: 5px;
  border: 1.5px solid #c3cee3;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: border-color 0.15s, background 0.15s;
}

.checkbox-box .check-svg {
  width: 12px;
  height: 12px;
  opacity: 0;
  transform: scale(0.7);
  transition: opacity 0.1s ease, transform 0.1s ease;
}

.option-row.selected .checkbox-box { border-color: #6594e4; background: #6594e4; }
.option-row.selected .checkbox-box .check-svg { opacity: 1; transform: scale(1); }

.number-stepper {
  display: flex;
  align-items: stretch;
  border: 1px solid rgba(101, 148, 228, 0.25);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.15s;
}

.number-stepper:focus-within { border-color: #6594e4; }

.stepper-btn {
  flex-shrink: 0;
  width: 44px;
  border: none;
  background: #f4f7ff;
  color: #6594e4;
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stepper-btn:hover:not(:disabled) { background: #eaf1ff; }
.stepper-btn:disabled { color: #c3cee3; cursor: not-allowed; }
.stepper-btn:first-child { border-right: 1px solid rgba(101, 148, 228, 0.2); }
.stepper-btn:last-child { border-left: 1px solid rgba(101, 148, 228, 0.2); }

.number-input {
  flex: 1;
  min-width: 0;
  width: 100%;
  border: none;
  padding: 11px 10px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  color: #1a1a2e;
  text-align: center;
}

.number-input:focus { outline: none; }

.text-input {
  text-align: left;
  border: 1px solid rgba(101, 148, 228, 0.25);
  border-radius: 12px;
  transition: border-color 0.15s;
}
.text-input:focus { border-color: #6594e4; }
.other-input { margin-top: 8px; }

/* Hide native spin buttons — the custom stepper replaces them */
.number-input::-webkit-outer-spin-button,
.number-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.number-input[type="number"] { -moz-appearance: textfield; appearance: textfield; }

/* ── Severity table ── */
.severity-table-wrap {
  overflow-x: auto;
  border: 1px solid rgba(101, 148, 228, 0.22);
  border-radius: 12px;
}

.severity-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}

.severity-table th, .severity-table td {
  text-align: center;
  padding: 8px 6px;
  border-bottom: 1px solid #eef1f8;
}

.severity-table thead th {
  background: #eaf1ff;
  border-bottom: 1px solid rgba(101, 148, 228, 0.22);
}

.severity-table thead th:first-child { border-top-left-radius: 11px; }
.severity-table thead th:last-child { border-top-right-radius: 11px; }

.severity-table th { color: #3d6fd1; font-weight: 700; font-size: 11.5px; }
.severity-table .symptom-col { text-align: left; white-space: nowrap; padding-left: 12px; }
.severity-table td.symptom-col { font-weight: 500; color: #444; }
.severity-table tbody tr:nth-child(odd) { background: #f8faff; }
.severity-table tbody tr:last-child td { border-bottom: none; }
.severity-table tbody tr:last-child td:first-child { border-bottom-left-radius: 11px; }
.severity-table tbody tr:last-child td:last-child { border-bottom-right-radius: 11px; }
.severity-table input[type="radio"] { width: 15px; height: 15px; accent-color: #6594e4; cursor: pointer; }

/* ── Nav row ── */
.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

/* ── Complete screen ── */
.complete-body {
  text-align: center;
  padding-top: 4px;
}

.complete-body h2 { font-size: 19px; color: #1a1a2e; margin: 0 0 4px; }
.complete-body p { font-size: 13px; color: #8b96ad; margin: 0 0 18px; }

.privacy-box {
  background: #eaf1ff;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  margin-bottom: 20px;
}

.privacy-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: #3d5a99;
  font-weight: 500;
}

.privacy-line :deep(.check-icon) { width: 16px; height: 16px; flex-shrink: 0; }

.complete-links {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 12px;
}

/* ── Popup ── */
.modal-backdrop {
  /* Teleported to <body>, so it's no longer a descendant of .assess-page —
     font-family must be set explicitly here, it won't inherit down. */
  font-family: 'Poppins', sans-serif;
  position: fixed;
  inset: 0;
  background: rgba(26, 26, 46, 0.45);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1000;
  animation: backdropIn 0.15s ease;
}

@keyframes backdropIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-panel {
  position: relative;
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 20px 60px rgba(20, 30, 60, 0.3);
  padding: 26px;
  width: 100%;
  max-width: 620px;
  max-height: 88vh;
  overflow-y: auto;
  animation: panelIn 0.16s ease;
}

@keyframes panelIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f4f7ff;
  color: #6594e4;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.modal-close svg { width: 16px; height: 16px; }
.modal-close:hover { background: #eaf1ff; }

/* ── Close confirmation (matches the Leave/Discard modal pattern used on
   the Recording page, for consistency across the app) ── */
.modal-overlay {
  font-family: 'Poppins', sans-serif;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.modal-card {
  background: #fff;
  border-radius: 24px;
  padding: 32px 28px;
  max-width: 360px;
  width: 90%;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.18);
}

.modal-leave-icon { width: 56px; height: 56px; object-fit: contain; margin-bottom: 16px; }
.modal-title { font-size: 17px; font-weight: 700; color: #1a1a2e; margin: 0 0 10px; text-align: center; }
.modal-desc { font-size: 13px; color: #666; text-align: center; line-height: 1.6; margin: 0 0 24px; }

.modal-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(102deg, #95b9f7, #6594e4);
  color: #fff;
  border: none;
  border-radius: 14px;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 10px;
}

.modal-btn-red { background: linear-gradient(102deg, #ff7b7b, #e84545); }

.modal-dismiss {
  background: none;
  border: none;
  color: #aaa;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  cursor: pointer;
}

.modal-dismiss:hover { color: #888; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* ── Step transition ── */
.step-panel { will-change: transform, opacity; }

.slide-forward-enter-active,
.slide-forward-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.slide-forward-enter-from { opacity: 0; transform: translateX(16px); }
.slide-forward-leave-to { opacity: 0; transform: translateX(-16px); }
.slide-back-enter-from { opacity: 0; transform: translateX(-16px); }
.slide-back-leave-to { opacity: 0; transform: translateX(16px); }

@media (prefers-reduced-motion: reduce) {
  .slide-forward-enter-active, .slide-forward-leave-active,
  .slide-back-enter-active, .slide-back-leave-active {
    transition: opacity 0.12s ease;
  }
  .slide-forward-enter-from, .slide-forward-leave-to,
  .slide-back-enter-from, .slide-back-leave-to {
    transform: none;
  }
}

/* ── Responsive ── */
@media (max-width: 560px) {
  .page-topbar { top: 16px; left: 16px; }
  .card, .modal-panel { padding: 18px; }
  .member-card-grid { grid-template-columns: 1fr; }
  .nav-row { flex-direction: column-reverse; }
  .btn-outline, .btn-primary.sm { width: 100%; justify-content: center; }
  .modal-backdrop { padding: 0; align-items: flex-end; }
  .modal-panel { max-width: 100%; max-height: 92vh; border-radius: 22px 22px 0 0; }

  /* Keep the close-confirmation as a small centered dialog, not a bottom sheet */
}
</style>
