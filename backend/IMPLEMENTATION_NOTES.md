# VocaSense Pipeline Notes

Current flow:
1. Frontend records audio and converts it to WAV.
2. `POST /api/voice/analyze` receives the WAV file.
3. `controller.py` writes a temporary raw WAV file.
4. noisereduce creates a denoised WAV file.
5. `feature_extractor.py` extracts acoustic features from the denoised file.
6. API returns step status, timing, and feature JSON to the frontend.

Next steps:
- Add model inference after feature extraction.
- Add result scoring and explanation text.
- Save each step to Supabase:
  - raw WAV in a `voice-recordings/raw` storage path.
  - denoised WAV in a `voice-recordings/denoised` storage path.
  - feature JSON, step status, timings, model output, and user id in a `voice_analysis_runs` table.
- Add cleanup/error statuses so failed runs are visible in Supabase.
