let pendingVoiceAnalysisInput = null

export const setPendingVoiceAnalysisInput = (input) => {
  pendingVoiceAnalysisInput = input
}

export const takePendingVoiceAnalysisInput = () => {
  const input = pendingVoiceAnalysisInput
  pendingVoiceAnalysisInput = null
  return input
}
