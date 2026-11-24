# -*- coding: utf-8 -*-
"""10-15: the three dialog buttons are opened from the casual site after the options close (opening a ■選択ダイアログ inside
the options' per-frame event re-entered the probe step code), the buttons themselves are checked on the page."""
import sys
from pathlib import Path
p = Path(sys.argv[1]); s = p.read_text('utf8')
pairs = [
('''        KR_PRShot("md_home_after.bmp");
        KR_PRStageSet("items");
        KR_PREnd(3);''',
 '''        KR_PRShot("md_home_after.bmp");
        KR_PRStageSet("menus");
        KR_PREnd(3);'''),
('''    if (stage == "items") {
        KR_PRStageSet("items_open");''',
 '''    if (stage == "menus") {
        KR_PROpenMenu("save");
        KR_PROpenMenu("term");
        KR_PROpenMenu("info");
        KR_PRStageSet("items");
    }
    if (stage == "items") {
        KR_PRStageSet("items_open");'''),
('''void KR_PRClickButton(string act, string n, string tag) {
    KR_PRStageSet("menu_dlg");
    KR_PRSet("Menu", tag);
    KR_PRSet("MenuDialogs", "0");
    KR_PRSet("DFrames", "0");
    KR_PRCheck(n + " is on the page and shown", AFL_Activity_IsExistPartsByName(act, n) && Ｐ＿表示設定取得(KR_PRPart(act, n)));
    // C_ConfigView@ClickEvent dispatches the click by part name to these (registered by name in EventConfLoadedActivity)
    KR_PRLog("OPEN " + n);
    if (tag == "save") KR_SaveStyleMenu();
    if (tag == "term") KR_TermMenu();
    if (tag == "info") KR_PlayerInfoMenu();
    KR_PRLog("OPEN " + n + " returned dialogs=" + KR_PRGet("MenuDialogs"));
    KR_PRCheck(n + " opened its dialog", KR_PRNum("MenuDialogs") >= 1);
    KR_PRStageSet("config_open");
}''',
 '''void KR_PRButtonOnPage(string act, string n) {
    KR_PRCheck(n + " is on the page and shown", AFL_Activity_IsExistPartsByName(act, n) && Ｐ＿表示設定取得(KR_PRPart(act, n)));
}
// C_ConfigView@ClickEvent dispatches a click on these buttons by part name (registered by name in EventConfLoadedActivity)
void KR_PROpenMenu(string tag) {
    KR_PRStageSet("menu_dlg");
    KR_PRSet("Menu", tag);
    KR_PRSet("MenuDialogs", "0");
    KR_PRSet("DFrames", "0");
    KR_PRLog("OPEN " + tag);
    if (tag == "save") KR_SaveStyleMenu();
    if (tag == "term") KR_TermMenu();
    if (tag == "info") KR_PlayerInfoMenu();
    KR_PRLog("OPEN " + tag + " returned dialogs=" + KR_PRGet("MenuDialogs"));
    KR_PRCheck(tag + " menu opened its dialog", KR_PRNum("MenuDialogs") >= 1);
}'''),
('''    if (f == 104) KR_PRClickButton(act, "KR_SaveStyleButton", "save");
    if (f == 108) KR_PRClickButton(act, "KR_TermConfigButton", "term");
    if (f == 112) KR_PRClickButton(act, "KR_PlayerInfoButton", "info");
    if (f == 116) { KR_PRLog("SETTINGS END " + KR_PRSettings()); KR_PRLog("CLOSE OPTIONS"); AFL_Activity_End(); }''',
 '''    if (f == 104) { KR_PRButtonOnPage(act, "KR_SaveStyleButton"); KR_PRButtonOnPage(act, "KR_TermConfigButton"); KR_PRButtonOnPage(act, "KR_PlayerInfoButton"); KR_PRButtonOnPage(act, "KR_ItemConfigButton"); }
    if (f == 108) { KR_PRLog("SETTINGS END " + KR_PRSettings()); KR_PRLog("CLOSE OPTIONS"); AFL_Activity_End(); }'''),
]
for a, b in pairs:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
p.write_text(s, 'utf8')
print('ok')
