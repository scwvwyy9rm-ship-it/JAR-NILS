"""ENIGMA-CRG v0 – forskningsprototyp för INV-2026-11-21-X1.

Isolerad, deterministisk codec. Ingen produktionskoppling.
Kontrakt: decode(encode(x, H), H) == x byte för byte, annars CRGError.
"""
import hashlib, re, difflib

MAGIC = b'CRG0'
RAW, COPY, PATCH, TPL, DEFTPL = 0, 1, 2, 3, 4
SELF = 0  # ref-index 0 = redan avkodad del av aktuellt objekt
MIN_COPY = 32
K = 16  # nyckellängd; historik samplas var K:e byte => alla matchningar >= 2K-1 hittas
MAX_OUT = 64 << 20
MAX_OPS = 1 << 20
SLOT = b'\x00'
VAR_RE = re.compile(rb'0x[0-9a-fA-F]+|[0-9a-fA-F]{8,}|\d+(?:[.:]\d+)*')


class CRGError(Exception):
    pass


def cid(b):
    return hashlib.sha256(b).digest()


# ---------- varint ----------
def uv(n, out):
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


class Reader:
    def __init__(self, b):
        self.b, self.i = b, 0

    def u(self):
        n = s = 0
        while True:
            if self.i >= len(self.b):
                raise CRGError('trunkerad varint')
            c = self.b[self.i]
            self.i += 1
            n |= (c & 0x7F) << s
            if not c & 0x80:
                return n
            s += 7
            if s > 63:
                raise CRGError('för lång varint')

    def take(self, n):
        if self.i + n > len(self.b):
            raise CRGError('trunkerad data')
        r = self.b[self.i:self.i + n]
        self.i += n
        return r

    def done(self):
        return self.i >= len(self.b)


# ---------- tillstånd (kausalt, återskapbart ur historiken) ----------
class State:
    """Mottagarens/avsändarens historik H: objekt i ordning + mallar + COPY-index."""

    def __init__(self):
        self.objs = {}  # cid -> bytes
        self.order = []
        self.key_last = {}  # nyckel -> cid för senaste objekt med nyckeln
        self.templates = []  # tid -> mall
        self.tpl_index = {}
        self.index = {}  # K-byte nyckel -> (cid, offset)

    def add(self, key, data, new_templates=()):
        c = cid(data)
        self.objs[c] = data
        self.order.append(c)
        if key is not None:
            self.key_last[key] = c
        for t in new_templates:
            self.tpl_index[t] = len(self.templates)
            self.templates.append(t)
        idx = self.index
        for off in range(0, len(data) - K + 1, K):
            idx[data[off:off + K]] = (c, off)
        return c


# ---------- kodare ----------
def _header(data, refs):
    out = bytearray(MAGIC)
    uv(len(data), out)
    out += cid(data)
    uv(len(refs), out)
    for r in refs:
        out += r
    return out


def enc_raw(data, st):
    out = _header(data, [])
    out.append(RAW); uv(len(data), out); out += data
    return bytes(out), []


def enc_copy(data, st):
    refs, refpos = [], {}
    ops = bytearray()
    lit_start = 0
    i, n = 0, len(data)
    local = {}
    idx = st.index
    objs = st.objs
    nops = 0

    def flush(upto):
        nonlocal nops
        if upto > lit_start:
            ops.append(RAW); uv(upto - lit_start, ops); ops.extend(data[lit_start:upto]); nops += 1

    while i + K <= n:
        key = data[i:i + K]
        best_len, best = 0, None
        for cand in (idx.get(key), local.get(key)):
            if cand is None:
                continue
            c, off = cand
            src = objs[c] if c is not None else data
            limit = i if c is None else len(src)
            # förläng framåt
            L = 0
            while i + L < n and off + L < limit and src[off + L] == data[i + L]:
                L += 1
            # förläng bakåt in i ej utskrivna literaler
            B = 0
            while B < i - lit_start and off - B - 1 >= 0 and src[off - B - 1] == data[i - B - 1]:
                B += 1
            if L + B > best_len:
                best_len, best = L + B, (c, off - B, i - B)
        if best_len >= MIN_COPY:
            c, off, start = best
            flush(start)
            if c is None:
                ri = SELF
            else:
                if c not in refpos:
                    refpos[c] = len(refs) + 1
                    refs.append(c)
                ri = refpos[c]
            ops.append(COPY); uv(ri, ops); uv(off, ops); uv(best_len, ops); nops += 1
            end = start + best_len
            for p in range((i // K + 1) * K, min(end, n - K + 1), K):
                local[data[p:p + K]] = (None, p)
            i = end
            lit_start = i
            continue
        if i % K == 0:
            local[key] = (None, i)
        i += 1
    flush(n)
    out = _header(data, refs)
    out += ops
    return bytes(out), []


def enc_patch(data, st, key):
    base_c = st.key_last.get(key)
    if base_c is None:
        return enc_raw(data, st)
    base = st.objs[base_c]
    a = base.splitlines(keepends=True)
    b = data.splitlines(keepends=True)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    edits = []  # (keep, delete, insert_bytes)
    ai = 0
    pend_keep = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            pend_keep += i2 - i1
        else:
            edits.append((pend_keep, i2 - i1, b''.join(b[j1:j2])))
            pend_keep = 0
    tail_keep = pend_keep
    out = _header(data, [base_c])
    out.append(PATCH); uv(1, out); uv(len(edits), out)
    for k, d, ins in edits:
        uv(k, out); uv(d, out); uv(len(ins), out); out += ins
    uv(tail_keep, out)
    return bytes(out), []


def split_template(line):
    if SLOT in line:
        return None
    slots = VAR_RE.findall(line)
    return VAR_RE.sub(SLOT, line), slots


def enc_tpl(data, st):
    lines = data.splitlines(keepends=True)
    out = _header(data, [])
    new_tpls, local_index = [], {}
    body = bytearray()
    for line in lines:
        s = split_template(line)
        if s is None:
            body.append(RAW); uv(len(line), body); body += line
            continue
        t, slots = s
        tid = st.tpl_index.get(t)
        if tid is None:
            tid = local_index.get(t)
        if tid is None:
            tid = len(st.templates) + len(new_tpls)
            local_index[t] = tid
            new_tpls.append(t)
            body.append(DEFTPL); uv(len(t), body); body += t
        body.append(TPL); uv(tid, body)
        for v in slots:
            uv(len(v), body); body += v
    out += body
    return bytes(out), new_tpls


# ---------- avkodare ----------
def decode(enc, st, max_out=MAX_OUT):
    """Returnerar (data, nya_mallar). Kastar CRGError vid varje avvikelse."""
    r = Reader(enc)
    if r.take(4) != MAGIC:
        raise CRGError('fel magic')
    n = r.u()
    if n > max_out:
        raise CRGError('deklarerad längd över budget')
    want = r.take(32)
    nrefs = r.u()
    refs = [None]
    for _ in range(nrefs):
        c = r.take(32)
        src = st.objs.get(c)
        if src is None:
            raise CRGError('referens saknas i H (framtida/okänt objekt)')
        if cid(src) != c:
            raise CRGError('H-objektets hash stämmer inte')
        refs.append(src)
    out = bytearray()
    new_tpls = []
    ntpl = len(st.templates)
    nops = 0
    while not r.done():
        nops += 1
        if nops > MAX_OPS:
            raise CRGError('för många operationer')
        op = r.take(1)[0]
        if op == RAW:
            out += r.take(r.u())
        elif op == COPY:
            ri, off, L = r.u(), r.u(), r.u()
            if ri == SELF:
                if off >= len(out) or len(out) + L > n:
                    raise CRGError('COPY utanför egen utdata')
                for k in range(L):  # tillåter överlapp
                    out.append(out[off + k])
            else:
                if ri >= len(refs):
                    raise CRGError('ogiltigt ref-index')
                src = refs[ri]
                if off + L > len(src):
                    raise CRGError('COPY utanför källans gränser')
                out += src[off:off + L]
        elif op == PATCH:
            ri = r.u()
            if ri == SELF or ri >= len(refs):
                raise CRGError('ogiltig PATCH-bas')
            a = refs[ri].splitlines(keepends=True)
            p = 0
            for _ in range(r.u()):
                k, d = r.u(), r.u()
                ins = r.take(r.u())
                if p + k + d > len(a):
                    raise CRGError('PATCH utanför basens rader')
                out += b''.join(a[p:p + k]); p += k + d; out += ins
            k = r.u()
            if p + k != len(a):
                raise CRGError('PATCH täcker inte basen exakt')
            out += b''.join(a[p:p + k])
        elif op == DEFTPL:
            t = r.take(r.u())
            new_tpls.append(t)
        elif op == TPL:
            tid = r.u()
            if tid < ntpl:
                t = st.templates[tid]
            elif tid - ntpl < len(new_tpls):
                t = new_tpls[tid - ntpl]
            else:
                raise CRGError('okänd mall')
            parts = t.split(SLOT)
            for j, part in enumerate(parts):
                out += part
                if j < len(parts) - 1:
                    out += r.take(r.u())
        else:
            raise CRGError('okänd operation')
        if len(out) > max_out or len(out) > n:
            raise CRGError('expansionsbudget överskriden')
    if len(out) != n:
        raise CRGError('fel längd')
    if cid(bytes(out)) != want:
        raise CRGError('utdatans hash stämmer inte')
    return bytes(out), new_tpls
