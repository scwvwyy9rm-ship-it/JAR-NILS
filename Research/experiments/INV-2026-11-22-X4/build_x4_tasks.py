"""Bygger frysta X4-uppgifter: små Python-program där en ändring påverkar tolkningen av oförändrade rader.

Facit = faktisk körning av den aktuella versionen. Deterministiskt (slumpfrö).
Ändringstyper:
  const   : en konstant högst upp ändras; den används långt ned i oförändrade funktioner
  op      : en operator i en hjälpfunktion ändras; anropskedjan nedåt är oförändrad
  default : ett standardargument ändras; anroparen (oförändrad) förlitar sig på det
  control : en ändring i en distraktorfunktion som inte anropas (utskriften ska vara OFÖRÄNDRAD)
"""
import json, random, sys, os, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg

OUT, N, SEED = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = random.Random(SEED)
WORDS = ['alpha', 'beta', 'gamma', 'delta', 'omega', 'sigma', 'kappa', 'theta', 'lambda_', 'zeta', 'rho', 'tau']


def make_program():
    names = rng.sample(WORDS, 6)
    c1, c2, c3 = (n.upper() for n in names[:3])
    v1, v2, v3 = rng.randint(2, 9), rng.randint(2, 9), rng.randint(1, 5)
    ops = {'h1': rng.choice(['+', '-']), 'h2': rng.choice(['*', '+'])}
    d = rng.randint(1, 4)
    lines = [f'{c1} = {v1}\n', f'{c2} = {v2}\n', f'{c3} = {v3}\n', '\n']
    distract = []
    for i in range(rng.randint(4, 6)):  # distraktorer (anropas aldrig)
        nm = f'unused_{names[3]}_{i}'
        k = rng.randint(2, 9)
        distract.append(nm)
        lines += [f'def {nm}(x):\n', f'    y = x * {k}\n', f'    if y > {rng.randint(10, 50)}:\n', f'        y = y - {k}\n', '    return y\n', '\n']
    lines += [f'def {names[3]}(x):\n', f'    return x {ops["h1"]} {c1}\n', '\n',
              f'def {names[4]}(x, step={d}):\n', f'    return x {ops["h2"]} {c2} + step\n', '\n']
    for i in range(rng.randint(2, 4)):  # fler distraktorer mellan hjälpare och main
        nm = f'unused_{names[5]}_{i}'
        distract.append(nm)
        lines += [f'def {nm}(s):\n', f'    return s.strip().lower() + "{rng.choice(WORDS)}"\n', '\n']
    lines += ['def main():\n', f'    v = {names[3]}({rng.randint(1, 9)})\n', f'    v = {names[4]}(v)\n',
              f'    v = v + {c3}\n', '    return v\n', '\n', 'print(main())\n']
    return lines, dict(c1=c1, c2=c2, c3=c3, h1=names[3], h2=names[4], distract=distract)


def run(src):
    return subprocess.run([sys.executable, '-I', '-c', src], capture_output=True, text=True, timeout=10).stdout.strip()


def edit(lines, meta, kind):
    new = list(lines)
    if kind == 'const':
        i = rng.choice([0, 1, 2])
        name, val = new[i].split(' = ')
        nv = int(val) + rng.choice([-1, 1]) * rng.randint(1, 3)
        new[i] = f'{name} = {nv}\n'
    elif kind == 'op':
        h = rng.choice(['h1', 'h2'])
        i = next(j for j, l in enumerate(new) if l.startswith(f'def {meta[h]}(')) + 1
        swap = {'+': '-', '-': '+', '*': '+'}
        m = re.search(r' ([+\-*]) ', new[i])
        new[i] = new[i][:m.start(1)] + swap[m.group(1)] + new[i][m.end(1):]
    elif kind == 'default':
        i = next(j for j, l in enumerate(new) if l.startswith(f'def {meta["h2"]}('))
        m = re.search(r'step=(\d+)', new[i])
        nd = int(m.group(1)) + rng.randint(1, 3)
        new[i] = new[i][:m.start(1)] + str(nd) + new[i][m.end(1):]
    elif kind == 'control':
        nm = rng.choice(meta['distract'])
        i = next(j for j, l in enumerate(new) if l.startswith(f'def {nm}(')) + 1
        new[i] = re.sub(r'\d+', lambda m: str(int(m.group()) + 1), new[i], count=1) if re.search(r'\d', new[i]) else new[i].replace('lower', 'upper')
    return new


tasks = []
kinds = ['const', 'op', 'default'] * ((N * 2 // 3) // 3 + 1)
kinds = kinds[:N - N // 3] + ['control'] * (N // 3)
rng.shuffle(kinds)
for idx, kind in enumerate(kinds):
    for _ in range(100):
        lines, meta = make_program()
        new = edit(lines, meta, kind)
        old_src, new_src = ''.join(lines), ''.join(new)
        if old_src == new_src:
            continue
        o_old, o_new = run(old_src), run(new_src)
        if not re.fullmatch(r'-?\d+', o_old or '') or not re.fullmatch(r'-?\d+', o_new or ''):
            continue
        if kind != 'control' and o_old == o_new:
            continue
        if kind == 'control' and o_old != o_new:
            continue
        break
    st = crg.State(); st.add('x', old_src.encode())
    e, _ = crg.enc_patch(new_src.encode(), st, 'x')
    assert crg.decode(e, st)[0] == new_src.encode()
    tasks.append({'id': f'P{idx:03d}', 'kind': kind, 'key': 'file:prog.py', 'func': 'main',
                  'old_excerpt': old_src, 'new_excerpt': new_src, 'answer': o_new, 'old_answer': o_old,
                  'patch_hex': e.hex(), 'old_cid': crg.cid(old_src.encode()).hex(),
                  'changed_idents': sorted(set(re.findall(r'[A-Za-z_]\w*', ''.join(l for l, m in zip(new, lines) if l != m)))
                                          - {'def', 'return', 'x', 'step', 'if', 'y', 's'})})
json.dump(tasks, open(OUT, 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(len(tasks), Counter(t['kind'] for t in tasks), 'rader/program ~', sum(t['new_excerpt'].count('\n') for t in tasks) // len(tasks))
