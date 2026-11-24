p = __file__.replace('edit_explore1.py', 'explore_r20.py')
s = open(p, encoding='utf8').read()
s = s.replace('" abs=" + ("%d" % ax) + "," + ("%d" % ay)', '" abs=" + ("%f" % ax) + "," + ("%f" % ay)')
s = s.replace('" abs=" + ("%d" % PartsEngine.GetComponentAbsolutePosX(n)) + "," + ("%d" % PartsEngine.GetComponentAbsolutePosY(n))',
              '" abs=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(n)) + "," + ("%f" % PartsEngine.GetComponentAbsolutePosY(n))')
s = s.replace('" abs=" + ("%d" % PartsEngine.GetComponentAbsolutePosX(root)) + "," + ("%d" % PartsEngine.GetComponentAbsolutePosY(root))',
              '" abs=" + ("%f" % PartsEngine.GetComponentAbsolutePosX(root)) + "," + ("%f" % PartsEngine.GetComponentAbsolutePosY(root))')
a = 'int KR_XMsgWait(FTPARTS_WaitForClickCallback func, bool cancel) {'
b = '''// probe only: what the player's hover does before the click (C_SceneHomebase@RunMember OnEnterChara: SetInfo + Show)
void KR_XPrepStatus(int charaNo, ref C_HomeMemberView memView) {
    ref C_HomeStatusView sv = memView.m_StatusView;
    sv.SetInfo(charaNo);
    sv.Show();
    KR_XLog("PREPSTATUS " + ("%d" % charaNo));
}
''' + a
if 'KR_XPrepStatus' not in s:
    assert s.count(a) == 1
    s = s.replace(a, b)
a = "    (work / 'x.jam').write_text('\\n'.join(patch), 'utf8')"
assert s.count(a) == 1, s.count(a)
b = """    rs = L.fid_of(m, 'C_SceneHomebase@RunStatus')
    path = work / f'original_{rs}.jam'
    L.cmd('ain', 'dump', '--function', 'C_SceneHomebase@RunStatus', '-o', path, src)
    patch.append(L.begin(L.clean(path.read_text('utf8'), 'C_SceneHomebase@RunStatus'), '\\t.LOCALREF charaNo\\n\\t.LOCALREF memView\\n\\tCALLFUNC KR_XPrepStatus\\n'))
""" + a
if "original_{rs}" not in s:
    s = s.replace(a, b)
open(p, 'w', encoding='utf8').write(s)
print('ok')
