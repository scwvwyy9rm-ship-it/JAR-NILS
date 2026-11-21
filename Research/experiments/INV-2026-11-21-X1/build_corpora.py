"""Bygger frysta korpusar för INV-2026-11-21-X1. Deterministiskt givet pinnade commits."""
import subprocess, json, hashlib, os, sys
DATA = sys.argv[1]; OUT = sys.argv[2]; N_COMMITS = int(sys.argv[3])
CLICK = os.path.join(DATA, 'click'); LOGHUB = os.path.join(DATA, 'loghub')
CLICK_PIN = '08b803cf32ceb2ae6a772c62d5da42757a897d44'
def git(repo, *a): return subprocess.run(['git', '-C', repo, *a], capture_output=True, check=True).stdout
def write(name, objs):
    with open(os.path.join(OUT, name + '.jsonl'), 'w') as f:
        for key, data in objs:
            f.write(json.dumps({'key': key, 'hex': data.hex()}) + '\n')
    tot = sum(len(d) for _, d in objs)
    print(name, len(objs), 'objekt', tot, 'byte', hashlib.sha256(b''.join(d for _, d in objs)).hexdigest()[:16])
os.makedirs(OUT, exist_ok=True)
# K1 loggar
k1 = []
for sysname in sorted(os.listdir(LOGHUB)):
    p = os.path.join(LOGHUB, sysname, f'{sysname}_2k.log')
    if not os.path.isfile(p): continue
    lines = open(p, 'rb').read().splitlines(keepends=True)
    for i in range(0, len(lines), 100):
        k1.append((f'log:{sysname}', b''.join(lines[i:i+100])))
write('K1_logs', k1)
# K2 kod-versionskedjor och K3 simulerad agentsession
commits = git(CLICK, 'rev-list', '--first-parent', '--reverse', f'-n{N_COMMITS}', CLICK_PIN, '--', 'src/click').decode().split()
start = git(CLICK, 'rev-parse', commits[0] + '~1').decode().strip()
k2, k3 = [], []
files0 = [f for f in git(CLICK, 'ls-tree', '-r', '--name-only', start, 'src/click').decode().split() if f.endswith('.py')]
for f in files0:
    k2.append((f'file:{f}', git(CLICK, 'show', f'{start}:{f}')))
for n, c in enumerate(commits):
    changed = [f for f in git(CLICK, 'diff', '--name-only', f'{c}~1', c, '--', 'src/click').decode().split() if f.endswith('.py')]
    k3.append(('tool:show', git(CLICK, 'show', '--stat', '--format=commit %H%nAuthor: %an%nDate: %ad%n%n    %s%n', c)))
    for f in changed:
        try: data = git(CLICK, 'show', f'{c}:{f}')
        except subprocess.CalledProcessError: continue  # borttagen fil
        k2.append((f'file:{f}', data))
        numbered = b''.join(b'%6d\t' % (i + 1) + l for i, l in enumerate(data.splitlines(keepends=True)))
        k3.append((f'tool:read:{f}', numbered))
        k3.append((f'tool:diff:{f}', git(CLICK, 'diff', f'{c}~1', c, '--', f)))
        k3.append((f'tool:grep:{f}', b''.join(b'%d:' % (i + 1) + l for i, l in enumerate(data.splitlines(keepends=True)) if l.startswith((b'def ', b'class ')))))
    if n % 10 == 0:
        k3.append(('tool:ls', git(CLICK, 'ls-tree', '-l', c, 'src/click/')))
write('K2_code', k2)
write('K3_agent', k3)
json.dump({'click_pin': CLICK_PIN, 'click_start': start, 'commits': commits,
           'loghub_head': git(LOGHUB, 'rev-parse', 'HEAD').decode().strip()}, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
