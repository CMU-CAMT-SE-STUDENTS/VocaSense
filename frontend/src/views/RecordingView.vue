<template>
  <div class="recording-page">

    <div class="page-topbar">
    <button class="btn-back" @click="goBack">
      <span class="back-arrow">←</span> Back To Home
    </button>
  </div>

  <div class="page-inner">

      <!--RECORDING IN PROGRESS-->
      <template v-if="recordingStatus === 'recording'">
        <div class="main-card">
          <div class="status-badge-recording">
            <span class="dot-recording"></span>
            Recording in Progress
          </div>

          <div class="countdown-display">
            <span class="countdown-number">{{ countdown }}</span>
            <p class="countdown-label">seconds remaining</p>
          </div>

          <div class="live-waveform-wrap">
            <div
              v-for="(h, i) in liveWaveformBars"
              :key="i"
              class="live-bar"
              :style="{ height: Math.round(h) + 'px' }"
            ></div>
          </div>

          <button class="btn-cancel" @click="cancelRecording">
            <img src="@/assets/icons/cancel.png" alt="" class="btn-cancel-img" />
            Cancel Recording
          </button>
        </div>
      </template>

      <!-- WAITING FOR VOICE -->
      <template v-else-if="recordingStatus === 'waiting_voice'">
        <div class="main-card">
          <div class="status-badge-waiting">
            <span class="dot-waiting"></span>
            Listening...
          </div>
          <p class="waiting-title">Start speaking to begin recording</p>
          <p class="waiting-hint">Say <strong>"Ahhhh"</strong> loudly — the timer will start automatically</p>
          <div class="live-waveform-wrap">
            <div
              v-for="(h, i) in liveWaveformBars"
              :key="i"
              class="live-bar"
              :style="{ height: Math.round(h) + 'px' }"
            ></div>
          </div>
          <button class="btn-cancel" @click="cancelWaiting">
            <img src="@/assets/icons/cancel.png" alt="" class="btn-cancel-img" />
            Cancel
          </button>
        </div>
      </template>

      <!-- VALIDATING RECORDING -->
      <template v-else-if="recordingStatus === 'validating_recording'">
        <div class="main-card">
          <div class="status-badge-validating">
            <span class="dot-validating"></span>
            Checking Voice Sample
          </div>

          <div class="validation-loader" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <h1 class="validating-title">Checking your recording</h1>
          <p class="validating-subtitle">Please wait while we verify that this is a continuous "Ahhhh" sample.</p>
        </div>
      </template>

      <!-- RECORDING COMPLETE -->
      <template v-else-if="recordingStatus === 'completed'">

        <!-- No voice detected → Recording Failed -->
        <div v-if="!voiceDetected" class="main-card">
          <img src="@/assets/icons/notcomplete.png" alt="Failed" class="complete-check-img" />
          <h1 class="complete-title">Recording Failed</h1>

          <div class="error-reasons">
            <div
              v-for="(reason, i) in validationReasons"
              :key="i"
              class="error-reason-item"
            >
              <span class="error-reason-icon">!</span>
              <span class="error-reason-text">{{ reason }}</span>
            </div>
          </div>

          <button class="btn-analyze" @click="recordAgain">Try Again</button>
        </div>

        <!-- Voice detected → Recording Complete -->
        <div v-else class="main-card">
          <img src="@/assets/icons/correct.png" alt="Complete" class="complete-check-img" />
          <h1 class="complete-title">Recording Complete!</h1>
          <p class="complete-subtitle">Your voice sample has been captured successfully</p>
          <p v-if="analysisError" class="sample-error-text">{{ analysisError }}</p>

          <div class="complete-audio-card">
            <div class="audio-player complete-player">
              <button class="play-btn" @click="toggleRecordingPlayback">
                <svg v-if="!isPlayingRecording" width="11" height="13" viewBox="0 0 11 13" fill="none">
                  <path d="M1 1L10 6.5L1 12V1Z" fill="white" />
                </svg>
                <svg v-else width="10" height="12" viewBox="0 0 10 12" fill="none">
                  <rect x="0" y="0" width="3" height="12" rx="1.5" fill="white" />
                  <rect x="7" y="0" width="3" height="12" rx="1.5" fill="white" />
                </svg>
              </button>
              <div class="waveform">
                <div
                  v-for="(barHeight, i) in waveformBars"
                  :key="i"
                  class="waveform-bar"
                  :class="{ played: i < recordingPlayProgress }"
                  :style="{ height: barHeight + 'px' }"
                ></div>
              </div>
              <span class="audio-duration">5.0s</span>
            </div>
          </div>

          <div class="complete-actions">
            <button class="btn-record-again" @click="recordAgain">Record Again</button>
            <button class="btn-analyze" @click="analyzeVoice">Analyze Voice</button>
          </div>
        </div>

      </template>

      <!-- DEFAULT (ready / not_ready / checking) -->
      <template v-else>
        <!-- Status badge above title -->
        <div class="status-badge" :class="statusClass">
          <span class="status-dot"></span>
          {{ statusText }}
        </div>

        <h1 class="page-title">Voice Recording Test</h1>
        <p class="page-subtitle">
          Say <span class="highlight">"Ahhhh"</span> continuously for 5 seconds when the recording starts
        </p>

        <!-- Recording card -->
        <div class="recording-card">
          <div class="card-mic-icon">
            <img src="@/assets/icons/Microphone1.png" alt="Microphone" width="32" height="32" />
          </div>

          <p class="card-label">Listen to the example voice before recording</p>

          <!-- Sample audio player (play-only) -->
          <div class="audio-player" @click="toggleSample" :class="{ 'player-playing': isPlayingSample }">
            <button class="play-btn" @click.stop="toggleSample">
              <svg v-if="!isPlayingSample" width="11" height="13" viewBox="0 0 11 13" fill="none">
                <path d="M1 1L10 6.5L1 12V1Z" fill="white" />
              </svg>
              <div v-else class="sound-bars">
                <span></span><span></span><span></span>
              </div>
            </button>
            <div class="waveform">
              <div
                v-for="(barHeight, i) in waveformBars"
                :key="i"
                class="waveform-bar"
                :class="{ played: i < playProgress }"
                :style="{ height: barHeight + 'px' }"
              ></div>
            </div>
            <span class="audio-duration">5.0s</span>
          </div>

          <p v-if="sampleLoadError" class="sample-error-text">
            Unable to load voice example. Please try again.
          </p>

          <!-- Instructions -->
          <div class="instructions">
            <div class="instr-item">
              <span class="instr-num">1</span>
              <span class="instr-text">Find a quiet place</span>
            </div>
            <div class="instr-item">
              <span class="instr-num">2</span>
              <span class="instr-text">Click the record button below</span>
            </div>
            <div class="instr-item">
              <span class="instr-num">3</span>
              <span class="instr-text">Say "Ahhhh" for 5 seconds</span>
            </div>
          </div>
        </div>

        <!-- Noise-during-recording card -->
        <div v-if="noiseDuringRec" class="noise-rec-card">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="error-icon" style="flex-shrink:0">
            <circle cx="9" cy="9" r="8.5" stroke="#ff9f0a" />
            <path d="M9 5v4M9 12v.5" stroke="#ff9f0a" stroke-width="1.5" stroke-linecap="round" />
          </svg>
          <p class="noise-rec-text">Recording was stopped because the background noise was too high. Please move to a quieter place and try again.</p>
        </div>

        <!-- Error card -->
        <div v-if="errorType" class="error-card">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="error-icon">
            <circle cx="9" cy="9" r="8.5" stroke="#e84545" />
            <path d="M9 5v4M9 12v.5" stroke="#e84545" stroke-width="1.5" stroke-linecap="round" />
          </svg>
          <p class="error-text">{{ errorMessage }}</p>
        </div>

        <!-- Start Recording button -->
        <button
          class="btn-record"
          :class="{
            'is-not-ready': recordingStatus === 'not_ready' && !errorType,
            'is-busy':      recordingStatus === 'requesting' || recordingStatus === 'checking_noise',
          }"
          @click="handleRecordButton"
          :disabled="isBtnDisabled"
        >
          <img src="@/assets/icons/Microphone.png" alt="" class="btn-mic-img" />
          {{ btnLabel }}
        </button>
      </template>

    </div><!-- /page-inner -->

    <p class="disclaimer">
      This platform provides preliminary voice health insights and does not replace professional medical diagnosis.
    </p>

    <!-- Noise alert modal -->
    <Transition name="modal-fade">
      <div v-if="showNoiseAlert" class="modal-overlay" @click="dismissNoiseAlert">
        <div class="modal-card" @click.stop>
          <div class="modal-icon-wrap">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="18" r="18" fill="rgba(255,159,10,0.12)" />
              <path d="M12 18c0-3.314 2.686-6 6-6v0c3.314 0 6 2.686 6 6v0" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round"/>
              <path d="M9 18c0-4.97 4.03-9 9-9v0c4.97 0 9 4.03 9 9v0" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
              <circle cx="18" cy="22" r="2" fill="#ff9f0a"/>
              <path d="M18 18v-2" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <h3 class="modal-title">Background Noise Too High</h3>
          <p class="modal-desc">
            We detected too much background noise. Please move to a quieter place for accurate voice analysis.
          </p>
          <button class="modal-btn" @click="retryAfterNoise">Try Again</button>
          <button class="modal-dismiss" @click="goBack">Cancel</button>
        </div>
      </div>
    </Transition>

    <!-- Noise during recording modal -->
    <Transition name="modal-fade">
      <div v-if="showNoiseDuringRecAlert" class="modal-overlay">
        <div class="modal-card" @click.stop>
          <div class="modal-icon-wrap">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="18" r="18" fill="rgba(255,159,10,0.12)" />
              <path d="M12 18c0-3.314 2.686-6 6-6v0c3.314 0 6 2.686 6 6v0" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round"/>
              <path d="M9 18c0-4.97 4.03-9 9-9v0c4.97 0 9 4.03 9 9v0" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
              <circle cx="18" cy="22" r="2" fill="#ff9f0a"/>
              <path d="M18 18v-2" stroke="#ff9f0a" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <h3 class="modal-title">Background Noise Detected</h3>
          <p class="modal-desc">
            Too much background noise was detected during recording. Please move to a quieter place and try again.
          </p>
          <button class="modal-btn" @click="retryAfterNoiseDuringRec">Record Again</button>
          <button class="modal-dismiss" @click="cancelNoiseDuringRec">Cancel</button>
        </div>
      </div>
    </Transition>

    <!-- Leave during recording modal -->
    <Transition name="modal-fade">
      <div v-if="showLeaveAlert" class="modal-overlay">
        <div class="modal-card" @click.stop>
          <img src="@/assets/icons/notcomplete.png" alt="" class="modal-leave-icon" />
          <h3 class="modal-title">Leave Recording?</h3>
          <p class="modal-desc">
            Recording is in progress. If you leave now, your current recording will be discarded.
          </p>
          <button class="modal-btn modal-btn-red" @click="confirmLeave">Leave & Discard</button>
          <button class="modal-dismiss" @click="cancelLeave">Keep Recording</button>
        </div>
      </div>
    </Transition>

    <!-- Record Again confirmation modal -->
    <Transition name="modal-fade">
      <div v-if="showRecordAgainAlert" class="modal-overlay">
        <div class="modal-card" @click.stop>
          <img src="@/assets/icons/notcomplete.png" alt="" class="modal-leave-icon" />
          <h3 class="modal-title">Discard Recording?</h3>
          <p class="modal-desc">
            Your current recording will be permanently deleted. This action cannot be undone.
          </p>
          <button class="modal-btn modal-btn-red" @click="confirmRecordAgain">Discard & Re-record</button>
          <button class="modal-dismiss" @click="cancelRecordAgain">Keep Recording</button>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import sampleAudioSrc from '@/assets/audio/maonoNormal.mp3'
import { setPendingVoiceAnalysisInput } from '@/utils/voiceAnalysisStore'

const router = useRouter()

const AUDIO_CONSTRAINTS = {
  audio: {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: { ideal: 1 },
    sampleRate: { ideal: 44100 },
  },
}
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const NOISE_LOUD_THRESHOLD = 20

const ERROR_MESSAGES = {
  denied:          'Microphone access is required. Please allow microphone access in your browser settings and try again.',
  not_found:       'No microphone was detected. Please connect a microphone and try again.',
  not_readable:    'Your microphone is in use by another application. Please close it and try again.',
  security:        'Microphone access requires a secure connection (HTTPS).',
  recording_error: 'A system error occurred during recording. Please try again.',
  other:           'Could not access the microphone. Please check your device and try again.',
}

// ── Waveform bars (static decorative)
const waveformBars = [
  4, 6, 9, 7, 11, 14, 17, 19, 15, 17, 20, 18, 16, 19, 20, 17, 15, 18, 20, 18, 16, 14, 18, 19, 15,
  13, 11, 9, 12, 10, 8, 9, 7, 5, 4,
]

// ── Sample audio player (play-only)
const isPlayingSample  = ref(false)
const playProgress     = ref(0)
const sampleLoadError  = ref(false)
let sampleAudio        = null
let sampleInterval     = null

// ── Recording state machine
// not_ready → requesting → checking_noise → ready → waiting_voice → recording → validating_recording → completed
const recordingStatus  = ref('not_ready')
const errorType        = ref(null)
const showNoiseAlert   = ref(false)
const countdown        = ref(5)
let countdownInterval  = null
let mediaRecorder      = null
let audioStream        = null

// ── Audio capture
let audioChunks           = []
let recordingWasCancelled = false
let recordingHadError     = false
const recordedAudioUrl    = ref(null)
const recordedAudioBlob   = ref(null)
const recordedWavBlob     = ref(null)
const lastVoiceValidation = ref(null)
const analysisError       = ref('')
const REASON_MAP = {
  'Audio is too short.': 'Recording is too short. Hold "Ahhhh" for at least 3 seconds.',
  'The voiced part is not continuous enough.': 'Keep the sound continuous. Try not to stop in the middle.',
  'Voiced duration is too short.': 'Hold "Ahhhh" longer. Aim for at least 3 seconds.',
  'Repeated syllable-like attacks were detected.': 'Say one long "Ahhhh". Avoid repeating short sounds.',
  'Amplitude changes look like running speech rather than one held Ah.': 'Hold one steady "Ahhhh". Do not speak normally.',
  'The voice has too many gaps.': 'Keep the sound going the whole time. Do not pause.',
  'The sound changes too much, like speech rather than a held vowel.': 'Hold a steady "Ahhhh". Try not to change the sound.',
  'Spectral changes look like consonants or changing vowels, not sustained Ah.': 'Say a clear, steady "Ahhhh" from start to finish.',
  'Too much high-frequency consonant-like energy was detected.': 'Use a soft open "Ahhhh". Avoid hissing or sharp sounds.',
  'The vowel band is too weak for an Ah-like sample.': 'Open your mouth wider. Say "Ahhhh" more clearly.',
  'Not enough voiced pitch was detected.': 'Speak louder so your voice is clearly heard.',
}

const validationReasons = computed(() => {
  const reasons = lastVoiceValidation.value?.ah_validation?.reasons
    ?.filter(r => !r.toLowerCase().startsWith('snr'))
    ?.map(r => REASON_MAP[r] ?? r)
  return reasons?.length ? reasons : ['Voice unclear — say "Ahhhh" louder and hold for 3 seconds.']
})

// ── Recorded audio playback
const isPlayingRecording    = ref(false)
const recordingPlayProgress = ref(0)
let playbackAudio           = null
let playbackInterval        = null

// ── Live waveform during recording
const liveWaveformBars = ref(Array(32).fill(8))
let liveAudioCtx       = null
let liveAnalyser       = null
let liveAnimFrame      = null
let liveSourceNode     = null
let noiseCheckAnalyser = null

// ── Voice detection
const voiceDetected           = ref(false)
const noiseDuringRec          = ref(false)
const showNoiseDuringRecAlert = ref(false)
const showLeaveAlert          = ref(false)
const showRecordAgainAlert    = ref(false)
let pendingNavNext            = null
let voiceFrameCount           = 0
let noiseDuringRecordingDetected = false

// ── Computed
const statusText = computed(
  () => ({
    not_ready:      'Not Ready to Record',
    requesting:     'Requesting Access',
    checking_noise: 'Checking Environment',
    ready:          'Ready to Record',
    waiting_voice:  'Listening for Voice',
    validating_recording: 'Checking Voice Sample',
  })[recordingStatus.value] ?? 'Not Ready to Record',
)

const statusClass = computed(
  () => ({
    not_ready:      'status-not-ready',
    requesting:     'status-checking',
    checking_noise: 'status-checking',
    ready:          'status-ready',
    validating_recording: 'status-checking',
  })[recordingStatus.value] ?? 'status-not-ready',
)

const isBtnDisabled = computed(
  () =>
    ['requesting', 'checking_noise', 'validating_recording'].includes(recordingStatus.value) ||
    (recordingStatus.value === 'not_ready' && !errorType.value),
)

const btnLabel = computed(() => {
  if (errorType.value) return 'Try Again'
  return ({
    not_ready:      'Start Recording',
    requesting:     'Requesting Permission...',
    checking_noise: 'Checking Environment...',
    ready:          'Start Recording',
  })[recordingStatus.value] ?? 'Start Recording'
})

const errorMessage = computed(() => ERROR_MESSAGES[errorType.value] ?? '')

// ── Navigation
const goBack = () => router.push('/')

// ── Sample audio
const toggleSample = () => {
  if (!sampleAudio) {
    sampleAudio = new Audio(sampleAudioSrc)
    sampleAudio.addEventListener('ended', () => {
      isPlayingSample.value = false
      playProgress.value = 0
      clearInterval(sampleInterval)
    })
    sampleAudio.addEventListener('error', () => {
      isPlayingSample.value = false
      playProgress.value = 0
      clearInterval(sampleInterval)
      sampleLoadError.value = true
    })
  }

  if (isPlayingSample.value) {
    sampleAudio.pause()
    clearInterval(sampleInterval)
    isPlayingSample.value = false
  }

  sampleLoadError.value = false
  sampleAudio.currentTime = 0
  sampleAudio.play()
  isPlayingSample.value = true
  playProgress.value = 0
  sampleInterval = setInterval(() => {
    if (sampleAudio?.duration) {
      playProgress.value = Math.floor(
        (sampleAudio.currentTime / sampleAudio.duration) * waveformBars.length,
      )
    }
  }, 80)
}

// ── Noise measurement
const percentile = (values, ratio) => {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const index = Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * ratio))
  return sorted[index]
}

const measureBackgroundNoise = (stream) =>
  new Promise((resolve) => {
    const AudioCtx = window.AudioContext || window['webkitAudioContext']
    const ctx      = new AudioCtx()
    const source   = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 2048
    source.connect(analyser)

    const data     = new Uint8Array(analyser.fftSize)
    const freqData = new Uint8Array(analyser.frequencyBinCount)
    const rms             = []
    const peaks           = []
    const zcrs            = []
    const speechBinCounts = []
    const started  = performance.now()
    const duration = 2000

    const finish = () => {
      const avgRms = rms.reduce((sum, value) => sum + value, 0) / Math.max(rms.length, 1)
      const p90Rms = percentile(rms, 0.9)
      const maxPeak = Math.max(...peaks, 0)
      const spikeFrames = peaks.filter((peak, index) => peak >= 20 || rms[index] >= NOISE_LOUD_THRESHOLD).length
      const spikeScore = (spikeFrames / Math.max(peaks.length, 1)) * 100
      const rmsStd = Math.sqrt(rms.reduce((sum, v) => sum + (v - avgRms) ** 2, 0) / Math.max(rms.length, 1))
      const avgZcr = zcrs.reduce((sum, v) => sum + v, 0) / Math.max(zcrs.length, 1)
      const zcrScore = avgZcr * 0.7

      // speech spreads energy across many freq bins (100Hz–3kHz); AC/fan only uses a few harmonics
      const avgActiveBins = speechBinCounts.reduce((sum, v) => sum + v, 0) / Math.max(speechBinCounts.length, 1)
      const spectralScore = avgActiveBins * 0.5

      const score = Math.max(avgRms, p90Rms, maxPeak * 0.85, spikeScore, rmsStd * 4, zcrScore, spectralScore)

      console.log('[noise-check]', {
        avgRms:       avgRms.toFixed(2),
        p90Rms:       p90Rms.toFixed(2),
        maxPeak:      maxPeak.toFixed(0),
        spikeScore:   spikeScore.toFixed(1),
        rmsStd:       rmsStd.toFixed(2),
        zcrScore:     zcrScore.toFixed(1),
        avgActiveBins:avgActiveBins.toFixed(1),
        spectralScore:spectralScore.toFixed(1),
        FINAL:        score.toFixed(2),
        threshold:    NOISE_LOUD_THRESHOLD,
        PASS:         score < NOISE_LOUD_THRESHOLD,
      })

      source.disconnect()
      ctx.close()
      resolve(score)
    }

    const capture = () => {
      analyser.getByteTimeDomainData(data)
      analyser.getByteFrequencyData(freqData)

      let sumSquares = 0
      let peak = 0
      let zcr = 0
      for (let i = 0; i < data.length; i++) {
        const centered = data[i] - 128
        sumSquares += centered * centered
        peak = Math.max(peak, Math.abs(centered))
        if (i > 0 && centered * (data[i - 1] - 128) < 0) zcr++
      }

      // bins 5–139 ≈ 100Hz–3kHz at 44100Hz SR; threshold 25 ≈ –91dB (above noise floor)
      let activeBins = 0
      for (let i = 5; i <= 139; i++) {
        if (freqData[i] > 25) activeBins++
      }

      rms.push(Math.sqrt(sumSquares / data.length))
      peaks.push(peak)
      zcrs.push(zcr)
      speechBinCounts.push(activeBins)

      if (performance.now() - started >= duration) {
        finish()
        return
      }

      requestAnimationFrame(capture)
    }

    capture()
  })

// ── Live waveform
const startLiveWaveform = (stream) => {
  const AudioCtx = window.AudioContext || window['webkitAudioContext']
  liveAudioCtx   = new AudioCtx()
  liveAudioCtx.resume()
  liveSourceNode = liveAudioCtx.createMediaStreamSource(stream)

  liveAnalyser          = liveAudioCtx.createAnalyser()
  liveAnalyser.fftSize  = 128
  liveSourceNode.connect(liveAnalyser)
  const data = new Uint8Array(liveAnalyser.fftSize)

  noiseCheckAnalyser          = liveAudioCtx.createAnalyser()
  noiseCheckAnalyser.fftSize  = 2048
  liveSourceNode.connect(noiseCheckAnalyser)
  const noiseData = new Uint8Array(noiseCheckAnalyser.fftSize)
  // consecutive frames where peak exceeds the sudden-loud threshold
  let loudFrames = 0

  const draw = () => {
    liveAnimFrame = requestAnimationFrame(draw)
    liveAnalyser.getByteTimeDomainData(data)
    const step = Math.floor(data.length / 32)
    let frameMax = 0
    liveWaveformBars.value = Array.from({ length: 32 }, (_, i) => {
      const sample = data[i * step] ?? 128
      const h = Math.max(8, Math.abs(sample - 128) * 4.0)
      if (h > frameMax) frameMax = h
      return h
    })

    if (recordingStatus.value === 'waiting_voice' && frameMax > 80) {
      voiceFrameCount++
      if (voiceFrameCount >= 25) beginRecording()
    }

    if (recordingStatus.value === 'recording') {
      noiseCheckAnalyser.getByteTimeDomainData(noiseData)
      let peak = 0
      for (let i = 0; i < noiseData.length; i++) {
        peak = Math.max(peak, Math.abs(noiseData[i] - 128))
      }
      // only flag very loud sudden events (door slam, shout, loud bang)
      // normal "Ah" at moderate-to-loud volume peaks around 60–90; threshold 110 avoids false positives
      if (peak >= 110) {
        loudFrames++
        if (loudFrames >= 5) handleNoiseDuringRec()
      } else {
        loudFrames = 0
      }
    } else {
      loudFrames = 0
    }
  }
  draw()
}

const stopLiveWaveform = () => {
  if (liveAnimFrame)       { cancelAnimationFrame(liveAnimFrame); liveAnimFrame = null }
  if (noiseCheckAnalyser)  { noiseCheckAnalyser.disconnect(); noiseCheckAnalyser = null }
  if (liveSourceNode)      { liveSourceNode.disconnect(); liveSourceNode = null }
  if (liveAudioCtx)        { liveAudioCtx.close(); liveAudioCtx = null }
  liveAnalyser = null
  liveWaveformBars.value = Array(32).fill(8)
}

// ── Mic + noise check
const requestMicAndCheck = async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    errorType.value = 'security'
    recordingStatus.value = 'not_ready'
    return
  }
  recordingStatus.value = 'requesting'
  errorType.value = null

  try {
    audioStream = await navigator.mediaDevices.getUserMedia(AUDIO_CONSTRAINTS)
    recordingStatus.value = 'checking_noise'

    const level = await measureBackgroundNoise(audioStream)

    if (level >= NOISE_LOUD_THRESHOLD) {
      audioStream.getTracks().forEach((t) => t.stop())
      audioStream = null
      showNoiseAlert.value = true
      recordingStatus.value = 'not_ready'
    } else {
      recordingStatus.value = 'ready'
    }
  } catch (err) {
    recordingStatus.value = 'not_ready'
    const name = err?.name ?? ''
    if      (name === 'NotAllowedError'  || name === 'PermissionDeniedError') errorType.value = 'denied'
    else if (name === 'NotFoundError'    || name === 'DevicesNotFoundError')  errorType.value = 'not_found'
    else if (name === 'NotReadableError' || name === 'TrackStartError')       errorType.value = 'not_readable'
    else if (name === 'SecurityError')                                         errorType.value = 'security'
    else                                                                       errorType.value = 'other'
  }
}

// ── Recording
const handleRecordButton = async () => {
  if (isBtnDisabled.value) return
  if (errorType.value) { errorType.value = null; await requestMicAndCheck(); return }
  if (recordingStatus.value === 'ready') enterWaitingVoice()
}

const enterWaitingVoice = () => {
  if (sampleAudio && isPlayingSample.value) {
    sampleAudio.pause()
    isPlayingSample.value = false
    playProgress.value = 0
    clearInterval(sampleInterval)
  }
  voiceDetected.value   = false
  noiseDuringRec.value  = false
  voiceFrameCount       = 0
  recordingStatus.value = 'waiting_voice'
  startLiveWaveform(audioStream)
}

const beginRecording = () => {
  if (recordingStatus.value !== 'waiting_voice') return
  recordingStatus.value        = 'recording'
  voiceDetected.value          = true
  voiceFrameCount              = 0
  audioChunks                  = []
  recordingWasCancelled        = false
  recordingHadError            = false
  noiseDuringRecordingDetected = false
  mediaRecorder         = new MediaRecorder(audioStream)

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data)
  }

  mediaRecorder.onerror = () => {
    recordingHadError     = true
    recordingWasCancelled = true
    clearInterval(countdownInterval)
    stopLiveWaveform()
    audioStream?.getTracks().forEach((t) => t.stop())
    audioStream = null
    audioChunks = []
    recordingStatus.value = 'not_ready'
    errorType.value       = 'recording_error'
  }

  mediaRecorder.onstop = async () => {
    if (recordingHadError) return
    if (noiseDuringRecordingDetected) { audioChunks = []; return }
    if (!recordingWasCancelled && audioChunks.length > 0) {
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      if (recordedAudioUrl.value) URL.revokeObjectURL(recordedAudioUrl.value)
      recordedAudioUrl.value = URL.createObjectURL(blob)
      recordedAudioBlob.value = blob
      recordedWavBlob.value = null
      audioChunks = []
      recordingStatus.value = 'validating_recording'
      voiceDetected.value = await validateRecordedVoiceSample()
      recordingStatus.value = 'completed'
    } else {
      audioChunks = []
      audioStream?.getTracks().forEach((t) => t.stop())
      audioStream = null
      requestMicAndCheck()
    }
  }

  mediaRecorder.start()
  countdown.value = 5
  countdownInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) { clearInterval(countdownInterval); stopRecording() }
  }, 1000)
}

const stopRecording = () => {
  clearInterval(countdownInterval)
  stopLiveWaveform()
  audioStream?.getTracks().forEach((t) => t.stop())
  if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop()
  // recordingStatus set to 'completed' inside onstop handler
}

const cancelRecording = () => {
  recordingWasCancelled = true
  clearInterval(countdownInterval)
  stopLiveWaveform()
  if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop()
}

const cancelWaiting = () => {
  stopLiveWaveform()
  audioStream?.getTracks().forEach((t) => t.stop())
  audioStream = null
  requestMicAndCheck()
}

// ── Recorded audio playback
const toggleRecordingPlayback = () => {
  if (!recordedAudioUrl.value) return
  if (!playbackAudio) {
    playbackAudio = new Audio(recordedAudioUrl.value)
    playbackAudio.addEventListener('ended', () => {
      isPlayingRecording.value = false
      recordingPlayProgress.value = 0
      clearInterval(playbackInterval)
    })
  }
  if (isPlayingRecording.value) {
    playbackAudio.pause()
    isPlayingRecording.value = false
    clearInterval(playbackInterval)
  } else {
    playbackAudio.currentTime = 0
    playbackAudio.play()
    isPlayingRecording.value = true
    recordingPlayProgress.value = 0
    playbackInterval = setInterval(() => {
      if (playbackAudio?.duration) {
        recordingPlayProgress.value = Math.floor(
          (playbackAudio.currentTime / playbackAudio.duration) * waveformBars.length,
        )
      }
    }, 80)
  }
}

const recordAgain = () => {
  if (recordingStatus.value === 'completed' && voiceDetected.value) {
    showRecordAgainAlert.value = true
    return
  }
  doRecordAgain()
}

const doRecordAgain = () => {
  if (playbackAudio) { playbackAudio.pause(); playbackAudio = null }
  clearInterval(playbackInterval)
  isPlayingRecording.value = false
  recordingPlayProgress.value = 0
  if (recordedAudioUrl.value) { URL.revokeObjectURL(recordedAudioUrl.value); recordedAudioUrl.value = null }
  recordedAudioBlob.value = null
  recordedWavBlob.value = null
  lastVoiceValidation.value = null
  analysisError.value = ''
  audioChunks = []
  voiceDetected.value = false
  requestMicAndCheck()
}

const confirmRecordAgain = () => { showRecordAgainAlert.value = false; doRecordAgain() }
const cancelRecordAgain  = () => { showRecordAgainAlert.value = false }

// ── Audio validation

// Convert Float32Array audio data to 16-bit PCM and write to DataView
const floatTo16BitPcm = (view, offset, input) => {
  for (let i = 0; i < input.length; i++, offset += 2) {
    const sample = Math.max(-1, Math.min(1, input[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
  }
}

// Write ASCII string to DataView at specified offset
const writeString = (view, offset, value) => {
  for (let i = 0; i < value.length; i++) {
    view.setUint8(offset + i, value.charCodeAt(i))
  }
}

// Convert AudioBuffer to WAV Blob (mono mixdown, 16-bit PCM)
const audioBufferToWavBlob = (audioBuffer) => {
  const channelCount = audioBuffer.numberOfChannels
  const sampleRate = audioBuffer.sampleRate
  const length = audioBuffer.length
  const mono = new Float32Array(length)

  for (let channel = 0; channel < channelCount; channel++) {
    const data = audioBuffer.getChannelData(channel)
    for (let i = 0; i < length; i++) mono[i] += data[i] / channelCount
  }

  const buffer = new ArrayBuffer(44 + mono.length * 2)
  const view = new DataView(buffer)
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + mono.length * 2, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(view, 36, 'data')
  view.setUint32(40, mono.length * 2, true)
  floatTo16BitPcm(view, 44, mono)

  return new Blob([view], { type: 'audio/wav' })
}

const getRecordedWavBlob = async () => {
  if (recordedWavBlob.value) return recordedWavBlob.value
  if (!recordedAudioBlob.value) throw new Error('No recording is available.')

  const AudioCtx = window.AudioContext || window['webkitAudioContext']
  const ctx = new AudioCtx()
  const audioBuffer = await ctx.decodeAudioData(await recordedAudioBlob.value.arrayBuffer())
  const wavBlob = audioBufferToWavBlob(audioBuffer)
  await ctx.close()
  recordedWavBlob.value = wavBlob
  return wavBlob
}

// Send recorded WAV blob to backend for validation
const validateRecordedVoiceSample = async () => {
  try {
    const wavBlob = await getRecordedWavBlob()
    const formData = new FormData()
    formData.append('file', wavBlob, 'voice-sample.wav')

    const response = await fetch(`${API_BASE_URL}/api/voice/validate`, {
      method: 'POST',
      body: formData,
    })

    const result = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(result?.detail || 'Voice validation API failed.')
    }

    lastVoiceValidation.value = result
    console.log('[voice-validation]', result)
    return Boolean(result.accepted)
  } catch (err) {
    // backend not available yet — fall through so recording flow is not blocked
    lastVoiceValidation.value = { accepted: true, error: err?.message || 'Could not validate voice sample.' }
    console.log('[voice-validation-error]', lastVoiceValidation.value)
    return true
  }
}

const analyzeVoice = async () => {
  if (!voiceDetected.value) return

  analysisError.value = ''

  try {
    const wavBlob = await getRecordedWavBlob()
    setPendingVoiceAnalysisInput({
      wavBlob,
    })
    router.push({ name: 'analysis' })
  } catch (err) {
    analysisError.value = err?.message || 'Could not analyze voice sample.'
  }
}

// ── Noise during recording
const handleNoiseDuringRec = () => {
  if (recordingStatus.value !== 'recording') return
  noiseDuringRecordingDetected = true
  recordingWasCancelled        = true
  clearInterval(countdownInterval)
  stopLiveWaveform()
  audioStream?.getTracks().forEach((t) => t.stop())
  audioStream = null
  if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop()
  recordingStatus.value         = 'not_ready'
  showNoiseDuringRecAlert.value = true
}

// ── Noise modal
const retryAfterNoise          = async () => { showNoiseAlert.value = false; await requestMicAndCheck() }
const dismissNoiseAlert        = ()        => { showNoiseAlert.value = false }
const retryAfterNoiseDuringRec = async () => { showNoiseDuringRecAlert.value = false; await requestMicAndCheck() }
const cancelNoiseDuringRec     = ()        => { showNoiseDuringRecAlert.value = false; requestMicAndCheck() }
const confirmLeave = () => {
  showLeaveAlert.value = false
  recordingWasCancelled = true
  clearInterval(countdownInterval)
  stopLiveWaveform()
  audioStream?.getTracks().forEach((t) => t.stop())
  audioStream = null
  if (mediaRecorder?.state !== 'inactive') mediaRecorder?.stop()
  audioChunks = []
  if (pendingNavNext) { pendingNavNext(); pendingNavNext = null }
}
const cancelLeave  = () => {
  showLeaveAlert.value = false
  if (recordingStatus.value === 'recording') {
    countdownInterval = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) { clearInterval(countdownInterval); stopRecording() }
    }, 1000)
  }
  if (pendingNavNext) { pendingNavNext(false); pendingNavNext = null }
}

// ── Lifecycle
const isRecordingActive = () =>
  recordingStatus.value === 'recording' || recordingStatus.value === 'waiting_voice'

const handleBeforeUnload = (e) => {
  if (isRecordingActive()) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onBeforeRouteLeave((_to, _from, next) => {
  if (isRecordingActive()) {
    pendingNavNext = next
    clearInterval(countdownInterval)
    showLeaveAlert.value = true
  } else {
    next()
  }
})

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  requestMicAndCheck()
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  clearInterval(sampleInterval)
  clearInterval(countdownInterval)
  clearInterval(playbackInterval)
  stopLiveWaveform()
  if (sampleAudio)   { sampleAudio.pause(); sampleAudio = null }
  if (playbackAudio) { playbackAudio.pause(); playbackAudio = null }
  audioStream?.getTracks().forEach((t) => t.stop())
  if (recordedAudioUrl.value) URL.revokeObjectURL(recordedAudioUrl.value)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Page ── */
.recording-page {
  font-family: 'Poppins', sans-serif;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: linear-gradient(180deg, #eef2ff 0%, #e8eeff 50%, #eff3ff 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 32px 0;
}

.page-inner {
  flex: 1;
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 0 0;
}

/* ── Topbar (fixed top-left) ── */
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
  padding: 7px 16px;
  border: 1px solid rgba(101, 148, 228, 0.4);
  border-radius: 20px;
  background: white;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #6594e4;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}
.btn-back:hover { opacity: 0.75; }
.back-arrow { font-size: 15px; line-height: 1; transform: translateY(-1px); display: inline-block; }

/* DEFAULT VIEW (ready / not_ready / checking) */

/* ── Status badge ── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 16px;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-size: 13px;
  font-weight: 600;
  color: #444;
  white-space: nowrap;
  margin-bottom: 14px;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.status-not-ready          { color: #aaa; }
.status-not-ready .status-dot  { background: #ccc; }

.status-checking           { color: #6594e4; }
.status-checking .status-dot   { background: #6594e4; animation: blink 1.1s ease-in-out infinite; }

.status-ready              { color: #5C7BAF; }
.status-ready .status-dot      { background: #34c759; animation: blink 1.4s ease-in-out infinite; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.15; }
}

/* ── Header ── */
.page-title { font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 10px; text-align: center; }
.page-subtitle { font-size: 14px; color: #666; text-align: center; margin-bottom: 22px; line-height: 1.6; }
.highlight { color: #6594e4; font-weight: 600; }

/* ── Recording card ── */
.recording-card {
  width: 100%;
  background: white;
  border-radius: 24px;
  padding: 24px 28px 22px;
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 22px;
}

.card-mic-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(137deg, #6594e4 6.18%, #95b9f7 94.01%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  box-shadow: 0 4px 16px rgba(101, 148, 228, 0.3);
}
.card-label { font-size: 13px; font-weight: 500; color: #666; margin-bottom: 14px; text-align: center; }

/* ── Audio player (shared by sample + complete view) ── */
.audio-player {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #eef2ff;
  border-radius: 40px;
  padding: 10px 18px 10px 10px;
  margin-bottom: 20px;
  cursor: pointer;
  user-select: none;
  align-self: center;
}
.audio-player.player-playing { cursor: default; }
.complete-player { cursor: default; margin-bottom: 0; }

.play-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6da8f5, #5c8ee0);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s;
  padding-left: 2px;
}
.play-btn:disabled { cursor: default; padding-left: 0; }
.play-btn:not(:disabled):hover { opacity: 0.85; }

.sound-bars { display: flex; align-items: flex-end; gap: 2px; height: 14px; }
.sound-bars span {
  width: 3px; background: white; border-radius: 2px;
  animation: sound-bar 0.75s ease-in-out infinite;
}
.sound-bars span:nth-child(1) { height: 6px;  animation-delay: 0s; }
.sound-bars span:nth-child(2) { height: 12px; animation-delay: 0.18s; }
.sound-bars span:nth-child(3) { height: 8px;  animation-delay: 0.36s; }
@keyframes sound-bar {
  0%, 100% { transform: scaleY(0.45); }
  50%       { transform: scaleY(1); }
}

.waveform {
  display: flex; align-items: center; gap: 1.5px; height: 44px; width: 200px;
}
.waveform-bar {
  flex: 1; min-width: 2px; max-width: 5px; border-radius: 3px; background: #93b4e8; transition: background 0.1s;
}
.waveform-bar.played { background: #6594e4; }
.audio-duration { font-size: 12px; font-weight: 600; color: #6594e4; flex-shrink: 0; }

/* ── Instructions ── */
.instructions {
  width: 100%; background: #f4f7ff; border-radius: 16px; padding: 14px 20px;
  display: flex; flex-direction: column; gap: 12px;
}
.instr-item { display: flex; align-items: center; gap: 14px; }
.instr-num {
  width: 28px; height: 28px; border-radius: 50%; background: white;
  border: 1px solid rgba(101, 148, 228, 0.25); display: flex; align-items: center;
  justify-content: center; font-size: 13px; font-weight: 600; color: #6594e4; flex-shrink: 0;
}
.instr-text { font-size: 13px; font-weight: 500; color: #555; }

/* ── Noise-during-recording card ── */
.noise-rec-card {
  width: 100%; display: flex; align-items: flex-start; gap: 10px;
  background: #fffbf0; border: 1px solid rgba(255, 159, 10, 0.35);
  border-radius: 14px; padding: 14px 16px; margin-bottom: 16px;
}
.noise-rec-text { font-size: 13px; font-weight: 500; color: #b87000; line-height: 1.55; }

/* ── Error card ── */
.error-card {
  width: 100%; display: flex; align-items: flex-start; gap: 10px;
  background: #fff6f6; border: 1px solid rgba(232, 69, 69, 0.2);
  border-radius: 14px; padding: 14px 16px; margin-bottom: 16px;
}
.error-icon { flex-shrink: 0; margin-top: 1px; }
.error-text { font-size: 13px; font-weight: 500; color: #c92020; line-height: 1.55; }

/* ── Start Recording button ── */
.btn-record {
  width: 100%; max-width: 360px;
  display: flex; align-items: center; justify-content: center; gap: 10px;
  padding: 14px 28px;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: white; border: none; border-radius: 40px;
  font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: opacity 0.2s, transform 0.1s;
  margin-bottom: 20px;
  box-shadow: 0 4px 16px rgba(101, 148, 228, 0.35);
}
.btn-record:hover:not(:disabled) { opacity: 0.88; }
.btn-record:active:not(:disabled) { transform: scale(0.98); }
.btn-record.is-not-ready {
  background: linear-gradient(102deg, #c5d5f0, #a0b8e0); box-shadow: none; cursor: not-allowed; opacity: 0.7;
}
.btn-record.is-busy {
  background: linear-gradient(102deg, #c8cdd6, #b0b6c0); box-shadow: none; cursor: not-allowed;
  animation: btn-blink-gray 1s ease-in-out infinite;
}
@keyframes btn-blink-gray {
  0%, 100% { opacity: 0.8; }
  50%       { opacity: 0.4; }
}
.btn-mic-img { width: 22px; height: 22px; flex-shrink: 0; }

/* ── Main card (recording + complete views) ── */
.main-card {
  width: 100%;
  background: white;
  border-radius: 24px;
  padding: 32px 28px 28px;
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* WAITING FOR VOICE VIEW */
.status-badge-waiting {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 18px; border-radius: 20px;
  border: 1.5px solid rgba(101, 148, 228, 0.45);
  background: white; font-size: 13px; font-weight: 600; color: #6594e4;
  white-space: nowrap; margin-bottom: 20px;
}
.dot-waiting {
  width: 8px; height: 8px; border-radius: 50%; background: #6594e4; flex-shrink: 0;
  animation: blink 0.9s ease-in-out infinite;
}
.waiting-title {
  font-size: 20px; font-weight: 700; color: #1a1a2e;
  text-align: center; margin-bottom: 10px;
}
.waiting-hint {
  font-size: 14px; font-weight: 400; color: #666;
  text-align: center; margin-bottom: 28px; line-height: 1.6;
}

/* VALIDATING RECORDING VIEW */
.status-badge-validating {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 18px; border-radius: 20px;
  border: 1.5px solid rgba(101, 148, 228, 0.45);
  background: white; font-size: 13px; font-weight: 600; color: #6594e4;
  white-space: nowrap; margin-bottom: 28px;
}
.dot-validating {
  width: 8px; height: 8px; border-radius: 50%; background: #6594e4; flex-shrink: 0;
  animation: blink 0.9s ease-in-out infinite;
}
.validation-loader {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 24px;
  box-shadow: inset 0 0 0 1px rgba(101, 148, 228, 0.18);
}
.validation-loader span {
  width: 8px;
  height: 34px;
  border-radius: 6px;
  background: linear-gradient(180deg, #95B9F7, #6594E4);
  animation: validation-pulse 0.9s ease-in-out infinite;
}
.validation-loader span:nth-child(2) { animation-delay: 0.12s; }
.validation-loader span:nth-child(3) { animation-delay: 0.24s; }
@keyframes validation-pulse {
  0%, 100% { transform: scaleY(0.45); opacity: 0.55; }
  50% { transform: scaleY(1); opacity: 1; }
}
.validating-title {
  font-size: 28px; font-weight: 800; color: #1a1a2e;
  text-align: center; margin-bottom: 10px;
}
.validating-subtitle {
  font-size: 14px; font-weight: 500; color: #666;
  text-align: center; line-height: 1.6; max-width: 390px;
}

/* RECORDING IN PROGRESS VIEW*/
.status-badge-recording {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 18px; border-radius: 20px;
  border: 1.5px solid rgba(232, 69, 69, 0.45);
  background: white; font-size: 13px; font-weight: 600; color: #c92020;
  white-space: nowrap; margin-bottom: 30px;
}
.dot-recording {
  width: 8px; height: 8px; border-radius: 50%; background: #ff3b30; flex-shrink: 0;
  animation: blink 0.7s ease-in-out infinite;
}

.countdown-display { display: flex; flex-direction: column; align-items: center; margin-bottom: 28px; }
.countdown-number {
  font-size: 100px; font-weight: 700; line-height: 1;
  background: linear-gradient(135deg, #95B9F7, #6594E4);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}
.countdown-label { font-size: 18px; font-weight: 500; color: #555; }

.live-waveform-wrap {
  display: flex; align-items: center; gap: 4px;
  width: 100%; max-width: 460px; height: 120px;
  justify-content: center; margin-bottom: 28px;
}
.live-bar {
  width: 8px; background: linear-gradient(to bottom, #95B9F7, #6594E4);
  border-radius: 4px; min-height: 8px; transition: height 0.06s ease;
}

.btn-cancel {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 14px 36px;
  background: linear-gradient(102deg, #ff7b7b, #e84545);
  color: white; border: none; border-radius: 40px;
  font-family: 'Poppins', sans-serif; font-size: 15px; font-weight: 600;
  cursor: pointer; transition: opacity 0.2s;
  box-shadow: 0 4px 16px rgba(232, 69, 69, 0.35);
}
.btn-cancel:hover { opacity: 0.88; }
.btn-cancel-img { width: 20px; height: 20px; flex-shrink: 0; }

/* RECORDING COMPLETE VIEW*/
.complete-check-img {
  width: 88px; height: 88px; object-fit: contain;
  margin-bottom: 28px;
}
.complete-title {
  font-size: 34px; font-weight: 800; color: #1a1a2e;
  margin-bottom: 12px; text-align: center;
}
.complete-subtitle {
  font-size: 15px; font-weight: 500; color: #666;
  text-align: center; margin-bottom: 28px;
}
.complete-audio-card {
  display: inline-flex;
  background: white;
  border-radius: 20px;
  padding: 16px 20px;
  box-shadow: 0 4px 20px rgba(101, 148, 228, 0.12);
  margin-bottom: 28px;
  align-self: center;
}


.complete-actions {
  display: flex; gap: 14px; flex-wrap: wrap; justify-content: center;
  margin-top: 0;
}
.error-reasons {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.error-reason-item {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #fff5f5;
  border: 1px solid #fca5a5;
  border-radius: 50px;
  padding: 10px 16px;
}
.error-reason-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1.5px solid #ef4444;
  color: #ef4444;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.error-reason-text {
  font-size: 13px;
  font-weight: 500;
  color: #ef4444;
}
.btn-analyze {
  padding: 12px 32px;
  background: linear-gradient(102deg, #95b9f7, #6594e4);
  color: white; border: none; border-radius: 40px;
  font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; box-shadow: 0 4px 16px rgba(101, 148, 228, 0.3);
  transition: opacity 0.2s;
}
.btn-analyze:hover { opacity: 0.88; }
.btn-record-again {
  padding: 12px 32px;
  background: transparent; color: #6594e4;
  border: 1.5px solid #6594e4; border-radius: 40px;
  font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.2s;
}
.btn-record-again:hover { background: rgba(101, 148, 228, 0.06); }

/* NOISE ALERT MODAL*/
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center; z-index: 999;
}
.modal-card {
  background: white; border-radius: 24px; padding: 32px 28px;
  max-width: 360px; width: 90%; display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
}
.modal-icon-wrap { margin-bottom: 16px; }
.modal-title { font-size: 17px; font-weight: 700; color: #1a1a2e; margin-bottom: 10px; text-align: center; }
.modal-desc { font-size: 13px; color: #666; text-align: center; line-height: 1.6; margin-bottom: 24px; }
.modal-btn {
  width: 100%; padding: 12px;
  background: linear-gradient(102deg, #95b9f7, #6594e4);
  color: white; border: none; border-radius: 14px;
  font-family: 'Poppins', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; margin-bottom: 10px;
}
.modal-btn-red { background: linear-gradient(102deg, #ff7b7b, #e84545); }
.sample-error-text { font-size: 12px; color: #e53935; text-align: center; margin-top: -8px; margin-bottom: 8px; }
.modal-leave-icon { width: 56px; height: 56px; object-fit: contain; margin-bottom: 16px; }
.modal-dismiss {
  background: none; border: none; color: #aaa;
  font-family: 'Poppins', sans-serif; font-size: 13px; cursor: pointer;
}
.modal-dismiss:hover { color: #888; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* ── Disclaimer ── */
.disclaimer {
  font-size: 13px; font-weight: 500; color: #aaa;
  text-align: center;
  padding: 8px 16px 14px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── Responsive ── */
@media (max-width: 600px) {
  .disclaimer { white-space: normal; font-size: 11px; }
}
@media (max-width: 480px) {
  .recording-page { padding: 24px 16px 0; }
  .page-topbar { top: 16px; left: 16px; }
  .btn-back { font-size: 12px; padding: 6px 20px; }
  .back-arrow { transform: translateY(-2px); }
  .recording-card { padding: 24px 20px 20px; }
  .page-title { font-size: 22px; }
  .btn-record { max-width: 100%; font-size: 14px; }
  .countdown-number { font-size: 80px; }
  .complete-title { font-size: 26px; }
}
</style>
