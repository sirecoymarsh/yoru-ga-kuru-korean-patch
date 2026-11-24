"""Base-independent preparation of one summary layer (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).

  python prepare_summary_layer.py --summaries <summaries.json ...> [--scenarios ...] --tag <mm> --out <folder>
        [--term-patch <term_alignment.json> [--term-confidence high]] [--only-patched] [--allow-draft]

Everything build_summary_layer.py does before it touches an AIN: A/B files merged in ID order (duplicate IDs refused), status gate
(independent_qa_pass / source_qa_pass baked, copy_of re-calls the original, excluded skipped), text gate (<= 100, no line break,
encodable), frozen-source binding (message IDs / source_event_sha256), the term-alignment patch (confidence >= the threshold, the
summary's current sha256 = the audited one, `before` exactly once, gates + particle check after the replacement - a patched text
that fails keeps its approved text and is listed, --term-strict stops instead; the summaries files are never modified), --only-patched selection, and where every copy_of target's text lives (this layer, April, E00011 or a
month that must be stacked below). The build repeats the same steps (same code), so a prepared result is what the build bakes.
Writes <out>/design/prepared_layer.json and <out>/evidence/term_patch_applied.json; the console shows counts only.
"""
from pathlib import Path
import argparse, datetime, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sltools as T
L = T.L


def record(tag, prep, summaries, term_path):
    now = datetime.datetime.now().astimezone().isoformat()
    lay = prep['layer']
    tabs = T.tab_of()
    names = T.tab_names()
    ids = sorted(set(prep['texts']) | set(prep['copies']))
    doc = dict(tag=tag, key=T.key(tag), author=T.AUTHOR, time=now, summaries=[str(p) for p in summaries],
               files=lay['files'], texts=len(prep['texts']), copies=len(prep['copies']), excluded=lay['excluded'],
               ids=ids, id_range=[ids[0], ids[-1]] if ids else None,
               tabs={names[t]: sum(1 for n in ids if tabs.get(n) == t) for t in sorted({tabs.get(n) for n in ids if n in tabs})},
               copy_resolution=prep['copy_resolution'],
               copy_targets_missing=sorted(int(k) for k, v in prep['copy_resolution'].items() if v['text_in'] == 'missing'),
               copy_targets_below=sorted({v['text_in'] for v in prep['copy_resolution'].values() if v['text_in'] != 'this layer'}),
               term_patch=None if not prep['term_record'] else {k: v for k, v in prep['term_record'].items() if k != 'events'},
               events=[dict(no=n, kind='text', summary=prep['texts'][n]) if n in prep['texts'] else dict(no=n, kind='copy_of', copy_of=prep['copies'][n])
                       for n in ids])
    term_doc = None
    if prep['term_record']:
        term_doc = dict(prep['term_record'], tag=tag, author=T.AUTHOR, time=now,
                        note='Applied to the text that is baked; the summaries.json files are not modified.')
    return doc, term_doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--summaries', nargs='+', required=True)
    ap.add_argument('--scenarios', nargs='*', default=[])
    ap.add_argument('--tag', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--term-patch')
    ap.add_argument('--term-confidence', default='high', choices=sorted(T.CONF_RANK, key=T.CONF_RANK.get))
    ap.add_argument('--only-patched', action='store_true')
    ap.add_argument('--term-strict', action='store_true', help='stop when a patched text fails the gate (default: keep the approved text)')
    ap.add_argument('--allow-draft', action='store_true')
    a = ap.parse_args(argv)
    T.prefix(a.tag)
    summaries = [Path(p).resolve() for p in a.summaries]
    out = T.assert_writable(a.out, extra_forbidden=[p.parent.parent for p in summaries])
    prep = T.prepare_layer(summaries, a.scenarios, a.allow_draft, a.term_patch, a.term_confidence, a.only_patched, a.term_strict)
    doc, term_doc = record(a.tag, prep, summaries, a.term_patch)
    T.writej(out / 'design/prepared_layer.json', doc)
    if term_doc:
        T.writej(out / 'evidence/term_patch_applied.json', term_doc)
    tp = doc['term_patch'] or {}
    print(json.dumps(dict(tag=a.tag, texts=doc['texts'], copies=doc['copies'], excluded=len(doc['excluded']), id_range=doc['id_range'],
                          tabs=doc['tabs'], copy_missing=len(doc['copy_targets_missing']), copy_text_in=doc['copy_targets_below'],
                          term_applied=tp.get('applied'), term_changed=len(tp.get('changed_ids', [])), term_skipped_proposals=tp.get('skipped_proposals'),
                          term_skipped_summaries=tp.get('skipped_summaries'), term_gate_skipped=[g['no'] for g in tp.get('gate_skipped', [])],
                          term_below_threshold=tp.get('below_threshold')), ensure_ascii=False))
    return doc


if __name__ == '__main__':
    main()
