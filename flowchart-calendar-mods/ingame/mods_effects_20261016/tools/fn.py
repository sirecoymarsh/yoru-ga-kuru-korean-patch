import sys, live
d = live.load()
for a in sys.argv[1:]:
    i = int(a, 0)
    print(i, d['names'][i] if 0 <= i < len(d['names']) else '??')
