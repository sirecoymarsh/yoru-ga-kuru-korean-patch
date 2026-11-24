# -*- coding: utf-8 -*-
"""One-off edit (10-18): 23 monthly talks sit in the pools of several months (later companions; some apart, e.g. 6월 and 11월):
KR_DLInfo keeps a month mask for kind 1 and KR_DLDue gives the deadline of the run of months that holds today."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def edit(path, pairs):
    s = path.read_text('utf8')
    for a, b in pairs:
        assert s.count(a) == 1, (path.name, a[:80], s.count(a))
        s = s.replace(a, b)
    path.write_text(s, 'utf8')


edit(HERE / 'claude_deadline.jaf', [
    ('''//   1  a monthly 특훈 뒤 대화 - its pool belongs to one month, so it closes on that month's last day;''',
     '''//   1  a monthly 특훈 뒤 대화 - in the pools of some months (most one month; a later companion's talks may sit in two or
//      three, even apart), so it closes on the last day of the run of months that holds today;'''),
    ('''// ---- baked: event -> kind * 100000000 + from * 10000 + due (from, due = month * 100 + day; from 0 = from the start)''',
     '''// ---- baked: event -> kind * 100000000 + (kind 1: the month mask, bit 0 = 4월 .. bit 7 = 11월;
//      kind 2: from * 10000 + due, month * 100 + day, from 0 = from the start)'''),
    ('''string KR_DLOrange() { return "r=255 g=152 b=92"; }''',
     '''string KR_DLOrange() { return "r=255 g=152 b=92"; }
int KR_DLBit(int mask, int m) {
    if (m < 4 || m > 11) return 0;
    int p = 1;
    for (int k = 4; k < m; k++) p = p * 2;
    return (mask / p) % 2;
}
// the deadline (month * 100 + day) of an event open today, else 0
int KR_DLDue(int info, int today) {
    if (info <= 0) return 0;
    int kind = info / 100000000;
    int rest = info % 100000000;
    if (kind == 1) {
        int m = today / 100;
        if (KR_DLBit(rest, m) == 0) return 0;
        int m2 = m;
        while (m2 < 11 && KR_DLBit(rest, m2 + 1) == 1) m2++;
        return m2 * 100 + KR_DLMonthDays(m2);
    }
    int due = rest % 10000;
    int from = rest / 10000;
    if (today > due) return 0;
    if (from > 0 && today < from) return 0;
    return due;
}'''),
    ('''bool KR_DLPending(int no, int today) {
    int info = KR_DLInfo(no);
    if (info <= 0) return false;
    int due = info % 10000;
    int from = (info / 10000) % 10000;
    if (today > due) return false;
    if (from > 0 && today < from) return false;
    int lane''', '''bool KR_DLPending(int no, int today) {
    if (KR_DLDue(KR_DLInfo(no), today) == 0) return false;
    int lane'''),
    ('''        KR_DLPut("u%d" % n, "%d" % (KR_DLInfo(no) % 10000));''', '''        KR_DLPut("u%d" % n, "%d" % KR_DLDue(KR_DLInfo(no), today));'''),
])
edit(HERE / 'work' / 'make_build.py', [
    ('''    calendar cells (r22 cells.json, tabs 0-7): kind 1 = an after_training pool of one month (closes on its last day), kind 2 =''',
     '''    calendar cells (r22 cells.json, tabs 0-7): kind 1 = after_training pools of some months (the month mask), kind 2 ='''),
    ('''            if ms:
                assert len(ms) == 1, (no, ms)
                m = ms[0]
                info[no] = 1 * 100000000 + (m * 100 + 1) * 10000 + m * 100 + END[m]''',
     '''            if ms:
                assert all(4 <= m <= 11 for m in ms), (no, ms)
                info[no] = 1 * 100000000 + sum(1 << (m - 4) for m in ms)'''),
])
print('ok')
