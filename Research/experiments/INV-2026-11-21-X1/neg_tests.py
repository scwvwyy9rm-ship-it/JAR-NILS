"""Negativa tester för CRG v0 (ADR-ENC-001 §3.2, §6.2). Varje fall ska ge CRGError."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crg

base = b''.join(b'line %d: value = %d\n' % (i, i * 7) for i in range(200))
newv = base.replace(b'value = 70\n', b'value = -70\n') + b'tail\n'

def fresh():
    st = crg.State(); st.add('f', base); return st

def patch_enc():
    e, _ = crg.enc_patch(newv, fresh(), 'f'); return e

def copy_enc():
    e, _ = crg.enc_copy(newv, fresh()); return e

def tamper_body(e, i=-3):
    b = bytearray(e); b[i] ^= 0x01; return bytes(b)

cases = {}
def case(name, fn):
    try:
        fn(); cases[name] = 'FEL: accepterades'
    except crg.CRGError as ex:
        cases[name] = f'avvisad ({ex})'

# positiva kontroller
assert crg.decode(patch_enc(), fresh())[0] == newv
assert crg.decode(copy_enc(), fresh())[0] == newv

def manipulated_H():
    st = fresh(); c = st.order[0]; st.objs[c] = st.objs[c][:-1] + b'X'
    crg.decode(patch_enc(), st)
case('manipulerat H-objekt (hash stämmer inte)', manipulated_H)
case('saknad referens / framtida objekt', lambda: crg.decode(patch_enc(), crg.State()))
def forward_ref():
    # objektet refererar sig självt via cid => finns inte i H förrän efter avkodning (cykel)
    e = bytearray(crg._header(newv, [crg.cid(newv)])); e.append(crg.COPY); crg.uv(1, e); crg.uv(0, e); crg.uv(len(newv), e)
    crg.decode(bytes(e), fresh())
case('självreferens via cid (cykel)', forward_ref)
case('trunkerad ström', lambda: crg.decode(patch_enc()[:-5], fresh()))
case('manipulerad nyttolast (utdatahash)', lambda: crg.decode(tamper_body(copy_enc()), fresh()))
def bad_magic():
    crg.decode(b'XXXX' + patch_enc()[4:], fresh())
case('fel magic', bad_magic)
def unknown_op():
    e = bytearray(crg._header(b'a', [])); e.append(9); crg.decode(bytes(e), fresh())
case('okänd operation', unknown_op)
def copy_oob():
    st = fresh(); e = bytearray(crg._header(newv, [st.order[0]])); e.append(crg.COPY); crg.uv(1, e); crg.uv(len(base) - 4, e); crg.uv(100, e)
    crg.decode(bytes(e), st)
case('COPY utanför källans gränser', copy_oob)
def self_copy_future():
    e = bytearray(crg._header(b'abcd', [])); e.append(crg.COPY); crg.uv(0, e); crg.uv(0, e); crg.uv(4, e)
    crg.decode(bytes(e), fresh())
case('självkopia av ännu ej avkodad data', self_copy_future)
def expansion():
    # liten ström som deklarerar enorm utdata
    e = bytearray(crg.MAGIC); crg.uv(10 ** 12, e); e += b'\0' * 32; crg.uv(0, e)
    crg.decode(bytes(e), fresh())
case('expansionsbudget: deklarerad längd', expansion)
def expansion2():
    # överlappande självkopia som försöker expandera långt över deklarerad längd
    target = b'a' * 10
    e = bytearray(crg._header(target, [])); e.append(crg.RAW); crg.uv(1, e); e += b'a'
    e.append(crg.COPY); crg.uv(0, e); crg.uv(0, e); crg.uv(10 ** 9, e)
    crg.decode(bytes(e), fresh())
case('expansionsbudget: överlappande självkopia', expansion2)
def patch_misaligned():
    st = fresh(); e = bytearray(crg._header(newv, [st.order[0]])); e.append(crg.PATCH); crg.uv(1, e); crg.uv(0, e); crg.uv(5, e)
    crg.decode(bytes(e), st)
case('PATCH täcker inte basen', patch_misaligned)
def unknown_tpl():
    e = bytearray(crg._header(b'x\n', [])); e.append(crg.TPL); crg.uv(99, e); crg.decode(bytes(e), fresh())
case('okänd mall', unknown_tpl)
# exakthet: whitespace, ogiltig UTF-8, negation, CRLF
for name, x in {'whitespace/tabbar/CRLF': b'a  \t b\r\n\r\n  \n', 'ogiltig UTF-8': b'\xff\xfe\x80abc\n\xc3',
                'negation': base.replace(b'= 7\n', b'= -7\n'), 'NUL-bytes': b'a\x00b\x00\n'}.items():
    for enc in (lambda d, st: crg.enc_copy(d, st), lambda d, st: crg.enc_patch(d, st, 'f'), lambda d, st: crg.enc_tpl(d, st)):
        st = fresh(); e, nt = enc(x, st); assert crg.decode(e, fresh())[0] == x, name
    cases[f'exakt rundtur: {name}'] = 'OK (COPY, PATCH, TEMPLATE)'

ok = all(not v.startswith('FEL') for v in cases.values())
print(json.dumps(cases, indent=1, ensure_ascii=False)); print('ALLA NEGATIVA TESTER GODKÄNDA' if ok else 'MISSLYCKADE')
json.dump(cases, open(sys.argv[1], 'w'), indent=1, ensure_ascii=False)
sys.exit(0 if ok else 1)
