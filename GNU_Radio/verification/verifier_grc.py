#!/usr/bin/env python3
"""Vérification des graphes de flux .grc SANS GNU Radio.

1. Contrôle structurel : blocs connectés existants, entrées toutes alimentées,
   types de ports compatibles, variables définies, filtres sous Nyquist.
2. Exécution numérique : chaque bloc est réinterprété avec NumPy selon sa
   définition dans GNU Radio (traitement par tableaux complets, dans l'ordre
   topologique), puis les sorties des démodulateurs sont comparées au message.

Usage : python3 verifier_grc.py ../am_tx_rx_sim.grc [...]
Dépendances : numpy, pyyaml.
"""
import sys, math, re, yaml, numpy as np

DURATION = 0.25          # secondes simulées (échelle du débit audio)

# ---------------------------------------------------------------- types des ports
def ports(bid, p):
    t = p.get('type', '')
    f, c, b = 'float', 'complex', 'byte'
    m = {'analog_sig_source_x': ([], [t]), 'analog_const_source_x': ([], [t]), 'blocks_throttle': ([t], [t]),
         'rational_resampler_xxx': ([{'fff': f, 'ccc': c, 'ccf': c}.get(t, t)], [{'fff': f, 'ccc': c, 'ccf': c}.get(t, t)]),
         'blocks_repeat': ([t], [t]), 'blocks_multiply_const_vxx': ([t], [t]), 'blocks_add_const_vxx': ([t], [t]),
         'blocks_float_to_complex': ([f, f], [c]), 'blocks_multiply_xx': ([t] * int(p.get('num_inputs', 2)), [t]),
         'blocks_add_xx': ([t] * int(p.get('num_inputs', 2)), [t]), 'analog_noise_source_x': ([], [t]),
         'low_pass_filter': ([{'fir_filter_ccf': c, 'fir_filter_fff': f}.get(t, t)], [{'fir_filter_ccf': c, 'fir_filter_fff': f}.get(t, t)]),
         'band_pass_filter': ([c], [c]), 'blocks_complex_to_mag': ([c], [f]), 'blocks_complex_to_arg': ([c], [f]),
         'blocks_complex_to_real': ([c], [f]), 'dc_blocker_xx': ([f], [f]), 'analog_quadrature_demod_cf': ([c], [f]),
         'analog_frequency_modulator_fc': ([f], [c]), 'analog_phase_modulator_fc': ([f], [c]), 'hilbert_fc': ([f], [c]),
         'blocks_conjugate_cc': ([c], [c]), 'analog_random_source_x': ([], [b]), 'blocks_char_to_float': ([b], [f]),
         'blocks_moving_average_xx': ([t], [t]), 'digital_binary_slicer_fb': ([f], [b]), 'audio_sink': ([f], []),
         'qtgui_time_sink_x': ([t] * int(p.get('nconnections', 1)), []),
         'blocks_delay': ([t], [t]), 'blocks_vector_source_x': ([], [t]), 'blocks_repack_bits_bb': ([b], [b]), 'epy_block': ([f], []), 'qtgui_freq_sink_x': ([t] * int(p.get('nconnections', 1)), [])}
    return m[bid]

# ---------------------------------------------------------------- outils de filtrage (firdes)
def hamming(n): return 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(n) / (n - 1))
def ntaps(fs, width, att=53.0):
    n = int(att * fs / (22.0 * width)); return n | 1
def firdes_lp(gain, fs, cut, width):
    n = ntaps(fs, width); M = (n - 1) / 2; k = np.arange(n) - M
    h = 2 * cut / fs * np.sinc(2 * cut / fs * k) * hamming(n)
    return gain * h / h.sum()
def firdes_cbp(gain, fs, lo, hi, width):
    h = firdes_lp(1.0, fs, (hi - lo) / 2, width); n = len(h); k = np.arange(n) - (n - 1) / 2
    return gain * h * np.exp(2j * np.pi * (lo + hi) / 2 * k / fs)
def kaiser_lp(gain, fs, cut, width, beta=7.0):
    """firdes.low_pass avec fenêtre de Kaiser, comme le filtre par défaut du Rational Resampler"""
    a = beta / 0.1102 + 8.7; n = int(a * fs / (22.0 * width)) | 1; M = (n - 1) / 2; k = np.arange(n) - M
    h = 2 * cut / fs * np.sinc(2 * cut / fs * k) * np.kaiser(n, beta)
    return gain * h / h.sum()
def hilbert_taps(n):
    k = np.arange(n) - (n - 1) / 2; h = np.zeros(n)
    odd = (k % 2 != 0); h[odd] = 2 / (np.pi * k[odd]); return h * hamming(n)

# ---------------------------------------------------------------- bloc Python intégré
def run_epy(p, x, ev):
    """exécute le code du bloc Python intégré avec un module gnuradio minimal (gr.sync_block)"""
    import types, inspect
    gr = types.ModuleType('gr')
    class sync_block:
        def __init__(self, name='', in_sig=None, out_sig=None): self.name = name
    gr.sync_block = sync_block
    pkg = types.ModuleType('gnuradio'); pkg.gr = gr
    sys.modules['gnuradio'] = pkg; sys.modules['gnuradio.gr'] = gr
    ns = {}; exec(compile(str(p['_source_code']), 'epy_block', 'exec'), ns)
    args = inspect.signature(ns['blk'].__init__).parameters
    kw = {k: ev(p[k]) for k in args if k != 'self' and k in p}
    b = ns['blk'](**kw)
    for k in range(0, len(x), 4096):                     # traitement par paquets, comme l'ordonnanceur
        b.work([x[k:k + 4096].astype(np.float32)], [])
    return b

# ---------------------------------------------------------------- interpréteur
def run(path, duration=None):
    D = duration or DURATION
    g = yaml.safe_load(open(path, encoding='utf8'))
    B = {b['name']: b for b in g['blocks'] if b['states']['state'] == 'enabled'}
    env = {'math': math, 'int': int, 'min': min, 'max': max, 'abs': abs}
    for _ in range(4):                                  # variables (ordre quelconque)
        for b in B.values():
            if b['id'] in ('variable', 'qtgui_range'):
                try: env[b['name']] = eval(str(b['parameters']['value']), {}, env)
                except Exception: pass
    ev = lambda s: eval(str(s), {}, env)
    conns = [c for c in g['connections'] if c[0] in B and c[2] in B]
    errs = []
    # contrôle structurel
    for c in g['connections']:
        for nm in (c[0], c[2]):
            if nm not in {b['name'] for b in g['blocks']}: errs.append(f"connexion vers un bloc inexistant : {nm}")
    inputs = {}
    for c in conns: inputs.setdefault(c[2], {})[int(c[3])] = (c[0], int(c[1]))
    for nm, b in B.items():
        if b['id'] in ('variable', 'qtgui_range', 'import'): continue
        ins, outs = ports(b['id'], b['parameters'])
        for i, ti in enumerate(ins):
            if i not in inputs.get(nm, {}): errs.append(f"{nm} : entrée {i} non connectée"); continue
            src, sp = inputs[nm][i]; to = ports(B[src]['id'], B[src]['parameters'])[1][sp]
            if to != ti: errs.append(f"type incompatible {src}[{sp}]={to} -> {nm}[{i}]={ti}")
        for k, v in b['parameters'].items():
            if k.startswith('_'): continue
            for ident in re.findall(r'\b[a-z_][a-z_0-9]*\b', re.sub(r"(['\"]).*?\1", '', str(v))):
                if ident in ('window', 'analog', 'qtgui', 'math', 'pi', 'win', 'hamming', 'true', 'false', 'gr', 'list', 'bytes', 'len', 'encode') or ident in env: continue
                if k in ('alias', 'comment', 'label', 'label1', 'label2', 'label3', 'name', 'ylabel', 'units', 'device_name', 'tr_tag', 'yunit', 'gui_hint', 'imports', 'orient', 'type', 'win', 'wintype', 'waveform', 'noise_type', 'tr_mode', 'tr_slope', 'description'): continue
                errs.append(f"{nm}.{k} : identifiant inconnu « {ident} »")
        if b['id'] in ('low_pass_filter',):
            if ev(b['parameters']['cutoff_freq']) >= ev(b['parameters']['samp_rate']) / 2: errs.append(f"{nm} : coupure au-delà de Nyquist")
    # rates et exécution dans l'ordre topologique
    rate, out = {}, {}
    order, done = [], set()
    while len(done) < len(B):
        prog = False
        for nm, b in B.items():
            if nm in done: continue
            if all(s in done for s, _ in inputs.get(nm, {}).values()):
                order.append(nm); done.add(nm); prog = True
        if not prog: errs.append("boucle ou bloc isolé"); break
    base = env.get('audio_rate', env.get('samp_rate'))
    rng = np.random.default_rng(0); captures = {}
    for nm in order:
        b = B[nm]; p = b['parameters']; bid = b['id']
        x = [out[s][sp] for s, sp in [inputs[nm][i] for i in sorted(inputs.get(nm, {}))]] if nm in inputs else []
        r = [rate[s] for s, _ in [inputs[nm][i] for i in sorted(inputs.get(nm, {}))]] if nm in inputs else []
        y = None; fr = r[0] if r else None
        if bid in ('variable', 'qtgui_range', 'import'): continue
        if bid == 'analog_sig_source_x':
            fr = ev(p['samp_rate']); n = int(D * fr)
            tt = np.arange(n) / fr; ph = 2 * np.pi * ev(p['freq']) * tt + ev(p.get('phase', 0))
            y = ev(p['amp']) * (np.exp(1j * ph) if p['type'] == 'complex' else np.cos(ph)) + ev(p.get('offset', 0))
        elif bid == 'analog_random_source_x':
            fr = env['samp_rate'] / env['sps']; n = int(D * fr) + 1
            y = rng.integers(ev(p['min']), ev(p['max']), n)
        elif bid == 'blocks_vector_source_x':
            fr = env['samp_rate'] / env['sps'] / 8; v = np.array(ev(p['vector']), dtype=np.uint8)
            n = int(D * fr) + 1; y = np.tile(v, n // len(v) + 1)[:n] if ev(p['repeat']) else v
        elif bid == 'blocks_repack_bits_bb':
            k, l = ev(p['k']), ev(p['l']); assert (k, l) == (8, 1) and 'MSB' in str(p['endianness'])
            y = np.unpackbits(x[0].astype(np.uint8)); fr = fr * 8
        elif bid == 'epy_block':
            captures[nm] = run_epy(p, x[0], ev); y = None
        elif bid in ('analog_noise_source_x', 'analog_const_source_x'):
            fr = None                                   # source sans débit propre : alignée sur l'autre entrée
        elif bid in ('blocks_throttle', 'qtgui_time_sink_x', 'qtgui_freq_sink_x', 'audio_sink'):
            y = x[0] if x else None
            if bid in ('qtgui_time_sink_x', 'qtgui_freq_sink_x'): captures[nm] = (x, r)
        elif bid == 'rational_resampler_xxx':
            L = ev(p['interp']); z = np.zeros(len(x[0]) * L, dtype=x[0].dtype); z[::L] = x[0]
            y = np.convolve(z, kaiser_lp(L, L, 0.45, 0.1))[:len(z)]; fr = fr * L
        elif bid == 'blocks_repeat':
            L = ev(p['interp']); y = np.repeat(x[0], L); fr = fr * L
        elif bid == 'blocks_multiply_const_vxx': y = x[0] * ev(p['const'])
        elif bid == 'blocks_add_const_vxx': y = x[0] + ev(p['const'])
        elif bid == 'blocks_float_to_complex':
            im = x[1] if len(x) > 1 and x[1] is not None else 0.0
            if len(x) > 1 and B[inputs[nm][1][0]]['id'] == 'analog_const_source_x': im = ev(B[inputs[nm][1][0]]['parameters']['const'])
            y = x[0] + 1j * im
        elif bid in ('blocks_multiply_xx', 'blocks_add_xx'):
            n = min(len(v) for v in x if v is not None)
            arrs = [v[:n] if v is not None else None for v in x]
            if bid == 'blocks_add_xx':
                y = sum(a for a in arrs if a is not None)
                for (s, _), a in zip([inputs[nm][i] for i in sorted(inputs[nm])], arrs):
                    if B[s]['id'] == 'analog_noise_source_x':
                        amp = ev(B[s]['parameters']['amp'])
                        y = y + amp / np.sqrt(2) * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
            else:
                y = arrs[0] * arrs[1]
            fr = [q for q in r if q][0]
        elif bid == 'low_pass_filter':
            h = firdes_lp(ev(p['gain']), ev(p['samp_rate']), ev(p['cutoff_freq']), ev(p['width']))
            d = ev(p['decim']); y = np.convolve(x[0], h)[:len(x[0])][::d]; fr = fr / d
        elif bid == 'band_pass_filter':
            h = firdes_cbp(ev(p['gain']), ev(p['samp_rate']), ev(p['low_cutoff_freq']), ev(p['high_cutoff_freq']), ev(p['width']))
            y = np.convolve(x[0], h)[:len(x[0])]
        elif bid == 'hilbert_fc':
            n = ev(p['num_taps']); h = hilbert_taps(n); d = (n - 1) // 2
            xd = np.concatenate([np.zeros(d), x[0]])[:len(x[0])]
            y = xd + 1j * np.convolve(x[0], h)[:len(x[0])]
        elif bid == 'blocks_conjugate_cc': y = np.conj(x[0])
        elif bid == 'blocks_delay':
            D = ev(p['delay']); y = np.concatenate([np.zeros(D, dtype=x[0].dtype), x[0][:len(x[0]) - D]])
        elif bid == 'blocks_complex_to_mag': y = np.abs(x[0])
        elif bid == 'blocks_complex_to_arg': y = np.angle(x[0])
        elif bid == 'blocks_complex_to_real': y = np.real(x[0])
        elif bid == 'dc_blocker_xx':
            D = ev(p['length']); k = np.ones(D) / D
            y = x[0] - np.convolve(np.convolve(x[0], k)[:len(x[0])], k)[:len(x[0])]
        elif bid == 'analog_quadrature_demod_cf':
            z = x[0]; y = ev(p['gain']) * np.concatenate([[0], np.angle(z[1:] * np.conj(z[:-1]))])
        elif bid == 'analog_frequency_modulator_fc':
            y = np.exp(1j * np.cumsum(ev(p['sensitivity']) * x[0]))
        elif bid == 'analog_phase_modulator_fc':
            y = np.exp(1j * ev(p['sensitivity']) * x[0])
        elif bid == 'blocks_char_to_float': y = x[0].astype(float) * ev(p.get('scale', 1))
        elif bid == 'blocks_moving_average_xx':
            Lm = ev(p['length']); y = ev(p['scale']) * np.convolve(x[0], np.ones(Lm))[:len(x[0])]
        elif bid == 'digital_binary_slicer_fb': y = (x[0] > 0).astype(np.int8)
        else:
            errs.append(f"bloc non interprété : {bid}")
        out[nm] = [y]; rate[nm] = fr
    return errs, captures, env

def compare(a, b, fs):
    """Corrélation maximale entre deux signaux après recherche du retard."""
    n = min(len(a), len(b)); a = a[n // 4:n]; b = b[n // 4:n]
    best = (0, 0)
    for d in range(0, int(0.01 * fs)):
        aa, bb = a[:len(a) - d], b[d:]
        cc = np.corrcoef(aa, bb)[0, 1]
        if cc > best[0]: best = (cc, d)
    return best

if __name__ == '__main__':
    tot_ok = True
    for path in sys.argv[1:]:
        errs, cap, env = run(path, 1.5 if 'texte' in path else None)
        print(f"\n=== {path.split('/')[-1]} ===")
        for e in errs: print("  ERREUR :", e)
        if 'texte' in path:
            b = [v for v in cap.values() if hasattr(v, 'messages')][0]
            ref = eval(str([bb for bb in yaml.safe_load(open(path, encoding='utf8'))['blocks'] if bb['name'] == 'texte'][0]['parameters']['value']))
            ok = len(b.messages) >= 2 and all(m == ref for m in b.messages) and not errs
            print(f"  {'OK   ' if ok else 'ECHEC'} {len(b.messages)} trames reçues, toutes identiques au texte émis : {ok}")
            tot_ok &= ok; continue
        x, r = cap['scope']
        if len(x) >= 2:
            if False:
                ref, dec = x[0], x[2]
                sps = env['sps']; n = min(len(ref), len(dec)) // sps - 4
                bt = (ref[sps // 2::sps][:n] > 0).astype(int)
                best = min(range(0, 3 * sps), key=lambda d: np.mean(bt[4:n - 4] != (dec[d + sps // 2::sps][:n] > 0.5).astype(int)[4:n - 4]))
                ber = np.mean(bt[4:n - 4] != (dec[best + sps // 2::sps][:n] > 0.5).astype(int)[4:n - 4])
                ok = ber == 0 and not errs
                print(f"  {'OK   ' if ok else 'ECHEC'} bits décidés identiques aux bits émis (taux d'erreur {ber:.4f}, retard {best} échantillons)")
            else:
                cc, d = compare(x[0], x[1], r[0])
                ok = cc > 0.99 and not errs
                print(f"  {'OK   ' if ok else 'ECHEC'} message démodulé / message émis : corrélation {cc:.4f} (retard {1e3 * d / r[0]:.2f} ms)")
            tot_ok &= ok
    print("\nRésultat global :", "OK" if tot_ok else "ECHEC")
