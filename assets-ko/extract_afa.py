import subprocess, sys, os
sys.stdout.reconfigure(encoding='utf-8')
A = r'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830\tools\alice-tools-0.13.0\alice.exe'
src, out = sys.argv[1], sys.argv[2]
lst = subprocess.run([A, 'ar', 'list', '--output-encoding', 'utf-8', src], capture_output=True).stdout.decode('utf-8', 'replace').splitlines()
names = [l.split(': ', 1)[1] for l in lst if ': ' in l]
for n in names:
    d = os.path.dirname(os.path.join(out, n.replace('/', os.sep)))
    os.makedirs(d, exist_ok=True)
r = subprocess.run([A, 'ar', 'extract', '--raw', '-f', '--output-encoding', 'utf-8', '-o', out, src], capture_output=True)
err = r.stderr.decode('utf-8', 'replace')
print(len(names), 'entries; errors:', err.count('ERROR'))
print(err[:500])
