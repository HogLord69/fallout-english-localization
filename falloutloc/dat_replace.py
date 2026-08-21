"""Surgically replace entries in a Fallout 2 DAT2 archive.
Every untouched entry keeps its ORIGINAL stored bytes (no recompression),
so the rebuild is bit-identical apart from the replaced files and offsets."""
import struct, zlib, io, os, hashlib

def read_entries(path):
    raw=open(path,'rb').read()
    tree_size, data_size = struct.unpack('<II', raw[-8:])
    tree=raw[len(raw)-8-tree_size:len(raw)-8]
    n=struct.unpack('<I',tree[:4])[0]; p=4; out=[]
    for _ in range(n):
        ln=struct.unpack('<I',tree[p:p+4])[0]; p+=4
        nb=tree[p:p+ln]; p+=ln
        typ=tree[p]; p+=1
        real,packed,off=struct.unpack('<III',tree[p:p+12]); p+=12
        out.append(dict(name_bytes=nb, name=nb.decode('cp1251','replace'),
                        typ=typ, real=real, packed=packed, off=off))
    return raw, out

def content(raw, e):
    b=raw[e['off']:e['off']+(e['packed'] if e['typ']==1 else e['real'])]
    return zlib.decompress(b) if e['typ']==1 else b

def replace(path, outpath, repl):
    """repl: {basename_lower: new_bytes}"""
    raw, ents = read_entries(path)
    out=io.BytesIO(); tree=io.BytesIO(); tree.write(struct.pack('<I',len(ents)))
    changed=[]
    for e in ents:
        key=e['name'].split('\\')[-1].lower()
        if key in repl:
            data=repl[key]; real=len(data)
            p=zlib.compress(data,9)
            if len(p)<real: typ,payload=1,p
            else: typ,payload=0,data
            changed.append(e['name'])
        else:
            typ=e['typ']; real=e['real']
            payload=raw[e['off']:e['off']+(e['packed'] if typ==1 else real)]
        off=out.tell(); out.write(payload)
        tree.write(struct.pack('<I',len(e['name_bytes']))+e['name_bytes']+bytes([typ])
                   +struct.pack('<III',real,len(payload),off))
    tb=tree.getvalue(); out.write(tb); out.write(struct.pack('<II',len(tb),out.tell()+8))
    open(outpath,'wb').write(out.getvalue())
    return changed

def verify(orig, new, expect_changed):
    ro,eo=read_entries(orig); rn,en=read_entries(new)
    assert len(eo)==len(en), f"entry count {len(eo)} -> {len(en)}"
    names_o=[e['name'] for e in eo]; names_n=[e['name'] for e in en]
    assert names_o==names_n, "name list or order changed"
    diff=[]
    for a,b in zip(eo,en):
        ca=content(ro,a); cb=content(rn,b)
        if ca!=cb: diff.append(a['name'])
    return diff
