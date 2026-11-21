"""INV-2026-11-21-X2 – representationskaskad. Kör: python3 -I run_x2.py <modell.gguf> <uppgifter.json> <ut.json>"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg
from llama_cpp import Llama

MODEL, TASKS, OUT = sys.argv[1:4]
THREADS = 4
llm = Llama(model_path=MODEL, n_ctx=8192, n_threads=THREADS, n_batch=512, seed=0, verbose=False, logits_all=False)
tok = lambda s: llm.tokenize(s.encode(), add_bos=False, special=True)

SYS = ("Du är en kodassistent. Svara ENDAST med den exakta efterfrågade kodraden, utan förklaring och utan kodblock.\n"
       "Ändringar kan anges i ENIGMA-IR PATCH-format relativt den tidigare lästa versionen: "
       "⟦KEEP k DEL d⟧ betyder: behåll nästa k rader oförändrade från tidigare version, ta sedan bort d rader; "
       "text som följer infogas därefter. ⟦KEEP k⟧ sist betyder: behåll de återstående k raderna.")


def render_patch(hexenc):
    e = bytes.fromhex(hexenc)
    r = crg.Reader(e); r.take(4); r.u(); r.take(32)
    refs = [r.take(32) for _ in range(r.u())]
    parts = []
    while not r.done():
        op = r.take(1)[0]
        assert op == crg.PATCH
        r.u(); parts.append(f'⟦PATCH bas={refs[0].hex()[:8]}⟧\n')
        for _ in range(r.u()):
            k, d = r.u(), r.u(); ins = r.take(r.u())
            parts.append(f'⟦KEEP {k} DEL {d}⟧\n'); parts.append(ins.decode())
        parts.append(f'⟦KEEP {r.u()}⟧\n')
    return ''.join(parts)


def prefix(t):
    return (f"<|im_start|>system\n{SYS}<|im_end|>\n<|im_start|>user\n"
            f"Tidigare läst version av ett utdrag ur {t['key'][5:]} (cid {t['old_cid'][:8]}):\n```\n{t['old_excerpt']}```\n")


def q(t):
    return (f"Citera den rad i den AKTUELLA versionen som börjar med `def {t['func']}(`, exakt som den står där "
            f"(funktionens signaturrad). Svara bara med den raden.<|im_end|>\n<|im_start|>assistant\n")


def raw_suffix(t):
    return f"Filen har ändrats. Aktuell version av utdraget:\n```\n{t['new_excerpt']}```\n" + q(t)


def ir_suffix(t):
    return f"Filen har ändrats. Ändringen mot tidigare version i ENIGMA-IR:\n{render_patch(t['patch_hex'])}\n" + q(t)


def escalate_suffix(t):
    return ("<|im_end|>\n<|im_start|>user\nSvaret kunde inte verifieras mot källan. "
            "Originalet återhämtat och verifierat (hash ok). " + raw_suffix(t))


def run(text, cached_prefix=None):
    """Kör prompt. Om cached_prefix anges evalueras den först OTIDSATT (motsvarar tidigare tur i KV-cachen)."""
    toks = tok(text)
    llm.reset()
    pre = 0
    if cached_prefix is not None:
        pt = tok(cached_prefix)
        assert toks[:len(pt)] == pt, 'prefix matchar inte tokenvis'
        llm.eval(pt)
        pre = len(pt)
    c0, w0 = time.process_time(), time.perf_counter()
    llm.eval(toks[pre:])
    out = []
    for _ in range(96):
        t = llm.sample(temp=0.0, top_k=1)
        if llm.token_eos() == t or t in (tok('<|im_end|>')[0],):
            break
        out.append(t)
        s = llm.detokenize(out).decode('utf-8', 'replace')
        if any('def ' in l for l in s.split('\n')[:-1]):
            break
        llm.eval([t])
    cpu, wall = time.process_time() - c0, time.perf_counter() - w0
    ans = extract(llm.detokenize(out).decode('utf-8', 'replace'))
    return {'svar': ans, 'nya_tokens': len(toks) - pre, 'gen_tokens': len(out), 'cpu_s': round(cpu, 2), 'wall_s': round(wall, 2),
            'tokens_tot': len(toks)}


def extract(text):
    """Förregistrerad svarstolkning: ta bort kodstaket och omslutande backticks, välj första raden med 'def '."""
    lines = [l for l in text.split('\n') if not l.strip().startswith('```')]
    lines = [l.strip().strip('`').strip() for l in lines]
    lines = [l for l in lines if l]
    for l in lines:
        if 'def ' in l:
            return l
    return lines[0] if lines else ''


def norm(x):
    return x.strip()


def correct(t, a):
    return norm(a) == norm(t['answer'])


def verify(t, a):
    """Deterministisk grundningskontroll som körmiljön kan göra utan facit: avkoda PATCH mot H och
    kontrollera att svaret är en exakt rad i aktuell version och definierar rätt funktion."""
    st = crg.State(); st.add('x', t['old_excerpt'].encode())
    cur = crg.decode(bytes.fromhex(t['patch_hex']), st)[0].decode()
    m = re.match(r'^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(', a)
    return bool(m and m.group(1) == t['func'] and norm(a) in [norm(l) for l in cur.splitlines()])


tasks = json.load(open(TASKS))
res = []
for t in tasks:
    p = prefix(t)
    A = run(p + raw_suffix(t))
    B = run(p + raw_suffix(t), cached_prefix=p)
    C = run(p + ir_suffix(t), cached_prefix=p)
    D = dict(C); D['eskalerad'] = False
    if not verify(t, C['svar']):
        E = run(p + ir_suffix(t) + C['svar'] + escalate_suffix(t), cached_prefix=p + ir_suffix(t))
        D = {'svar': E['svar'], 'eskalerad': True, 'nya_tokens': C['nya_tokens'] + E['nya_tokens'],
             'gen_tokens': C['gen_tokens'] + E['gen_tokens'], 'cpu_s': round(C['cpu_s'] + E['cpu_s'], 2),
             'wall_s': round(C['wall_s'] + E['wall_s'], 2)}
    row = {'id': t['id'], 'kind': t['kind'], 'facit': t['answer']}
    for name, r in (('A_RAW', A), ('B_RAW_cache', B), ('C_IR_cache', C), ('D_kaskad', D)):
        r['korrekt'] = correct(t, r['svar'])
        r['verifierad'] = verify(t, r['svar'])
        row[name] = r
    D['missad_återhämtning'] = (not D['eskalerad']) and not D['korrekt']
    res.append(row)
    print(t['id'], t['kind'], ' '.join(f"{n}={'✓' if row[n]['korrekt'] else '✗'}" for n in ('A_RAW', 'C_IR_cache', 'D_kaskad')),
          'esk' if D['eskalerad'] else '', flush=True)
    json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
