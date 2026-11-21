"""INV-2026-11-21-X3a – strukturstyrd KV-återanvändning (H5, deterministisk nivå, ingen träning).

Kör: python3 -I run_x3a.py <modell.gguf> <uppgifter.json> <ut.json> [--selftest]

Armar (gemensamt: rubrik + tidigare läst utdrag har redan evaluerats, dvs. ligger i KV-cachen):
  FULL      : aktuellt utdrag beräknas från grunden efter rubriken (övre kvalitetsgräns, full kostnad)
  IR        : tidigare utdrag cachat; ENIGMA-IR PATCH + fråga beräknas (som X2 arm C)
  REUSE     : tidigare utdrag cachat; KV redigeras på plats enligt PATCH: borttagna rader tas bort,
              efterföljande celler flyttas (RoPE-justering), infogade rader beräknas på sina positioner.
              Kopierade rader återanvänds utan omberäkning (H5).
  REUSE+NBR : som REUSE men raderna närmast varje ändring (±1) beräknas om (deterministisk selektiv omberäkning).
"""
import sys, os, json, time, re, ctypes
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg
import llama_cpp as L
from llama_cpp import Llama

MODEL, TASKS, OUT = sys.argv[1:4]
SELFTEST = '--selftest' in sys.argv
llm = Llama(model_path=MODEL, n_ctx=8192, n_threads=4, n_batch=512, seed=0, verbose=False)
CTX = llm._ctx.ctx
MEM = L.llama_get_memory(CTX) if hasattr(L, 'llama_get_memory') else None
NV = llm.n_vocab()
IM_END = llm.tokenize(b'<|im_end|>', add_bos=False, special=True)[0]
EOS = llm.token_eos()


def tk(s, special=False):
    return llm.tokenize(s.encode(), add_bos=False, special=special)


def seq_rm(p0, p1):
    if MEM is not None:
        L.llama_memory_seq_rm(MEM, 0, p0, p1)
    else:
        L.llama_kv_self_seq_rm(CTX, 0, p0, p1)


def seq_add(p0, p1, d):
    if MEM is not None:
        L.llama_memory_seq_add(MEM, 0, p0, p1, d)
    else:
        L.llama_kv_self_seq_add(CTX, 0, p0, p1, d)


def clear():
    if MEM is not None:
        L.llama_memory_clear(MEM, True)
    else:
        L.llama_kv_self_clear(CTX)


def decode(tokens, positions, want_logits=False):
    """Evaluera tokens på givna positioner i sekvens 0. Returnerar logits för sista token om önskat."""
    out = None
    for s in range(0, len(tokens), 512):
        tt, pp = tokens[s:s + 512], positions[s:s + 512]
        b = L.llama_batch_init(len(tt), 0, 1)
        try:
            b.n_tokens = len(tt)
            for i, (t, p) in enumerate(zip(tt, pp)):
                b.token[i] = t; b.pos[i] = p; b.n_seq_id[i] = 1; b.seq_id[i][0] = 0
                b.logits[i] = 1 if (want_logits and s + i == len(tokens) - 1) else 0
            rc = L.llama_decode(CTX, b)
            if rc != 0:
                raise RuntimeError(f'llama_decode rc={rc}')
            if want_logits and s + len(tt) == len(tokens):
                ptr = L.llama_get_logits_ith(CTX, len(tt) - 1)
                out = np.ctypeslib.as_array(ptr, shape=(NV,)).copy()
        finally:
            L.llama_batch_free(b)
    return out


def generate(first_logits, next_pos, max_new=96):
    out = []
    logits = first_logits
    pos = next_pos
    for _ in range(max_new):
        t = int(np.argmax(logits))
        if t in (EOS, IM_END):
            break
        out.append(t)
        s = llm.detokenize(out).decode('utf-8', 'replace')
        if any('def ' in l for l in s.split('\n')[:-1]):
            break
        logits = decode([t], [pos], want_logits=True); pos += 1
    return llm.detokenize(out).decode('utf-8', 'replace'), len(out)


def extract(text):
    lines = [l for l in text.split('\n') if not l.strip().startswith('```')]
    lines = [l.strip().strip('`').strip() for l in lines]
    lines = [l for l in lines if l]
    for l in lines:
        if 'def ' in l:
            return l
    return lines[0] if lines else ''


SYS = ("Du är en kodassistent. Svara ENDAST med den exakta efterfrågade kodraden, utan förklaring och utan kodblock.\n"
       "Ändringar kan anges i ENIGMA-IR PATCH-format relativt den tidigare lästa versionen: "
       "⟦KEEP k DEL d⟧ betyder: behåll nästa k rader oförändrade från tidigare version, ta sedan bort d rader; "
       "text som följer infogas därefter. ⟦KEEP k⟧ sist betyder: behåll de återstående k raderna.")


def header(t):
    return f"<|im_start|>system\n{SYS}<|im_end|>\n<|im_start|>user\nUtdrag ur {t['key'][5:]}:\n```\n"


def question(t):
    return (f"```\nCitera den rad i den AKTUELLA versionen av utdraget som börjar med `def {t['func']}(`, exakt som den står där "
            f"(funktionens signaturrad). Svara bara med den raden.<|im_end|>\n<|im_start|>assistant\n")


def ir_text(t):
    e = bytes.fromhex(t['patch_hex']); r = crg.Reader(e); r.take(4); r.u(); r.take(32)
    refs = [r.take(32) for _ in range(r.u())]
    parts = []
    while not r.done():
        assert r.take(1)[0] == crg.PATCH; r.u()
        parts.append(f'⟦PATCH bas={refs[0].hex()[:8]}⟧\n')
        for _ in range(r.u()):
            k, d = r.u(), r.u(); ins = r.take(r.u())
            parts.append(f'⟦KEEP {k} DEL {d}⟧\n'); parts.append(ins.decode())
        parts.append(f'⟦KEEP {r.u()}⟧\n')
    return ''.join(parts)


def patch_ops(t):
    """Radvis redigeringslista ur PATCH: [(keep, delete, [infogade rader])], tail_keep."""
    e = bytes.fromhex(t['patch_hex']); r = crg.Reader(e); r.take(4); r.u(); r.take(32)
    [r.take(32) for _ in range(r.u())]
    assert r.take(1)[0] == crg.PATCH; r.u()
    eds = []
    for _ in range(r.u()):
        k, d = r.u(), r.u(); ins = r.take(r.u()).decode()
        eds.append((k, d, ins.splitlines(keepends=True)))
    return eds, r.u()


def line_tokens(lines):
    return [tk(l) for l in lines]


def timed(fn):
    c0, w0 = time.process_time(), time.perf_counter()
    r = fn()
    return r, time.process_time() - c0, time.perf_counter() - w0


def base_cache(t):
    """Rubrik + tidigare utdrag evalueras (otidsatt = tidigare tur). Returnerar radlayout."""
    clear()
    h = tk(header(t), special=True)
    decode(h, list(range(len(h))))
    pos = len(h)
    layout = []  # (start_pos, ntok) per gammal rad
    toks = line_tokens(t['old_excerpt'].splitlines(keepends=True))
    flat, fpos = [], []
    for lt in toks:
        layout.append([pos, len(lt)]); flat += lt; fpos += list(range(pos, pos + len(lt))); pos += len(lt)
    decode(flat, fpos)
    return len(h), layout, pos


def arm_full(t):
    clear()
    h = tk(header(t), special=True)
    decode(h, list(range(len(h))))
    def go():
        new = [x for lt in line_tokens(t['new_excerpt'].splitlines(keepends=True)) for x in lt]
        q = tk(question(t), special=True)
        seq = new + q
        lg = decode(seq, list(range(len(h), len(h) + len(seq))), want_logits=True)
        txt, ng = generate(lg, len(h) + len(seq))
        return txt, len(seq), ng
    (txt, n, ng), cpu, wall = timed(go)
    return {'svar': extract(txt), 'beräknade_tokens': n, 'gen_tokens': ng, 'cpu_s': round(cpu, 2), 'wall_s': round(wall, 2)}


def arm_ir(t):
    hlen, layout, pos = base_cache(t)
    def go():
        seq = tk("```\nFilen har ändrats. Ändringen mot tidigare version i ENIGMA-IR:\n" + ir_text(t), special=True)[0:]
        seq += tk(question(t)[4:], special=True)  # utan inledande ``` (redan stängt ovan)
        lg = decode(seq, list(range(pos, pos + len(seq))), want_logits=True)
        txt, ng = generate(lg, pos + len(seq))
        return txt, len(seq), ng
    (txt, n, ng), cpu, wall = timed(go)
    return {'svar': extract(txt), 'beräknade_tokens': n, 'gen_tokens': ng, 'cpu_s': round(cpu, 2), 'wall_s': round(wall, 2)}


def arm_reuse(t, nbr):
    hlen, layout, end = base_cache(t)
    eds, tail = patch_ops(t)

    def go():
        computed = 0
        # bygg ny radlista: ('old', idx) eller ('new', text); markera grannar till ändringar
        plan, oi = [], 0
        for k, d, ins in eds:
            plan += [('old', oi + j) for j in range(k)]; oi += k
            dels = list(range(oi, oi + d)); oi += d
            plan += [('del', x) for x in dels]
            plan += [('new', s) for s in ins]
        plan += [('old', oi + j) for j in range(tail)]
        kept = [p for p in plan if p[0] != 'del']
        recompute = set()
        if nbr:
            for i, p in enumerate(kept):
                if p[0] == 'new':
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(kept) and kept[j][0] == 'old':
                            recompute.add(kept[j][1])
            # även rader som grannade en borttagning
            for i, p in enumerate(plan):
                if p[0] == 'del':
                    for j in (i - 1, i + 1):
                        if 0 <= j < len(plan) and plan[j][0] == 'old':
                            recompute.add(plan[j][1])
        # 1) ta bort raderade och omberäknade gamla rader ur KV
        for p in plan:
            if p[0] == 'del' or (p[0] == 'old' and p[1] in recompute):
                s, n = layout[p[1]]
                seq_rm(s, s + n)
        # 2) placera kvarvarande gamla rader på nya positioner, från slutet för att undvika kollisioner
        newpos, pos = [], hlen
        for p in kept:
            if p[0] == 'old':
                n = layout[p[1]][1]
            else:
                n = len(tk(p[1]))
            newpos.append(pos); pos += n
        new_end = pos
        # flytta i två steg via ett högt temporärt område för att undvika överlapp
        OFF = 1 << 20
        for p, np_ in zip(kept, newpos):
            if p[0] == 'old' and p[1] not in recompute:
                s, n = layout[p[1]]
                seq_add(s, s + n, OFF + np_ - s)
        for p, np_ in zip(kept, newpos):
            if p[0] == 'old' and p[1] not in recompute:
                n = layout[p[1]][1]
                seq_add(OFF + np_, OFF + np_ + n, -OFF)
        # 3) beräkna infogade och omberäknade rader på sina positioner, i positionsordning
        toks, poss = [], []
        for p, np_ in zip(kept, newpos):
            if p[0] == 'new':
                lt = tk(p[1])
            elif p[1] in recompute:
                lt = tk(t['old_excerpt'].splitlines(keepends=True)[p[1]])
            else:
                continue
            toks += lt; poss += list(range(np_, np_ + len(lt)))
        if toks:
            decode(toks, poss); computed += len(toks)
        q = tk(question(t), special=True)
        lg = decode(q, list(range(new_end, new_end + len(q))), want_logits=True); computed += len(q)
        txt, ng = generate(lg, new_end + len(q))
        return txt, computed, ng
    (txt, n, ng), cpu, wall = timed(go)
    return {'svar': extract(txt), 'beräknade_tokens': n, 'gen_tokens': ng, 'cpu_s': round(cpu, 2), 'wall_s': round(wall, 2)}


def selftest(t):
    """Kontroll av KV-redigeringen: REUSE med omberäkning av ALLA gamla rader ska ge samma första-logits som FULL."""
    global arm_reuse
    import types
    # identitet: om PATCH är tom ska REUSE == cache av gammal = ny. Testa istället full omberäkning:
    hlen, layout, end = base_cache(t)
    for s, n in layout:
        seq_rm(s, s + n)
    new_lines = t['new_excerpt'].splitlines(keepends=True)
    toks = [x for l in new_lines for x in tk(l)]
    decode(toks, list(range(hlen, hlen + len(toks))))
    q = tk(question(t), special=True)
    a = decode(q, list(range(hlen + len(toks), hlen + len(toks) + len(q))), want_logits=True)
    clear()
    h = tk(header(t), special=True); decode(h, list(range(len(h))))
    b = decode(toks + q, list(range(len(h), len(h) + len(toks) + len(q))), want_logits=True)
    d = float(np.max(np.abs(a - b)))
    # flytt-test: gammal cache, flytta allt +7 och tillbaka -7 => ska ge samma som ingen flytt (inom avrundning)
    hlen, layout, end = base_cache(t)
    x = decode(q, list(range(end, end + len(q))), want_logits=True)
    hlen, layout, end = base_cache(t)
    seq_add(hlen, end, 1000); seq_add(hlen + 1000, end + 1000, -1000)
    y = decode(q, list(range(end, end + len(q))), want_logits=True)
    return {'omberäkning_vs_full_maxdiff': d, 'flytt_rundtur_maxdiff': float(np.max(np.abs(x - y))),
            'argmax_lika': int(np.argmax(a)) == int(np.argmax(b))}


tasks = json.load(open(TASKS))
if SELFTEST:
    print(json.dumps([selftest(t) for t in tasks[:3]], indent=1))
    sys.exit(0)
res = []
for t in tasks:
    row = {'id': t['id'], 'kind': t['kind'], 'facit': t['answer'], 'gammal': t['old_line']}
    for name, fn in (('FULL', arm_full), ('IR', arm_ir), ('REUSE', lambda t: arm_reuse(t, False)), ('REUSE_NBR', lambda t: arm_reuse(t, True))):
        r = fn(t)
        r['korrekt'] = r['svar'].strip() == t['answer'].strip()
        r['inaktuell'] = t['kind'] == 'ändrad' and r['svar'].strip() == t['old_line'].strip()
        row[name] = r
    res.append(row)
    print(t['id'], t['kind'], ' '.join(f"{n}={'✓' if row[n]['korrekt'] else '✗'}{row[n]['beräknade_tokens']}" for n in ('FULL', 'IR', 'REUSE', 'REUSE_NBR')), flush=True)
    json.dump(res, open(OUT, 'w'), indent=1, ensure_ascii=False)
