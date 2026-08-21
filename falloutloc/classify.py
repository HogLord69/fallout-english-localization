import re, unicodedata
def demoji(s):
    out=[]
    for c in s:
        try: out.append(c.encode('cp1251').decode('cp1252'))
        except Exception: out.append(c)
    return ''.join(out)
def norm(s):
    s=demoji(s)
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))   # drop accents, don't space them
    s=re.sub(r'[^0-9a-zA-Z]+',' ',s)
    return s.strip().lower()
