"""Bygger frysta X2-uppgifter ur K2 (click-versionskedjor). Deterministiskt.

Uppgift: givet en tidigare läst version av ett utdrag och en ändring, ange den exakta
första raden i definitionen av funktion F i den AKTUELLA versionen.
Hälften av uppgifterna gäller funktioner vars def-rad ändrades, hälften funktioner i
samma ändrade område vars def-rad INTE ändrades (test av oförändrade värden).
"""
import json, re, sys, os, random, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg

CORP, OUT, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
WIN = 40  # rader före/efter
DEF = re.compile(r'^(\s*)(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(')
objs = [json.loads(l) for l in open(os.path.join(CORP, 'K2_code.jsonl'))]
last = {}
changed, unchanged = [], []
for o in objs:
    key, new = o['key'], bytes.fromhex(o['hex']).decode('utf-8')
    if key in last:
        old = last[key]
        a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        hunks = [op for op in sm.get_opcodes() if op[0] != 'equal']
        old_defs = {}
        for i, l in enumerate(a):
            m = DEF.match(l)
            if m: old_defs.setdefault(m.group(2), []).append(i)
        for tag, i1, i2, j1, j2 in hunks:
            for j in range(max(0, j1 - 15), min(len(b), j2 + 15)):
                m = DEF.match(b[j])
                if not m: continue
                name = m.group(2)
                if sum(1 for l in b if (mm := DEF.match(l)) and mm.group(2) == name) != 1: continue  # entydigt namn
                if len(old_defs.get(name, [])) != 1: continue
                oi = old_defs[name][0]
                lo_n, hi_n = max(0, j - WIN), min(len(b), j + WIN)
                lo_o, hi_o = max(0, oi - WIN), min(len(a), oi + WIN)
                t = {'key': key, 'func': name, 'answer': b[j].rstrip('\r\n'),
                     'old_line': a[oi].rstrip('\r\n'),
                     'old_excerpt': ''.join(a[lo_o:hi_o]), 'new_excerpt': ''.join(b[lo_n:hi_n])}
                if t['old_excerpt'] == t['new_excerpt']: continue
                (changed if t['answer'] != t['old_line'] else unchanged).append(t)
    last[key] = new
def dedup(ts):
    seen, out = set(), []
    for t in ts:
        k = (t['key'], t['func'], t['answer'], t['new_excerpt'])
        if k not in seen: seen.add(k); out.append(t)
    return out
changed, unchanged = dedup(changed), dedup(unchanged)
rng = random.Random(20261121)
sel = rng.sample(changed, min(N // 2, len(changed))) + rng.sample(unchanged, min(N - min(N // 2, len(changed)), len(unchanged)))
rng.shuffle(sel)
for i, t in enumerate(sel):
    t['id'] = f'T{i:03d}'
    t['kind'] = 'ändrad' if t['answer'] != t['old_line'] else 'oförändrad'
    st = crg.State(); st.add('x', t['old_excerpt'].encode())
    e, _ = crg.enc_patch(t['new_excerpt'].encode(), st, 'x')
    assert crg.decode(e, st)[0] == t['new_excerpt'].encode()
    t['patch_hex'] = e.hex()
    t['old_cid'] = crg.cid(t['old_excerpt'].encode()).hex()
json.dump(sel, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('kandidater ändrad/oförändrad:', len(changed), len(unchanged), '-> valda', len(sel),
      {k: sum(1 for t in sel if t['kind'] == k) for k in ('ändrad', 'oförändrad')})
