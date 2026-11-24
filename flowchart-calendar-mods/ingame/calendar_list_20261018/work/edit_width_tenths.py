# -*- coding: utf-8 -*-
"""One-off edit (10-18): text widths in tenths of a pixel (integer 0.8 x 16 = 12 lost 0.8 px a character and a 29-character
summary line ran 23 px past its column on the second native probe)."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'claude_list.jaf'
s = p.read_text('utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''// ---- text width and cutting / wrapping to a pixel width. Measured on the first native probe (10-18, font 257): Hangul and the
//      other two-byte (proxy) characters 0.8 x size, a space 0.27 x size, digits 0.4-0.47 x size; others taken as 0.55 x size.
int KR_LVCharW(string c, int size) {
    if (c == " ") return (size * 28) / 100;
    if (c.LengthByte() >= 2) return (size * 80) / 100;
    return (size * 55) / 100;
}
int KR_LVWidth(string s, int size) {''',
'''// ---- text width (in tenths of a pixel) and cutting / wrapping to a pixel width. Measured on the first native probe (10-18,
//      font 257): Hangul and the other two-byte (proxy) characters 0.8 x size, a space 0.27 x size, digits 0.4-0.47 x size;
//      others taken as 0.55 x size.
int KR_LVCharW(string c, int size) {
    if (c == " ") return (size * 28) / 10;
    if (c.LengthByte() >= 2) return size * 8;
    return (size * 55) / 10;
}
int KR_LVWidth(string s, int size) {''')
rep('''string KR_LVCut(string s, int size, int maxW) {
    if (KR_LVWidth(s, size) <= maxW) return s;
    int n = s.Length();
    int ell = (size * 80) / 100;''',
'''string KR_LVCut(string s, int size, int maxPx) {
    int maxW = maxPx * 10;
    if (KR_LVWidth(s, size) <= maxW) return s;
    int n = s.Length();
    int ell = size * 8;''')
rep('''string KR_LVWrap(string s, int size, int maxW, int maxLines) {
    string out = "";''',
'''string KR_LVWrap(string s, int size, int maxPx, int maxLines) {
    int maxW = maxPx * 10;
    string out = "";''')
# inside KR_LVWrap the two KR_LVCut calls take pixels
a = 'if (lines + 1 >= maxLines) return out + KR_LVCut(line + " " + word, size, maxW);'
assert s.count(a) == 1
s = s.replace(a, 'if (lines + 1 >= maxLines) return out + KR_LVCut(line + " " + word, size, maxPx);')
a = '''        if (ww > maxW) {
            if (lines + 1 >= maxLines) return out + KR_LVCut(word, size, maxW);
            out = out + KR_LVCut(word, size, maxW) + "\\n";'''
assert s.count(a) == 1, s.count(a)
s = s.replace(a, '''        if (ww > maxW) {
            if (lines + 1 >= maxLines) return out + KR_LVCut(word, size, maxPx);
            out = out + KR_LVCut(word, size, maxPx) + "\\n";''')
rep('''        int w = KR_LVWidth(label2, 17) + 30;''', '''        int w = (KR_LVWidth(label2, 17) + 9) / 10 + 30;''')
p.write_text(s, 'utf8')
print('ok')
