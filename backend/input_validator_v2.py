"""Backend production candidate: canonical waveform + composite evidence."""
from __future__ import annotations
import math
import numpy as np
from scipy.signal import resample_poly
import input_validator as iv
from audio_normalizer import normalize_for_voice_analysis
from validator_config import DEFAULT_CONFIG

CANONICAL_ANALYSIS_SR=DEFAULT_CONFIG.canonical_sr; LOW_RMS_THRESHOLD=DEFAULT_CONFIG.low_rms_threshold
TEMPORAL_EVIDENCE_REQUIRED=DEFAULT_CONFIG.temporal_evidence_required

def _resample(samples,sr):
 if sr==CANONICAL_ANALYSIS_SR:return samples.astype(np.float32)
 g=math.gcd(sr,CANONICAL_ANALYSIS_SR);return resample_poly(samples,CANONICAL_ANALYSIS_SR//g,sr//g).astype(np.float32)
def preprocess(audio):
 dc=float(np.mean(audio.samples));x=_resample(audio.samples,audio.sample_rate);x=x-float(np.mean(x))
 return iv.AudioData(x.astype(np.float32),CANONICAL_ANALYSIS_SR),{'native_sr':audio.sample_rate,'analysis_sr':CANONICAL_ANALYSIS_SR,'raw_duration':len(audio.samples)/audio.sample_rate,'raw_peak':float(np.max(np.abs(audio.samples))),'dc_offset_before':dc,'dc_offset_after':float(np.mean(x))}
def _speech_evidence(audio):
 frames=iv._frame_audio_np(audio);rms=np.sqrt(np.mean(frames**2,axis=1));gate=max(iv._percentile_exact(rms,.55)*.55,.008);vf=frames[rms>=gate]
 if len(vf)==0:vf=np.zeros((1,frames.shape[1]))
 vf=vf[::2];z=np.sum((vf[:,:-1]>=0)!=(vf[:,1:]>=0),axis=1)/max(vf.shape[1]-1,1)
 fs=np.array([120,180,260,350,500,700,900,1100,1400,1800,2300,3000,3800,5000,6500]);fs=fs[fs<CANONICAL_ANALYSIS_SR/2];p=iv._dft_powers(vf,CANONICAL_ANALYSIS_SR,fs);total=p.sum(1)+1e-12;rat=p/total[:,None]
 high=p[:,fs>=1800].sum(1)/total;con=p[:,fs>=2300].sum(1)/total;music=p[:,fs>=1400].sum(1)/total;entropy=-np.sum(rat*np.log(rat+1e-12),1)/math.log(len(fs));cent=(p*fs).sum(1)/total
 flags={'zcr':z>.13,'high_ratio':high>.38,'consonant_ratio':con>.24,'music_band':music>.42,'entropy':entropy>.72,'centroid':cent>1900}; count=sum(v.astype(int) for v in flags.values())
 return flags,count
def validate_sustained_ah(audio, temporal_required=TEMPORAL_EVIDENCE_REQUIRED, vowel_required=None, trigger_required=DEFAULT_CONFIG.speech_frame_trigger_count):
 norm=normalize_for_voice_analysis(audio.samples,audio.sample_rate);a=iv.AudioData(norm.audio,norm.sample_rate);meta={'native_sr':norm.native_sample_rate,'analysis_sr':norm.analysis_sample_rate,'raw_duration':len(audio.samples)/audio.sample_rate,'raw_peak':float(np.max(np.abs(audio.samples))),'dc_offset_before':norm.dc_offset_before,'dc_offset_after':norm.dc_offset_after};gain=norm.applied_gain;limited=norm.low_rms_rescue_limited
 m=iv.validate_sustained_ah(a)
 # Backend v1 exposed spectral-prefixed centroid names; normalize that schema
 # internally so the candidate can coexist without changing v1's API.
 m.setdefault('centroid_median',m.get('spectral_centroid_median',0.0))
 m.setdefault('centroid_cv',m.get('spectral_centroid_cv',0.0))
 flags,count=_speech_evidence(a)
 structural={'duration':m['duration_sec']<3,'voiced_ratio':m['voiced_ratio']<.8,'voiced_duration':m['voiced_duration_sec']<2.8,'onset':m['onset_count']>3,'gap':m['gap_count']>5,'pitch_coverage':m['pitch_coverage']<.35}
 temporal={'envelope':m['envelope_peak_count']>7 or m['envelope_modulation']>.75,'zcr':m['zcr_median']>.18 or m['zcr_std']>.07,'spectral_speech_like':float((count>=trigger_required).mean())>.12,'mfcc':m['mfcc_delta_mean']>.28 or m['mfcc_delta_p90']>.72 or m['mfcc_unstable_ratio']>.22,'vowel_shape_change':m['centroid_jumps']>7 and m['centroid_cv']>.35}
 # `music_band_ratio` is energy >=1400 Hz, not a direct music detector; a
 # held vowel may legitimately occupy that band.  Require corroboration.
 quality={'high_consonant':m['high_ratio_p90']>.55 or m['consonant_ratio_p90']>.35,'music_band_high':m['music_band_ratio_p90']>.48,'high_entropy':m['spectral_entropy_p90']>.78,'mixed_texture':m['mfcc_std_mean']>1.1 and m['spectral_entropy_median']>.52}
 quality_background_count=sum(quality[k] for k in ('music_band_high','high_entropy','mixed_texture'))
 # Both legacy vowel predicates root in weak 500–1100 Hz energy. They form one
 # static-identity family, never two independent votes.
 resonance_very_weak=m['vowel_band_ratio_median']<.015
 vowel={'resonance_very_weak':resonance_very_weak,'centroid_too_high_for_weak_resonance':m['centroid_median']>1200,'hum_like_low_centroid':m['centroid_median']<220 and m['pitch_stability']<.03,'static_vowel_identity_suspicious':resonance_very_weak and (m['centroid_median']>1200 or (m['centroid_median']<220 and m['pitch_stability']<.03))}
 reasons=[]
 labels=[('duration','Audio is too short.'),('voiced_ratio','The voiced part is not continuous enough.'),('voiced_duration','Voiced duration is too short.'),('onset','Repeated syllable-like attacks were detected.'),('gap','The voice has too many gaps.'),('pitch_coverage','Not enough voiced pitch was detected.')]
 reasons += [text for key,text in labels if structural[key]]
 if quality['high_consonant']:reasons.append('Too much high-frequency consonant-like energy was detected.')
 if quality_background_count>=DEFAULT_CONFIG.quality_background_evidence_required:reasons.append('Broadband background audio was detected behind the voice.')
 if sum(temporal.values())>=temporal_required:reasons.append('The sound changes too much to be one sustained Ah vowel.')
 # Static spectral identity is diagnostic-only until an independent content
 # family is calibrated; do not double-count vowel-band-derived predicates.
 if m['voiced_rms_median']<LOW_RMS_THRESHOLD:reasons.append('Voice level is too weak.')
 meta.update(applied_gain=float(gain),low_rms_rescue_used=norm.low_rms_rescue_used,low_rms_rescue_limited=limited,low_rms_rescue_unmet=norm.low_rms_rescue_unmet)
 metrics={key:value for key,value in m.items() if key not in ('accepted','reasons')}
 return {'accepted':not reasons,'passed':not reasons,'reasons':reasons,'preprocessing':meta,'metrics':metrics,'evidence':{'structural':structural,'quality':quality,'temporal':temporal,'vowel_identity':vowel,'speech_like_components':{k:float(v.mean()) for k,v in flags.items()}},'scores':{'temporal_evidence_count':sum(temporal.values()),'vowel_identity_evidence_count':int(vowel['static_vowel_identity_suspicious']),'quality_background_evidence_count':quality_background_count,'speech_like_ratio_ge2':float((count>=trigger_required).mean())}}
def validate_content(content): return validate_sustained_ah(iv.read_wav_mono(content))
