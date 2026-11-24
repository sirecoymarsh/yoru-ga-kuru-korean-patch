"""Execute fixed JAM and real weapon-table regressions, retaining the prior suite."""
from pathlib import Path
import copy,json
from cheat_support_20260915 import R,sha,savej,cmd
from build_remaster_multiplier_20260915 import ex,decode
from build_mod_tab_20260915 import scalar
from build_route_perf_20260915 import symbol

HERE=Path(__file__).resolve().parent;O=R/'staging/smart_auto_fix_20260922';BASE=R/'staging/smart_auto_20260922'
# Keep historical verification immutable. Reuse it with stronger native boundaries.
s=(HERE/'verify_smart_auto_20260922.py').read_text(encoding='utf8')
s=s.replace("O=R/'staging/smart_auto_20260922'","O=R/'staging/smart_auto_fix_20260922'")
s=s.replace("[0]*5","[0]*6")
s=s.replace("assert v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]])", "v.weapons[0]=w;assert v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]])")
s=s.replace("result=v.run('KR_SmartDamage',[v.pa,w,e[0]])", "v.weapons[0]=w;result=v.run('KR_SmartDamage',[v.pa,w,e[0]])")
ns={'__name__':'smart_auto_fix_regressions','__file__':str(HERE/'verify_smart_auto_20260922.py')};exec(compile(s,ns['__file__'],'exec'),ns)
BaseVM=ns['VM'];M=ns['M'];FS=ns['FS']

class VM(BaseVM):
 def method(self,mid,owner,args):
  if mid in [27320,27321,27325,27326,27290,27293,27296,27297]:
   return self.run(symbol(M,mid),args,owner)
  # Simple native property access boundary; all attack/hit arithmetic runs JAM.
  if mid in [26843,26846,26876]:return owner[{26843:12,26846:13,26876:23}[mid]]
  if mid in [27288,27291,27294]:return owner[{27288:0,27291:1,27294:2}[mid]]
  return super().method(mid,owner,args)
ns['VM']=VM

def real_table(rt):
 t=ex.decode_ex(rt/'NightRemasterEX.ex').blocks[39].payload;rows={};weapons={}
 for row in t.rows:
  r=[decode(c.payload.value) if c.type_id==3 else scalar(c.payload) for c in row];rows[r[0]]=r
  w=[0]*28;w[0]=r[0];w[1]=r[5];w[2:6]=r[1:5];w[6:17]=r[6:17]
  w[17:23]=[r[20],r[21],r[19],r[22],r[17],r[18]];w[23:26]=r[23:26]
  w[26]=r[26:31]+[0];w[27]=[i for i in r[31:36] if i>0];weapons[r[0]]=w
 return rows,weapons

def setup(character,table,rows):
 v=VM();v.pa[0]=character;v.pa[1]=60;v.pa[2]=v.pa[3]=10000;v.pa[13:17]=[250]*4
 v.weapons=copy.deepcopy(table)
 eligible=[i for i,r in rows.items() if character*100<i<=character*100+15 and all(v.pa[13+j]>=r[6+j] for j in range(4))]
 v.weapons[0]=copy.deepcopy(table[max(eligible)])
 v.areas={1:[int(i==12) for i in range(25)],2:[int(i//5==2) for i in range(25)],3:[int(i%5==2) for i in range(25)],4:[1]*25}
 v.enemies=[ns['enemy'](i,5000) for i in range(9)]
 return v

def test_real():
 rt=Path(json.loads((O/'source_pointer.json').read_text())['runtime']);rows,table=real_table(rt)
 ids=[i for i,w in table.items() if i//100 in [3,6,7] and 50<=i%100<100 and w[11]==0]
 assert len(ids)==26,ids
 evidence=[]
 for i in ids:
  v=setup(i//100,table,rows);before=copy.deepcopy((v.pa,v.weapons,v.enemies));best=v.evaluate(i)
  assert best[0]>0 and best[1]==i and best[2]>=0,(i,best)
  assert before==(v.pa,v.weapons,v.enemies)
  # Same complete data and boundaries reproduce the previous rejecting body.
  original_execute=ns['ns']['O'];ns['ns']['O']=BASE
  try:
   old=setup(i//100,table,rows);rejected=old.evaluate(i);assert rejected[0]==0 and rejected[2]==-1,(i,rejected)
  finally:ns['ns']['O']=original_execute
  evidence.append(dict(id=i,name=rows[i][5],old_score=rejected[0],fixed_score=best[0],target=best[2]))
 # Native eligible skill list, not forced EX: favorable actual abilities win.
 selections=[]
 for character in [3,6,7]:
  v=setup(character,table,rows);v.techniques=[i for i,r in rows.items() if i//100==character and 50<=i%100<100 and r[8]<=v.pa[1]]
  if character==7:
   v.enemies=[ns['enemy'](0,5000)]+[-1]*8;v.enemies[0][0][13]=1
  assert v.decide() and v.pf[3]==1,(character,v.pf)
  assert v.pf[4] in v.techniques
  selections.append(dict(character=character,technique=v.pf[4],name=rows[v.pf[4]][5],action=v.pf[3]))
 # Type-0 EX keeps EX-only costs/repeat/range; HP must never be treated as basic.
 v=setup(3,table,rows);i=355;v.enemies=[ns['enemy'](0,100000)]+[-1]*8
 a=v.evaluate(i);v.pa[25][51]=3;v.pa[25][52]=5;b=v.evaluate(i);assert a==b,(a,b)
 v.pa[23]=4;assert v.evaluate(i)[2]==-1 # native strict reach 4 > depth+y
 v=setup(3,table,rows);cost=table[i][20]+v.pa[1]*table[i][9]//100;floor=(v.pa[2]+4)//5
 v.pa[3]=floor+cost-1;assert v.evaluate(i)[2]==-1
 v.pa[3]=floor+cost;assert v.evaluate(i)[2]>=0
 # Damage uses current weapon, not zero EX placeholders, without mutating it.
 v=setup(7,table,rows);i=752;w=v.weapons[i];assert w[12]==w[13]==0
 damage=v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]]);assert damage>1
 v.weapons[0][12]*=2;assert v.run('KR_SmartDamage',[v.pa,w,v.enemies[0][0]])>damage
 result=dict(table_sha256=sha(rt/'NightRemasterEX.ex'),affected_count=len(ids),regressions=evidence,real_skill_selections=selections,EX_cost_range_repeat_preserved=True,current_weapon_base_not_placeholder=True,gameplay_verified=False)
 savej(O/'real_weapon_regression.json',result);return result

def main():
 ns['prepare']();ns['test']();actual=test_real()
 report=json.loads((O/'verification.json').read_text());report['status']='SMART_AUTO_FIX_COMPILED_PASS'
 report['real_weapon_data']=actual;report['boundaries']='Original native attack/hit computation and modified decision JAM executed; property/table/copy/graphics boundaries emulated; no native gameplay claim.'
 savej(O/'verification.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
