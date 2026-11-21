"""INV-2026-11-21-X1 – testrigg. Kör: python3 -I run_x1.py <korpusmapp> <utfil.json>"""
import sys, os, json, time, subprocess, tempfile, lzma
import zstandard as zstd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg

CORP, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else None
Z19 = zstd.ZstdCompressor(level=19)


def z19(b):
    return len(Z19.compress(b))


def load(name):
    objs = []
    for line in open(os.path.join(CORP, name + '.jsonl')):
        o = json.loads(line)
        objs.append((o['key'], bytes.fromhex(o['hex'])))
    return objs


def xdelta(data, base):
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, 't'); open(t, 'wb').write(data)
        cmd = ['xdelta3', '-9', '-e', '-f', '-c']
        if base is not None:
            s = os.path.join(d, 's'); open(s, 'wb').write(base); cmd += ['-s', s]
        return len(subprocess.run(cmd + [t], capture_output=True, check=True).stdout)


def tpl_columns(data, tindex, templates):
    """CLP-liknande kolumnkodning: mall-id, variabler och nya mallar i separata strömmar."""
    ids, vars_, newt, raws = bytearray(), bytearray(), bytearray(), bytearray()
    for line in data.splitlines(keepends=True):
        s = crg.split_template(line)
        if s is None:
            crg.uv(0, ids); crg.uv(len(line), raws); raws += line; continue
        t, slots = s
        tid = tindex.get(t)
        if tid is None:
            tid = len(templates); tindex[t] = tid; templates.append(t)
            crg.uv(len(t), newt); newt += t
        crg.uv(tid + 1, ids)
        for v in slots:
            crg.uv(len(v), vars_); vars_ += v
    return ids, vars_, newt, raws


def render(enc, st):
    """Textrendering av en CRG-kodning för tokenräkning (förhandsindikator för X2)."""
    r = crg.Reader(enc); r.take(4); r.u(); r.take(32)
    refs = [None] + [r.take(32) for _ in range(r.u())]
    parts = []
    ntpl = len(st.templates); new = []
    while not r.done():
        op = r.take(1)[0]
        if op == crg.RAW:
            parts.append(r.take(r.u()))
        elif op == crg.COPY:
            ri, off, L = r.u(), r.u(), r.u()
            tag = 'self' if ri == 0 else refs[ri].hex()[:8]
            parts.append(f'⟦COPY {tag}@{off}+{L}⟧'.encode())
        elif op == crg.PATCH:
            ri = r.u(); parts.append(f'⟦PATCH {refs[ri].hex()[:8]}⟧'.encode())
            for _ in range(r.u()):
                k, d = r.u(), r.u(); ins = r.take(r.u())
                parts.append(f'⟦KEEP {k} DEL {d}⟧'.encode()); parts.append(ins)
            parts.append(f'⟦KEEP {r.u()}⟧'.encode())
        elif op == crg.DEFTPL:
            new.append(r.take(r.u()))
        elif op == crg.TPL:
            tid = r.u(); t = st.templates[tid] if tid < ntpl else new[tid - ntpl]
            ps = t.split(crg.SLOT)
            for j, p in enumerate(ps):
                parts.append(p)
                if j < len(ps) - 1:
                    parts.append(r.take(r.u()))
    return b''.join(parts)


def run_corpus(name, tok):
    objs = load(name)
    raw_total = sum(len(d) for _, d in objs)
    res = {'objekt': len(objs), 'raw_byte': raw_total}
    # ---------- R2 baslinjer ----------
    t0 = time.time()
    hist = bytearray(); last = {}
    b_z = b_zp = b_x = 0
    tindex, templates = {}, []
    b_tpl = 0
    for key, d in objs:
        b_z += z19(d)
        if hist:
            dic = zstd.ZstdCompressionDict(bytes(hist[-(32 << 20):]), dict_type=zstd.DICT_TYPE_RAWCONTENT)
            b_zp += len(zstd.ZstdCompressor(level=19, dict_data=dic).compress(d))
        else:
            b_zp += z19(d)
        b_x += xdelta(d, last.get(key))
        cols = tpl_columns(d, tindex, templates)
        b_tpl += sum(z19(bytes(c)) for c in cols if c)
        hist += d; last[key] = d
    res['R2'] = {'zstd19': b_z, 'zstd19+historik': b_zp, 'xdelta3': b_x, 'TPL-kolumn (CLP-lik)': b_tpl}
    res['tid_baslinjer_s'] = round(time.time() - t0, 1)
    # ---------- R2 CRG ----------
    variants = {
        'CRG{COPY}': lambda d, k, st: crg.enc_copy(d, st),
        'CRG{PATCH}': lambda d, k, st: crg.enc_patch(d, st, k),
        'CRG{TEMPLATE}': lambda d, k, st: crg.enc_tpl(d, st),
    }
    choice_counts = {}
    crg_encs = {}
    tok_raw = tok_rend = 0
    for vname in list(variants) + ['CRG{ALL}']:
        st_e, st_d = crg.State(), crg.State()
        tot = 0; encs = []; te = td = 0.0
        for key, d in objs:
            t1 = time.time()
            if vname == 'CRG{ALL}':
                best = None
                for cname, f in variants.items():
                    e, nt = f(d, key, st_e)
                    s = z19(e)
                    if best is None or s < best[0]:
                        best = (s, e, nt, cname)
                s, e, nt, cname = best
                choice_counts[cname] = choice_counts.get(cname, 0) + 1
            else:
                e, nt = variants[vname](d, key, st_e)
                s = z19(e)
            te += time.time() - t1
            tot += s; encs.append(e)
            t2 = time.time()
            dec, dnt = crg.decode(e, st_d)
            td += time.time() - t2
            if dec != d:
                raise SystemExit(f'FÖRLUSTFRIHET BRUTEN: {name} {vname}')
            if vname == 'CRG{ALL}' and tok is not None:
                tok_raw += len(tok.encode(d.decode('utf-8', 'replace')).ids)
                tok_rend += len(tok.encode(render(e, st_d).decode('utf-8', 'replace')).ids)
            st_d.add(key, dec, dnt)
            st_e.add(key, d, nt)
        res['R2'][vname] = tot
        res.setdefault('tid_s', {})[vname] = {'kodning': round(te, 1), 'avkodning': round(td, 1)}
        res.setdefault('förlustfri', {})[vname] = f'{len(objs)}/{len(objs)}'
        crg_encs[vname] = encs
        print(name, vname, tot, flush=True)
    res['CRG{ALL}_val'] = choice_counts
    if tok is not None:
        res['tokens_qwen2'] = {'RAW': tok_raw, 'CRG{ALL}-rendering': tok_rend}
    # ---------- R1 arkiv ----------
    cat = b''.join(d for _, d in objs)
    zl = zstd.ZstdCompressor(level=19, compression_params=None)
    p = zstd.ZstdCompressionParameters.from_level(19, window_log=27, enable_ldm=True)
    zlong = zstd.ZstdCompressor(compression_params=p)
    r1 = {'zstd19 --long=27': len(zlong.compress(cat)), 'xz -9e': len(lzma.compress(cat, preset=9 | lzma.PRESET_EXTREME))}
    tindex, templates = {}, []
    cols = [bytearray() for _ in range(4)]
    for _, d in objs:
        for c, part in zip(cols, tpl_columns(d, tindex, templates)):
            c += part
    r1['TPL-kolumn (CLP-lik)'] = sum(len(zlong.compress(bytes(c))) for c in cols if c)
    for vname, encs in crg_encs.items():
        r1[vname] = len(zlong.compress(b''.join(encs)))
    res['R1'] = r1
    return res


def tokenizer():
    try:
        import gguf
        from tokenizers import Tokenizer, models, pre_tokenizers, decoders, Regex
        r = gguf.GGUFReader(os.environ['QWEN2_GGUF'])
        f = r.fields
        arr = lambda k: [bytes(f[k].parts[i]).decode('utf-8') for i in f[k].data]
        toks, merges = arr('tokenizer.ggml.tokens'), arr('tokenizer.ggml.merges')
        vocab = {t: i for i, t in enumerate(toks)}
        bpe = models.BPE(vocab=vocab, merges=[tuple(m.split(' ', 1)) for m in merges], byte_fallback=False)
        tk = Tokenizer(bpe)
        pat = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
        tk.pre_tokenizer = pre_tokenizers.Sequence([
            pre_tokenizers.Split(Regex(pat), behavior='isolated'),
            pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False)])
        tk.decoder = decoders.ByteLevel()
        s = 'def foo(x):\n    return x + 1  # åäö'
        assert tk.decode(tk.encode(s).ids) == s
        return tk
    except Exception as e:
        print('tokenizer saknas:', e)
        return None


if __name__ == '__main__':
    tok = tokenizer()
    results = {}
    for name in ['K1_logs', 'K2_code', 'K3_agent']:
        if ONLY and name not in ONLY:
            continue
        t = time.time()
        results[name] = run_corpus(name, tok)
        results[name]['total_tid_s'] = round(time.time() - t, 1)
        json.dump(results, open(OUT, 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(results, indent=1, ensure_ascii=False))
