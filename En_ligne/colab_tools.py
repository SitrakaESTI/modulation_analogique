"""Exécution réelle des graphes de flux .grc avec GNU Radio, sans interface graphique (Google Colab).
Les afficheurs QT GUI sont remplacés par des Vector Sink, les curseurs QT GUI Range par des variables,
puis grcc génère le programme Python, qui est exécuté pendant une durée fixée."""
import yaml, os, sys, subprocess, importlib, time, io, contextlib
import numpy as np

def headless(grc, out_dir='/content/hl', **valeurs):
    g = yaml.safe_load(open(grc, encoding='utf8'))
    fid = g['options']['parameters']['id'] + '_hl'
    g['options']['parameters'].update({'id': fid, 'generate_options': 'no_gui', 'run_options': 'run'})
    blocs, conns, sinks = [], [], {}
    for b in g['blocks']:
        p = b['parameters']
        if b['id'] == 'qtgui_range':
            b = {'name': b['name'], 'id': 'variable', 'parameters': {'comment': '', 'value': p['value']}, 'states': b['states']}
        if b['name'] in valeurs:
            b['parameters']['value'] = str(valeurs[b['name']])
        if b['id'] in ('qtgui_time_sink_x', 'qtgui_freq_sink_x'):
            n = int(p.get('nconnections', 1)); sinks[b['name']] = (p['type'], n, b['id'])
            for k in range(n):
                blocs.append({'name': f"{b['name']}_{k}", 'id': 'blocks_vector_sink_x',
                              'parameters': {'affinity': '', 'alias': '', 'comment': '', 'type': p['type'], 'vlen': '1', 'reserve_items': '1024'},
                              'states': b['states']})
            continue
        blocs.append(b)
    for c in g['connections']:
        if c[2] in sinks: conns.append([c[0], c[1], f"{c[2]}_{c[3]}", '0'])
        else: conns.append(c)
    g['blocks'], g['connections'] = blocs, conns
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, fid + '.grc'); yaml.safe_dump(g, open(path, 'w', encoding='utf8'), allow_unicode=True, sort_keys=False)
    return path, fid, sinks

def executer(grc, duree=2.0, out_dir='/content/hl', **valeurs):
    path, fid, sinks = headless(grc, out_dir, **valeurs)
    r = subprocess.run(['grcc', '-o', out_dir, path], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stdout + r.stderr)
    sys.path.insert(0, out_dir)
    mod = importlib.import_module(fid); mod = importlib.reload(mod)
    tb = getattr(mod, fid)()
    tb.start(); time.sleep(duree); tb.stop(); tb.wait()
    data = {}
    for s, (typ, n, kind) in sinks.items():
        data[s] = (kind, [np.array(getattr(tb, f'{s}_{k}').data()) for k in range(n)])
    return tb, data

def correlation(a, b, fs, max_retard=0.02):
    n = min(len(a), len(b)); a, b = a[n // 4:n], b[n // 4:n]; best = (0.0, 0)
    for d in range(int(max_retard * fs)):
        cc = np.corrcoef(a[:len(a) - d], b[d:])[0, 1]
        if cc > best[0]: best = (cc, d)
    return best
