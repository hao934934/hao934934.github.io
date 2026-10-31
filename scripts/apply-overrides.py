import sys,json
txt=open('Packages',encoding='utf-8').read(); out=[]
try: ov=json.load(open('overrides.json',encoding='utf-8'))
except: ov={}
norm={k.split('/')[-1]:v for k,v in ov.items()}
m=0
for b in txt.split('\n\n'):
    if not b.strip(): out.append(b); continue
    lines=b.split('\n'); fn=None
    for l in lines:
        if l.startswith('Filename:'): fn=l.split(':',1)[1].strip(); break
    key=fn.split('/')[-1] if fn else None; o=norm.get(key)
    if o:
        nm=o.get('name') or ''; ds=o.get('desc') or o.get('description') or ''
        nl=[]; replaced=False
        for l in lines:
            if l.startswith('Name:') and nm: nl.append('Name: '+nm); replaced=True
            elif l.startswith('Description:') and ds: nl.append('Description: '+ds); replaced=True
            else: nl.append(l)
        if not replaced and (nm or ds):
            ins=[]; added=False
            for l in nl:
                if l.startswith('Package:') and not added and nm: ins.append('Name: '+nm); added=True
                elif l.startswith('Depends:') and not added and nm: ins.append('Name: '+nm); added=True
                ins.append(l)
            nl=ins
        m+=1; out.append('\n'.join(nl))
    else: out.append(b)
open('Packages','w',encoding='utf-8').write('\n\n'.join(out))
print('overridden packages:',m)