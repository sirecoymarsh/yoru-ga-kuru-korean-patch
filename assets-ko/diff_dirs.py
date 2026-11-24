import sys, os, hashlib, collections, shutil, json
sys.stdout.reconfigure(encoding='utf-8')
a, b = sys.argv[1], sys.argv[2]   # a = korean, b = reference
out = sys.argv[3] if len(sys.argv) > 3 else None
def h(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()
c = collections.Counter(); rep = []
for dp, dns, fns in os.walk(a):
    for f in fns:
        pa = os.path.join(dp, f); rel = os.path.relpath(pa, a); pb = os.path.join(b, rel)
        st = 'new' if not os.path.exists(pb) else ('same' if os.path.getsize(pa) == os.path.getsize(pb) and h(pa) == h(pb) else 'changed')
        ext = os.path.splitext(f)[1].lower()
        c[(st, ext)] += 1
        if st != 'same':
            rep.append({'path': rel.replace('\\', '/'), 'state': st, 'size': os.path.getsize(pa)})
            if out:
                d = os.path.join(out, rel); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(pa, d)
for k, v in sorted(c.items()): print(k, v)
if out: json.dump(rep, open(os.path.join(out, 'changed_files.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in rep[:40]: print(r)
