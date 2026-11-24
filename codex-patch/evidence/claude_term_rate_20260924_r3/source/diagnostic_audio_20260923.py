"""Audio policy for isolated probes only. Never included in a game release."""
import json
from pathlib import Path

POLICY = 'Master mixer muted before initialization; config mute writes forced on; audio playback/timing retained.'
JAF = '''
void KR_DiagnosticMute() {
    if (!KiwiSoundEngine.SetMixerMute(0, true) ||
        !config::detail::GetMasterMute()) {
        system.Exit(91);
        return;
    }
}
'''

def mute_patch(meta):
    f = next(f for f in meta['functions'] if f['name'] == 'config::detail::SetMute')
    assert [a['name'] for a in f['arguments']] == ['groupNumber', 'mute']
    return (f"FUNC {f['index']}\n\t.LOCALREF groupNumber\n\tPUSH 1\n"
            '\tCALLHLL KiwiSoundEngine SetMixerMute 0\n\tPOP\n\tRETURN\n'
            'ENDFUNC config::detail::SetMute\n')

def scripted_input_patches(meta):
    """Do not let unrelated desktop clicks/keys alter scripted native probes."""
    return [f"FUNC {f['index']}\n\tPUSH 0\n\tRETURN\nENDFUNC {f['name']}\n"
            for f in meta['functions']
            if f['name'].startswith('C_UserInputManager::Is') and f['return-type'][0]==47]

def require_silent_probe(root):
    """Fail closed if an old builder produced the diagnostic AIN."""
    import hashlib
    root = Path(root)
    digest = hashlib.sha256((root/'NightRemaster.ain').read_bytes()).hexdigest()
    for name in ['click_probe_manifest.json', 'weapon_probe_manifest.json']:
        p = root/name
        if not p.exists():
            continue
        manifest = json.loads(p.read_text('utf8'))
        if manifest.get('probe_sha256') == digest and manifest.get('audio') == POLICY:
            return POLICY
    raise RuntimeError('Diagnostic launch blocked: current probe lacks verified mute instrumentation. Rebuild it with the muted probe builder.')
