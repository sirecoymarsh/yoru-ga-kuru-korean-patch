"""Dry-run common comma-continuation layout rule; never writes a game AIN."""
import collections,re,sys
import polish_translation_20260917 as p
import audit_message_pixel_widths as m
sys.stdout.reconfigure(encoding='utf-8')
j,k,pr,classes,proxy=p.load()
current=p.readj(p.WORK/'final_map.json')
pages=p.readj(p.HERE/'message_page_groups.json')['pages']
excluded=set(p.readj(p.WORK/'semantic_exclusions.json')['message_ids'])
uses=collections.Counter(i for pg in pages for i in pg['body_message_ids'])
_,faces=m.parse_fnl_font(p.INPUT/'font.fnl',0)
face,den,_=m.select_fnl_face(faces,60)
indices,_=m.load_proxy_indices(proxy,len(face.widths))
meter=m.WidthMeasurer(face,den,indices,-2.,2.,0.)
width=lambda t:meter.measure(t,True)['max_width_px']
normal=lambda t:re.sub(r'\s','',t)
counts=collections.Counter();records=[];edits={}
for pg in pages:
 ids=pg['body_message_ids'];vals=[current.get(str(i),k[i]) for i in ids]
 if not pg['complete'] or len(ids)<2 or not any(t.rstrip().endswith(',') for t in vals[:-1]):continue
 if pg['window_type'] not in ('Text','Face','All') or pg['font_command']!=0:counts['nonstandard_window_font']+=1;continue
 if any(i in excluded for i in ids):counts['excluded_semantic_scope']+=1;continue
 if any(uses[i]!=1 for i in ids):counts['multiple_uses']+=1;continue
 if any(not t.strip() or re.search(r'[\x00-\x1f\x7f]|\$\{|【|】|료　　　　',t) for t in vals):counts['protected_or_blank']+=1;continue
 # Only ordinary narration or uniformly indented single-speaker dialogue.
 quoted=vals[0].startswith('「') and vals[-1].endswith('」')
 if quoted:
  if any(not t.startswith('　') for t in vals[1:]):counts['irregular_indent']+=1;continue
 elif any(t.startswith(('　',' ')) or '「' in t or '」' in t for t in vals):counts['irregular_indent']+=1;continue
 budget=668 if pg['window_type']=='Face' else 884
 if any(width(t)>budget for t in vals):counts['existing_width_exception']+=1;continue
 clean=[t[1:] if t.startswith('　') else t for t in vals]
 groups=[];group=clean[0]
 for a,b in zip(clean,clean[1:]):
  if a.rstrip().endswith(','):group=group.rstrip()+' '+b.lstrip(' ')
  else:groups.append(group);group=b
 groups.append(group)
 out=[];failed=False
 for group in groups:
  rest=group
  while rest:
   indent='　' if quoted and out else ''
   if width(indent+rest)<=budget:out.append(indent+rest);break
   choices=[i for i,c in enumerate(rest) if c==' ' and i>0 and width(indent+rest[:i])<=budget and rest[i+1:i+2] not in '」』）】!?！？.,、。']
   if not choices:failed=True;break
   cut=max(choices);out.append(indent+rest[:cut]);rest=rest[cut+1:]
  if failed:break
 if failed or len(out)>len(ids):counts['unfit_without_word_split']+=1;continue
 blank=len(ids)-len(out);out+=['']*blank
 assert normal(''.join(out))==normal(''.join(vals))
 assert all(width(t)<=budget for t in out)
 if out==vals:counts['already_suitable']+=1;continue
 records.append({'page_id':pg['page_id'],'ids':ids,'blank_tail_fields':blank,'old_widths':[width(t) for t in vals],'new_widths':[width(t) for t in out]})
 for i,old,new in zip(ids,vals,out):
  if old!=new:edits[str(i)]=new
 counts['changed_pages']+=1;counts['new_empty_fields']+=blank
 if blank:counts['pages_with_empty_tail']+=1
report={'status':'dry_run_only_not_applied','rule':'Within complete, uniform, single-use MSG/R/.../A pages, join only comma-ended boundaries and wrap at spaces using exact FNL widths. Preserve characters and punctuation, page control, names and other original line boundaries. Empty tail fields are an unresolved runtime/intent risk.','counts':dict(counts),'changed_fields':len(edits),'reported_page':next((r for r in records if 2280 in r['ids']),None),'records':records}
p.writej(p.WORK/'global_lineflow_dry_run.json',report)
p.writej(p.WORK/'global_lineflow_dry_run_map.json',edits)
print({k:v for k,v in report.items() if k!='records'})
print('Reported paragraph trial:',[edits.get(str(i),current.get(str(i),k[i])) for i in [2280,2281,2282]])
