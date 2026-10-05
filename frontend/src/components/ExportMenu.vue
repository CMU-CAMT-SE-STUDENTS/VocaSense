<template>
  <div class="export-menu" ref="rootEl">
    <button type="button" class="export-trigger" :disabled="disabled || busy" @click="open = !open">
      <svg viewBox="0 0 24 24" fill="none"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      {{ busy ? 'Exporting…' : label }}
    </button>
    <div v-if="open" class="export-options">
      <button type="button" class="export-option" @click="choose('pdf')">Save as PDF</button>
      <button type="button" class="export-option" @click="choose('png')">Save as PNG</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

defineProps({
  disabled: Boolean,
  busy: Boolean,
  label: { type: String, default: 'Export' }
})
const emit = defineEmits(['export'])

const open = ref(false)
const rootEl = ref(null)

function choose(format) {
  open.value = false
  emit('export', format)
}

const onDocClick = (e) => {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<style scoped>
.export-menu { position: relative; }

.export-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(101, 148, 228, 0.25);
  background: #fff;
  border-radius: 16px;
  padding: 8px 14px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
  white-space: nowrap;
}
.export-trigger svg { width: 14px; height: 14px; }
.export-trigger:hover:not(:disabled) { background: #f4f7ff; }
.export-trigger:disabled { opacity: 0.6; cursor: not-allowed; color: #8a94a8; }

.export-options {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 100%;
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(101, 148, 228, 0.15);
  box-shadow: 0 10px 28px rgba(38, 60, 110, 0.16);
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 40;
}

.export-option {
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 8px 12px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 500;
  color: #444;
  text-align: left;
  white-space: nowrap;
  cursor: pointer;
}
.export-option:hover { background: #f4f7ff; color: #6594e4; }
</style>
