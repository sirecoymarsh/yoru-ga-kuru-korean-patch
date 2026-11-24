"""Review-bound live installation. Only the handed-off, unmodified AIN is installed."""
from pathlib import Path
import sys,json,shutil,datetime
sys.dont_write_bytecode=True
D=Path(r'P:\AI\Codex\projects\YoruGaKuru_flowchart_20260922\ingame\r15_calendar')
R=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import r15lib as L
import publish_calendar_r15 as p
H='d81ddd5ad383ef870f96eca0c4da763a6cf475445d71f029ffb1f2c692037963'
assert L.sha(D/'candidate/NightRemaster.ain')==H
vm=L.readj(R/'work/build/vm_verification_selftest.json')
assert vm['candidate_sha256']==H and vm['saves_checked']==51 and all(x['caught'] for x in vm['planted_defects'])
native_path=R/'native_config/config_complete/result.json';native=L.readj(native_path)
assert native.get('exit_code')==0 and native['log'][-1]=='END' and native['candidate_sha256']==H
assert native['user_save_folder_unchanged'] and not native.get('vm_error') and not native.get('message') and not native['events']
assert any(x.startswith('CONFIG REQUEST STILL DEFERRED') for x in native['log'])
assert L.readj(R/'transaction_fixture.json')['payload']=={'NightRemaster.ain':H}
review=dict(status='APPROVED_FOR_LIVE_INSTALL',reviewer='Codex internal',time=datetime.datetime.now().astimezone().isoformat(),candidate_sha256=H,
 implementation_author=L.AUTHOR,source_changes=0,vm=vm['counts'],planted_defects_caught=len(vm['planted_defects']),
 native_settings_replay={'result':str(native_path),'sha256':L.sha(native_path),'passed':True,'audio':'muted','private_save_folder':native['save_folder']},
 native_home_panel_replay={'result':str(D/'증거/probe_result.json'),'sha256':L.sha(D/'증거/probe_result.json'),'author':L.AUTHOR,'screens_reviewed':True},
 findings=[{'id':'CAL-REVIEW-001','severity':'minor','detail':'Publisher references source/manifest.json but did not copy candidate manifest there; install adapter supplies the exact candidate manifest.'}],
 limitations=['No exhaustive native replay of all 1164 events; native replay representative E30160 only. Choice chains and battle preserve the game implementation and have static review, not native completion evidence.',
 'Native scripted callbacks exercised; physical mouse hit testing is not claimed.',
 'Replay writes read/seen state and can raise affinity in the current playthrough. Replay-created saves require the pinned new function frames.'],
 harness_notes=['An initial isolated check opened index 8 (debug page); actual Mods index 9 verified in original builder. This was a test driver issue, not a candidate change.',
 'Confirmed the reservation notice through the original C_MessageDialog input polling call (KR_ExploreLevelEnter); removed unnecessary legacy callback redirects before the final successful run.'],
 visual_review=['Fable cal_month/cal_lane/cal_card: Korean glyphs and layout fit 1280x720; independent settings route screenshots reviewed.'],
 restore_command='python "'+str(D/'publish_calendar_r15.py')+'" --restore')
L.writej(R/'review.json',review)
draft=L.readj(D/'required_calendar_r15.json');draft['codex_independent_review']={'report':str(R/'review.json'),'sha256':L.sha(R/'review.json'),'candidate_sha256':H,'native_settings_replay':True}
p.DRAFT=R/'required_calendar_r15.json';L.writej(p.DRAFT,draft)
before=p.snapshot_saves();base_contracts={x.name:L.readj(x) for x in L.CODEX.glob('required_*.json')}
p.install()
assert (p.E/'journal.json').exists() and L.readj(p.E/'journal.json')['status']=='COMMITTED'
# Complete the source reference already emitted by the original publisher.
shutil.copy2(D/'candidate/manifest.json',p.E/'source/manifest.json')
for name in ['review.json','install_review.py','verify_review.py','native_review.py','native_page9.py','native_config_complete.py','native_notice_confirm.py']:
 shutil.copy2(R/name,p.E/'source'/('codex_'+name))
ptr=L.readj(L.CURRENT);rt=Path(ptr['runtime']);manifest=L.readj(Path(ptr['manifest']))
assert L.sha(rt/'NightRemaster.ain')==H and L.sha(Path(ptr['manifest']))==ptr['manifest_sha256']
p.exact_tree(rt,manifest['files'])
for name,old in base_contracts.items():
 now=L.readj(L.CODEX/name)
 assert now.get('instruction')==old.get('instruction'),name
 assert now['calendar_r15_preserved_by']==str(p.E),name
 for f,h in now.get('required_files',{}).items():
  if (rt/f).is_file(): assert L.sha(rt/f)==h,(name,f)
assert p.snapshot_saves()==before
post=dict(status='INSTALLED_AND_POSTCHECK_PASS',candidate_sha256=H,manifest_sha256=ptr['manifest_sha256'],user_save_files_unchanged=len(before),prior_contracts_preserved=len(base_contracts),runtime=str(rt),external_backup=str(p.E/'before'))
L.writej(R/'post_install.json',post);shutil.copy2(R/'post_install.json',p.E/'codex_post_install.json')
(R/'README.md').write_text('# 이벤트 달력 r15 검수·설치\n\n설치 완료. 후보 원본 AIN 그대로 사용; 게임 데이터 수정 파일 1개.\n\n- 모드 → 플레이 정보 → 캐릭터별 남은 이벤트 → 이벤트 달력\n- 거점 캐릭터 이름 클릭 → 달력으로 보기\n- 기존 저장 51개 / 복귀 지점 1,255개 호환, 2,388개 메뉴 상태 및 13개 결함 주입 검사 통과.\n- 별도 음소거 사본에서 설정 창의 실제 Mods 버튼 → 달력 → 예약 안내 → 설정 종료 → 재생 21메시지 → 거점 복귀 확인.\n- 설치 전후 사용자 저장 파일 '+str(len(before))+'개 동일.\n\n재생은 현재 플레이의 읽음·이벤트 기록 및 일부 친밀도에 반영된다. 전 이벤트의 선택지·전투를 실기로 전수 재생한 것은 아니다.\n\n보고서: review.json / post_install.json. 원복: '+review['restore_command']+'\n',encoding='utf8')
print(json.dumps(post,ensure_ascii=False,indent=2))
