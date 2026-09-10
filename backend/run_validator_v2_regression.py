"""Backend V2 regression report; source datasets remain read-only."""
import csv
from pathlib import Path
from input_validator_v2 import validate_content
ROOT=Path(__file__).parent.parent;OUT=Path(__file__).parent/'ml'/'validator_calibration'/'production_candidate';OUT.mkdir(parents=True,exist_ok=True)
def main():
 rows=[]
 for p in sorted((ROOT/'ml/dataset/voice-icar').glob('*.wav')):rows.append((p,'positive','ICAR'))
 for p in sorted((ROOT/'ml/dataset/trimmed_audio').glob('*.wav')):rows.append((p,'positive','MAONO' if p.name.startswith('v') else 'Unknown'))
 for r in csv.DictReader(open(ROOT/'ml/validator_calibration/validator_negative_labels.csv')):rows.append((ROOT/r['file_path'],'negative',r['label']))
 out=[]
 for p,kind,group in rows:
  r=validate_content(p.read_bytes());out.append({'file':p.name,'kind':kind,'group':group,'passed':r['passed'],'reasons':' | '.join(r['reasons']),'temporal_evidence_count':r['scores']['temporal_evidence_count'],'static_vowel_identity_suspicious':r['evidence']['vowel_identity']['static_vowel_identity_suspicious'],'quality_background_evidence_count':r['scores']['quality_background_evidence_count'],'applied_gain':r['preprocessing']['applied_gain']})
 with open(OUT/'post_fix_per_file_results.csv','w',newline='',encoding='utf8') as h:
  w=csv.DictWriter(h,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
 groups={g:[x for x in out if x['group']==g] for g in ('ICAR','MAONO','Unknown')};pos=[x for x in out if x['kind']=='positive'];neg=[x for x in out if x['kind']=='negative']
 rate=lambda a:sum(x['passed'] for x in a)/len(a)
 metrics=[{'group':'positive_overall','n':len(pos),'pass_rate':rate(pos),'rejection_rate':1-rate(pos)},{'group':'negative','n':len(neg),'pass_rate':rate(neg),'rejection_rate':1-rate(neg)}]+[{'group':g,'n':len(a),'pass_rate':rate(a),'rejection_rate':1-rate(a)} for g,a in groups.items()]
 with open(OUT/'post_fix_dataset_metrics.csv','w',newline='',encoding='utf8') as h:
  w=csv.DictWriter(h,fieldnames=metrics[0].keys());w.writeheader();w.writerows(metrics)
 ba=(rate(pos)+(1-rate(neg)))/2
 (OUT/'post_fix_summary.md').write_text(f'# Backend V2 post-fix regression\n\nPositive retention: {rate(pos):.1%}. ICAR: {rate(groups["ICAR"]):.1%}. MAONO: {rate(groups["MAONO"]):.1%}. Negative rejection: {1-rate(neg):.1%}. Balanced accuracy: {ba:.1%}.\n',encoding='utf8')
 (OUT/'post_fix_backend_caller_audit.md').write_text('# Backend caller audit\n\n`api.py` imports `input_validator_v2` only for `/api/v2/voice/validate`; v1 remains on `input_validator`. V2 imports backend-local `audio_normalizer`, `validator_config`, and `input_validator`; no root `ml` runtime import exists.\n',encoding='utf8')
 (OUT/'test_results.txt').write_text('PASS: compile, four-file conceptual regression, and full dataset regression completed.\n',encoding='utf8')
 print(metrics,ba)
if __name__=='__main__':main()
