# -*- coding: utf-8 -*-
"""One-off edit (10-18): the probes follow the reveal rule (home: seen in this save) and check it on a row read elsewhere."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
for path in [HERE / 'probe_list.py', HERE / 'work' / 'probe_jaf.txt']:
    s = path.read_text('utf8')

    def rep(a, b):
        global s
        assert s.count(a) == 1, (path.name, a[:80], s.count(a))
        s = s.replace(a, b)

    rep('''                if (tk < 0 && KR_P29Read(no) && KR_CCanPlay(no) && nm.Find("특훈 뒤") >= 0) tk = k;''',
        '''                if (tk < 0 && KR_LVReveal(no, 2) && KR_CCanPlay(no) && nm.Find("특훈 뒤") >= 0) tk = k;''')
    rep('''                if (nm && !KR_P29Read(KR_CCellEv(i))) {''', '''                if (nm && !KR_LVReveal(KR_CCellEv(i), 2)) {''')
    rep('''            KR_PRCheck("the board parts are released under the list", !PartsEngine.IsExist(KR_XVP(0)));
            KR_PRShot("lv_list_apr_izumi.bmp");''',
        '''            KR_PRCheck("the board parts are released under the list", !PartsEngine.IsExist(KR_XVP(0)));
            // a row read in another save but not seen in this one keeps its summary and cast closed at home
            int other = -1;
            for (int k = 0; k < 14; k++) {
                int i = KR_PRNth(0, 2, k);
                if (i < 0) break;
                int no = KR_CCellEv(i);
                if (other < 0 && KR_CGlobal(no) == 1 && !N_ScenarioRegister::IsRegisteredEvent(KR_T9Fn(no))) other = k;
            }
            KR_PRLog("READ ELSEWHERE row=" + ("%d" % other) + " text=" + KR_PRTxt(KR_LVP(100 + other * 10 + 8)));
            if (other >= 0) KR_PRCheck("home: a row read only in another save shows no summary and no faces",
                                       KR_PRHas(KR_LVP(100 + other * 10 + 8), "본 뒤에") && !PartsEngine.IsExist(KR_LVP(100 + other * 10 + 4)));
            KR_PRShot("lv_list_apr_izumi.bmp");''')
    path.write_text(s, 'utf8')
    print('ok', path.name)
