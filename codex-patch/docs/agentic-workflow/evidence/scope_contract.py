"""Executable design contract, NOT installed game code or native runtime proof."""
from dataclasses import dataclass, replace
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
RANGES = [(1001,1010),(1101,1110),(2001,2010),(2101,2110),
          (2201,2210),(2301,2310),(2401,2410),(2501,2510)]
ALLOWED = frozenset(i for lo,hi in RANGES for i in range(lo,hi+1))

@dataclass(frozen=True)
class Context:
    current_id: int = 1001
    map_id: int = 1001
    start_id: int = 1001
    base_id: int = 1000
    scene_id: int = 13
    enabled: bool = True
    sunday_exploration: bool = True
    event_object_present: bool = False
    map_present: bool = True
    table_ref_valid: bool = True
    party_count: int = 3
    valid_party_refs: bool = True
    movable_count: int = 3
    remaining: int = 1000
    tutorial: bool = False
    battle: bool = False
    other_modal: bool = False
    transitioning: bool = False
    moving: bool = False
    scene_generation: int = 1
    map_generation: int = 1
    session: int = 1
    date_key: int = 428
    party_ids: tuple = (1,2,3)
    multipliers: tuple = (1,1,1,1)

def eligible(c):
    """Common predicate for display and commit recheck; no RNG or state writes."""
    family = 1000 if c.current_id < 2000 else 2000
    return (c.enabled and c.current_id in ALLOWED and c.scene_id == 13
        and c.map_present and c.table_ref_valid and c.map_id == c.current_id
        and c.start_id in ALLOWED and c.base_id == family
        and c.start_id // 1000 == c.current_id // 1000
        and c.sunday_exploration and not c.event_object_present
        and 1 <= c.party_count <= 3 and c.valid_party_refs
        and 1 <= c.movable_count <= c.party_count and c.remaining > 0
        and not (c.tutorial or c.battle or c.other_modal or c.transitioning or c.moving))

def may_commit(confirmed, live, explicit_confirmation):
    # Snapshot equality also rejects a changed but otherwise eligible floor/date/party.
    return bool(explicit_confirmation and confirmed == live and eligible(live))

def main():
    rows = json.loads((HERE/'dungeon_table.json').read_text(encoding='utf8'))
    by_id = {r['id']: r for r in rows}
    assert len(by_id) == len(rows) == 118
    assert len(ALLOWED) == 80 and ALLOWED <= by_id.keys()
    assert {i for i in by_id if i >= 1000} - ALLOWED == {1201,2601}
    cases = []
    def check(label,actual,expected):
        assert actual == expected, (label,actual,expected)
        cases.append({'id':label,'pass':True})
    for i in by_id:
        base = 1000 if i < 2000 else 2000
        c = replace(Context(),current_id=i,map_id=i,start_id=base+1,base_id=base)
        check(f'EX:{i}',bool(eligible(c)),i in ALLOWED)
    for i in (-1,0,1000,1011,1500,1999,2000,2602,99999):
        check(f'unknown:{i}',bool(eligible(replace(Context(),current_id=i,map_id=i))),False)
    for key,value in dict(enabled=False,scene_id=12,sunday_exploration=False,
        event_object_present=True,map_present=False,table_ref_valid=False,map_id=1002,
        start_id=2001,base_id=2000,party_count=0,valid_party_refs=False,movable_count=0,
        remaining=0,tutorial=True,battle=True,other_modal=True,transitioning=True,moving=True).items():
        check(f'guard:{key}',bool(eligible(replace(Context(),**{key:value}))),False)
    check('party_overflow',bool(eligible(replace(Context(),party_count=4))),False)
    check('negative_time',bool(eligible(replace(Context(),remaining=-1))),False)
    check('cancel',may_commit(Context(),Context(),False),False)
    check('explicit_confirm',may_commit(Context(),Context(),True),True)
    for key,value in dict(current_id=1201,map_id=1002,map_generation=2,scene_generation=2,
        session=2,date_key=429,party_ids=(1,2,4),multipliers=(20,1,1,1),remaining=999).items():
        check(f'changed_after_confirm:{key}',may_commit(Context(),replace(Context(),**{key:value}),True),False)
    for before,after in [(1110,1201),(2510,2601),(1001,201),(2001,700)]:
        base=1000 if before<2000 else 2000
        c=replace(Context(),current_id=before,map_id=before,start_id=base+1,base_id=base)
        check(f'stale:{before}->{after}',may_commit(c,replace(c,current_id=after,map_id=after),True),False)
    evidence = {
        'status':'SCOPE_CONTRACT_STATIC_PASS_NOT_INSTALLED',
        'translator_model':'Codex internal',
        'allowed_current_dungeon_ids':sorted(ALLOWED),
        'excluded_story_ids':sorted(i for i in by_id if i<1000),
        'excluded_special_terminal_ids':[1201,2601],
        'unknown_ids':'deny',
        'native_runtime_verified':False,
        'fixture_count':len(cases),'fixtures':cases,
        'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [HERE/'dungeon_table.json',*(HERE/f'original_{i}.jam' for i in
            (26986,26988,27068,27069,27150,27151,28622,28624,28637,28639,26518,30093,30094,30087,28172,27741,26469))]},
        'limitations':[
            'This Python contract does not prove AIN/PACT bindings or runtime operation.',
            'Map/scene generation and modal guards still require native implementation and verification.',
            'Reward coefficients, full rollback boundary and event ID audit remain WI-001 work.'
        ]
    }
    (HERE/'scope-contract-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'PASS {len(cases)} static contract cases; 80 ordinary / 36 story / 2 excluded terminal IDs; game unchanged')

if __name__ == '__main__': main()
