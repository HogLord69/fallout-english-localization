import struct, zlib, sys, os

def read_tree(path):
    f=open(path,'rb'); f.seek(0,2); size=f.tell()
    f.seek(size-8); tree_size, data_size = struct.unpack('<II', f.read(8))
    f.seek(size-8-tree_size)
    tree=f.read(tree_size)
    n=struct.unpack('<I',tree[:4])[0]
    p=4; out=[]
    for i in range(n):
        ln=struct.unpack('<I',tree[p:p+4])[0]; p+=4
        name=tree[p:p+ln].decode('cp1252',errors='replace'); p+=ln
        typ=tree[p]; p+=1
        real,packed,off=struct.unpack('<III',tree[p:p+12]); p+=12
        out.append((name,typ,real,packed,off))
    return f,out

def extract(path,dest,filt=None):
    f,entries=read_tree(path)
    cnt=0
    for name,typ,real,packed,off in entries:
        if filt and not filt(name): continue
        f.seek(off); raw=f.read(packed if typ==1 else real)
        if typ==1:
            try: raw=zlib.decompress(raw)
            except Exception as e: print("ERR",name,e); continue
        op=os.path.join(dest,name.replace('\\','/'))
        os.makedirs(os.path.dirname(op),exist_ok=True)
        open(op,'wb').write(raw); cnt+=1
    return cnt,len(entries)

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='list':
        f,e=read_tree(sys.argv[2])
        for name,typ,real,packed,off in e: print(f"{real:9d} {name}")

def build(srcdir, outpath, compress=True):
    import io
    files=[]
    for root,_,fs in os.walk(srcdir):
        for fn in fs:
            full=os.path.join(root,fn)
            rel=os.path.relpath(full,srcdir).replace('/','\\')
            files.append((rel,full))
    files.sort(key=lambda x:x[0].lower())
    out=open(outpath,'wb'); tree=io.BytesIO(); tree.write(struct.pack('<I',len(files)))
    for rel,full in files:
        data=open(full,'rb').read(); real=len(data)
        if compress:
            p=zlib.compress(data,9)
            if len(p)<real: typ,payload=1,p
            else: typ,payload=0,data
        else: typ,payload=0,data
        off=out.tell(); out.write(payload)
        nb=rel.encode('cp1251',errors='replace')
        tree.write(struct.pack('<I',len(nb))+nb+bytes([typ])+struct.pack('<III',real,len(payload),off))
    tb=tree.getvalue(); out.write(tb)
    out.write(struct.pack('<II',len(tb),out.tell()+8))
    out.close()
