"""Reuse the proven calendar build/probe/install pipeline for the narrow context revision."""
from pathlib import Path
import re
H=Path(__file__).resolve().parent
OLD='calendar_choices_20260929';NEW='calendar_choice_context_20260929'
def source(stem,ext='.py'):
    return (H/(stem+'_'+OLD+ext)).read_text('utf8').replace(OLD,NEW).replace('CALENDAR_CHOICES_20260929','CALENDAR_CHOICE_CONTEXT_20260929')
def write(stem,t,ext='.py'):
    p=H/(stem+'_'+NEW+ext);p.write_text(t,'utf8')
    if ext=='.py':compile(t,str(p),'exec')
t=source('build').replace('acb3e7abefcd37d58dbc8ac7d6bc38c01c5bec7b5ee244580c2f62ce989cdb3c','6681bc33dc97a99eb59a3280a3b53e505f09fb8aac7e8a1d84c0b64e0c9b08ac').replace('KR_R29','KR_S29')
t=t.replace("('when_fix','KR_T19WhenFix','KR_S29When','no','string'),('conds','KR_T19CardCond','KR_S29Cond','k','string'),\n      ('stage_cols','KR_T19StageCols','KR_S29StageCols','k','int'),('chip_cols','KR_T19ChipCols','KR_S29ChipCols','c','int')", "('when_fix','KR_T19WhenFix','KR_S29When','no','string')")
insert='''
# Only the 20 context-rich details gain an explicit choice field; other boards use an exact fallback.
info=(HERE/'calendar_detail_layout_20260929.jaf').read_text('utf8').split('string KR_B29Info(',1)[1].split('void KR_B29Buttons()',1)[0]
baseinfo='string KR_S29InfoBase('+info
info='string KR_S29Info('+info
info=info.replace('    bool read = KR_P29Read(no);','    string date="";\\n'+''.join('    if(no==%s) date=%s;\\n'%(n,json.dumps(v,ensure_ascii=False)) for n,v in labels['dates'].items())+'    if(date=="") return KR_S29InfoBase(no,stages,width);\\n    bool read = KR_P29Read(no);\\n    if(!read) date=KR_T19EvWhen(no);')
info=info.replace('string t = KR_B29Field("언제",KR_T19EvWhen(no),width);','string t = KR_B29Field("언제",date,width);\\n    if(read) t=t+KR_B29Field("선택",KR_T19WhenFix(no),width);\\n    else t=t+KR_B29Field("선택","열람 후 표시됩니다",width);')
jaf.append(baseinfo)
jaf.append(info)
'''
t=t.replace("jaf='\\n\\n'.join(jaf)+'\\n';",insert+"\njaf='\\n\\n'.join(jaf)+'\\n';")
insert2='''
old='KR_B29Info';new='KR_S29Info';clone=new+'Base'
assert all(m['functions'][fid(old)][k]==dm['functions'][ids[clone]][k] for k in ['arguments','variables','return-type'])
p=W/(old+'_original.jam');L.cmd('ain','dump','--function',old,'-o',p,src)
jam=L.clean(p.read_text('utf8'),old)
jam=re.sub(r'(?m)^FUNC .*$',f'FUNC {ids[clone]}',jam);jam=re.sub(r'(?m)^ENDFUNC .*$',f'ENDFUNC {clone}',jam)
patch.append(jam);clones[clone]=old
p=W/(new+'.jam');L.cmd('ain','dump','--function',new,'-o',p,decl)
patch.append(L.clean(L.native_lower(p.read_text('utf8')),new))
patch.append(f'FUNC {fid(old)}\\n\\t.LOCALREF no\\n\\t.LOCALREF stages\\n\\t.LOCALREF width\\n\\t.CALLFUNC {new}\\n\\tRETURN\\nENDFUNC {old}\\n'.replace('.CALLFUNC','CALLFUNC'))
'''
t=t.replace("(W/'patch.jam').write_text",insert2+"\n(W/'patch.jam').write_text")
t=t.replace("forward={old:new for _,old,new,_,_ in spec}","forward={old:new for _,old,new,_,_ in spec};forward['KR_B29Info']='KR_S29Info'")
write('build',t)
t=source('probe')
t=t.replace('KR_Q29Detail(50205,-1,"choice_recollection_long");', 'KR_Q29Detail(50205,-1,"choice_recollection_long"); KR_Q29Detail(612,-1,"choice_context_narration"); KR_Q29Detail(30153,-1,"choice_context_cinema"); KR_Q29Detail(65004,-1,"choice_context_replay");')
t=t.replace('KR_P22Shot("choice_common_unread");KR_P29Board', 'KR_P22Shot("choice_common_unread");KR_P29Board(323,KR_T19EvHead(323),1,true);KR_Q29Bounds(323);KR_P22Shot("choice_context_unread");KR_P22Log("CONTEXT UNREAD <<<\\\\n"+KR_B29Info(323,1,22)+"\\\\n>>>");KR_P29Board')
write('probe',t)
t=source('verify')
# Prior installed screenshots are the control group for unchanged surfaces.
t=t.replace('evidence/calendar_detail_layout_20260929/screenshots','evidence/calendar_choices_20260929/screenshots')
t=t.replace("assert '호시카와와' not in re.search(r'DETAIL 328 <<<\\n(.*?)\\n>>>',log,re.S).group(1)","assert '함께 촬영할 사람' in re.search(r'DETAIL 323 <<<\\n(.*?)\\n>>>',log,re.S).group(1)\nhidden=re.search(r'CONTEXT UNREAD <<<\\n(.*?)\\n>>>',log,re.S).group(1)\nassert all(s not in hidden for s in ['촬영','이즈미','해설','영화'])\nassert '열람 후 표시됩니다' in hidden")
t=t.replace("'choice_recollection_long.png']", "'choice_recollection_long.png','choice_context_narration.png','choice_context_cinema.png','choice_context_replay.png','choice_context_unread.png']")
t=t.replace('Scope: 38 numbered branch scenes, 7 common continuations and their references. Fourteen other after-training-priority answer-number labels remain outside this batch.', 'Scope: 20 character-selection branches and their details. Eighteen prior non-name choices and all seven common joins remain unchanged.')
t=t.replace('Display getters and branch-menu columns only;', 'Display getters and a dedicated detail choice field only;')
write('verify',t)
write('scan',source('scan','.ps1'),'.ps1')
t=source('publish')
t=t.replace("O/'work/build/helpers_readable.jaf']", "O/'work/build/helpers_readable.jaf',HERE/'calendar_detail_layout_20260929.jaf']")
t=t.replace("calendar_choices=str(E/", "calendar_choice_context=str(E/")
t=t.replace("hook['calendar_choices_revision']", "hook['calendar_choice_context_revision']")
t=t.replace("'source/label_patch.json'", "'source/label_patch.json'")
t=t.replace('Calendar choice labels now show actual choices instead of numbered branches, with verified common joins. Unread new choice identities hidden; original gameplay and save code preserved.', 'Twenty character choices now show source-backed situation, preceding prompt, and exact option in a separate detail choice field. Unread identities hidden; original gameplay and save code preserved.')
t=t.replace('Preserve KR_R29* choice-label overrides and exact cloned fallback getters. Thirty-eight numbered branches use real choice labels; seven common joins include all alternatives. Do not infer selected person from first speaker. Preserve original choices, endings, unread masking, portrait sizes, summaries and prior replay/save guards.', 'Preserve KR_S29* context display overrides and exact cloned fallbacks, including KR_S29Info dedicated choice field. Twenty character-selection branches distinguish photography, slideshow narration and cinema. Quote actual installed options, not invented character dialogue. Preserve all prior KR_R29 labels and common joins, original choices, endings, unread masking, portrait sizes, summaries and save guards.')
start=t.index("        note=f'");end=t.index("\n        write(R/'progress.md'",start)
t=t[:start]+'''        note=f'\\n\\n### {now} 캘린더 선택 상황·실제 문구 표기 설치 — Codex internal\\n- 인물 선택 20개: 함께 촬영할 사람 / 슬라이드 해설자 / 영화에 초대할 사람을 제목과 목록에서 구분. 상세 선택 칸에 앞선 질문·독백과 실제 선택지 문구 표시.\\n- 원본 JP 및 현재 설치 한국어를 대조했고 미열람 선택 정보는 숨김. 이전 일반 선택 18개와 공통 합류 7개, 시나리오/선택지/엔딩/초상화/저장 구조 유지.\\n- 독립 문맥 검수, native 무음 915칸 및 변경 상세/목록/취소·재생/열람·미열람 확인, 저장 {qa["existing_resume_saves"]}개와 복귀 주소 {qa["saved_return_frames"]}개 보존, Defender·설치/복구 검증 통과.\\n- 설치 {rt}; 백업·검증 {E}; 복구 publish_calendar_choice_context_20260929.py --restore.\\n'
'''.rstrip()+t[end:]
start=t.index("    P.put(E/'README.md'");end=t.index("\n    print(P.js(report)",start)
t=t[:start]+'''    P.put(E/'README.md',('# 캘린더 선택 상황·문구\\n\\n촬영 상대, 슬라이드 해설자, 영화 동행자를 고르는 인물 선택 20개를 구분합니다. 상세 보드의 선택 칸에 앞선 질문/독백과 실제 게임 선택지 문구를 함께 표시합니다. 미열람 정보는 숨기며 원본 대사·선택지·엔딩 조건·저장은 변경하지 않았습니다.\\n\\nscreenshots: 실제 native 무음 검증 / before: 설치 전 백업 / source: 문맥 근거, 소스, 검수 기록.\\n').encode('utf8'))'''+t[end:]
write('publish',t)
print('Context build, probe, verification, scan and publisher adapters created.')
