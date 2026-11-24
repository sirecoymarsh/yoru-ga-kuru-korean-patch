# -*- coding: utf-8 -*-
"""10-15: the probe logs the shimmer (row parts, glow band, portrait) instead of the star."""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'probe_autonav.py'
s = p.read_text('utf8')
pairs = [
    ('''void KR_PRStarLog(int n) {
    if (!PartsEngine.IsExist(n)) { KR_PRLog("STAR " + ("%d" % n) + " none"); return; }
    KR_PRLog("STAR " + ("%d" % n) + " parent=" + ("%d" % PartsEngine.Parts_GetParentPartsNumber(n)) + " alpha=" + ("%d" % PartsEngine.GetComponentAlpha(n)) + " mul=" + ("%d" % PartsEngine.GetComponentMulColorR(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorG(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorB(n)) + " show=" + ("%d" % KR_PRB(PartsEngine.IsComponentShow(n))));
}''',
     '''string KR_PRPart(int n) {
    if (n <= 0 || !PartsEngine.IsExist(n)) return ("%d" % n) + ":none";
    return ("%d" % n) + ":p" + ("%d" % PartsEngine.Parts_GetParentPartsNumber(n)) + ":z" + ("%d" % PartsEngine.GetComponentPosZ(n)) + ":a" + ("%d" % PartsEngine.GetComponentAlpha(n)) + ":mul" + ("%d" % PartsEngine.GetComponentMulColorR(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorG(n)) + "," + ("%d" % PartsEngine.GetComponentMulColorB(n)) + ":add" + ("%d" % PartsEngine.GetComponentAddColorR(n)) + "," + ("%d" % PartsEngine.GetComponentAddColorG(n)) + "," + ("%d" % PartsEngine.GetComponentAddColorB(n)) + ":w" + ("%d" % PartsEngine.Parts_GetPartsWidth(n, 1)) + ":show" + ("%d" % KR_PRB(PartsEngine.IsComponentShow(n)));
}
void KR_PRRowLog() {
    string t = "ROW n=" + KR_ANGet("RowN") + " n0=" + KR_ANGet("RowN0");
    int n = KR_ANGetInt("RowN");
    for (int i = 0; i < n; i++) t = t + " " + KR_PRPart(KR_ANGetInt("Row" + ("%d" % i)));
    t = t + " glow=" + KR_PRPart(KR_ANGlowPart());
    KR_PRLog(t);
}
void KR_PRTrLog() {
    KR_PRLog("TRAIN cg=" + KR_PRPart(KR_ANGetInt("TrCg")) + " box=" + KR_PRPart(KR_ANGetInt("TrBox")));
}'''),
    ('''    if (f == 40) { KR_PRStarLog(KR_ANStarPart()); KR_PRShot("an_choice_" + stage + "_a.bmp"); }
    if (f == 47) { KR_PRStarLog(KR_ANStarPart()); KR_PRShot("an_choice_" + stage + "_b.bmp"); }''',
     '''    if (f == 40) { KR_PRRowLog(); KR_PRShot("an_choice_" + stage + "_a.bmp"); }
    if (f == 71) { KR_PRRowLog(); KR_PRShot("an_choice_" + stage + "_b.bmp"); }'''),
    ('''    if (f == 40) { KR_PRStarLog(KR_ANTrainStarPart()); KR_PRShot("an_partner_a.bmp"); }
    if (f == 47) { KR_PRStarLog(KR_ANTrainStarPart()); KR_PRShot("an_partner_b.bmp"); }''',
     '''    if (f == 40) { KR_PRTrLog(); KR_PRShot("an_partner_a.bmp"); }
    if (f == 71) { KR_PRTrLog(); KR_PRShot("an_partner_b.bmp"); }'''),
    ('''        KR_PRLog("AFTER CONFIRM trfired=" + KR_ANGet("TrFired") + " star=" + ("%d" % KR_PRB(PartsEngine.IsExist(KR_ANTrainStarPart()))));''',
     '''        KR_PRLog("AFTER CONFIRM trfired=" + KR_ANGet("TrFired") + " trcg=" + KR_ANGet("TrCg"));'''),
    ('''    bool r = KR_ANSelFrame();
    if (KR_ANGet("Fired") == "1" && KR_PRGet("FiredLogged") != stage) {''',
     '''    bool r = KR_ANSelFrame();
    if (f == 1) KR_PRRowLog();
    if (KR_ANGet("Fired") == "1" && KR_ANGet("Mode") == "1" && KR_PRGet("FiredLogged") != stage) {'''),
]
for old, new in pairs:
    assert s.count(old) == 1, old[:50]
    s = s.replace(old, new)
assert not any(k in s for k in ('KR_ANStarPart', 'KR_ANTrainStarPart', 'StarLog')), 'star code left'
p.write_text(s, 'utf8')
print('ok')
