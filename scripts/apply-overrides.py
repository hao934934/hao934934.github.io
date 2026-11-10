import sys,json,os
txt=open('Packages',encoding='utf-8').read(); out=[]
try: ov=json.load(open('overrides.json',encoding='utf-8'))
except: ov={}
norm={k.split('/')[-1]:v for k,v in ov.items()}
m=0
for b in txt.split('\n\n'):
    if not b.strip(): out.append(b); continue
    lines=b.split('\n'); fn=None; pk=None
    for l in lines:
        if l.startswith('Filename:') and fn is None: fn=l.split(':',1)[1].strip()
        elif l.startswith('Package:') and pk is None: pk=l.split(':',1)[1].strip()
    key=fn.split('/')[-1] if fn else None
    # 优先按包名（pkg:com.xxx）匹配，这样换了版本、文件名变了也照样生效
    o=norm.get('pkg:'+pk) if pk else None
    if not o: o=norm.get(key)
    if o:
        nm=o.get('name') or ''; ds=o.get('desc') or o.get('description') or ''
        # deb 的 Description 是带续行的多行字段，写回去时后续行要缩进一个空格
        ds = '\n '.join([x.strip() for x in ds.splitlines() if x.strip()])
        nl=[]; replaced=False
        skip_cont=False
        for l in lines:
            # 原 Description 的续行（以空格开头）要被新内容整体替换掉
            if skip_cont and l.startswith(' '):
                continue
            skip_cont=False
            if l.startswith('Name:') and nm: nl.append('Name: '+nm); replaced=True
            elif l.startswith('Description:') and ds: nl.append('Description: '+ds); replaced=True; skip_cont=True
            else: nl.append(l)
        if not replaced and (nm or ds):
            ins=[]; added=False; addedd=False
            for l in nl:
                if l.startswith('Package:') and not added and nm: ins.append('Name: '+nm); added=True
                elif l.startswith('Depends:') and not added and nm: ins.append('Name: '+nm); added=True
                elif l.startswith('Description:'):
                    ins.append(l); continue
                ins.append(l)
            # 没有 Description 行就在末尾补一条
            if ds and not any(x.startswith('Description:') for x in ins):
                ins.append('Description: '+ds)
            nl=ins
        changes=o.get('changes') or ''
        version=o.get('changesVersion') or ''
        current=next((l.split(':',1)[1].strip() for l in lines if l.startswith('Version:')), '')
        if changes and (not version or version==current) and pk:
            raw_desc=next((l.split(':',1)[1].strip() for l in nl if l.startswith('Description:')), '')
            detail=ds.replace('\n ', '\n') if ds else raw_desc
            safe=''.join(c if c.isascii() and (c.isalnum() or c in '._-') else '_' for c in pk)
            safe_ver=''.join(c if c.isascii() and (c.isalnum() or c in '._-') else '_' for c in current)
            dest='depictions/'+safe+'_'+safe_ver+'.json'
            depiction={'class':'DepictionTabView','tabs':[
                {'tabname':'详情','class':'DepictionStackView','views':[
                    {'class':'DepictionMarkdownView','markdown':detail or '暂无详情','useSpacing':True}]},
                {'tabname':'更新日志','class':'DepictionStackView','views':[
                    {'class':'DepictionMarkdownView','markdown':changes,'useSpacing':True}]}]}
            os.makedirs('depictions',exist_ok=True)
            with open(dest,'w',encoding='utf-8') as f: json.dump(depiction,f,ensure_ascii=False)
            base=os.environ.get('REPO_URL','').rstrip('/')
            if base:
                nl=[l for l in nl if not l.startswith('SileoDepiction:')]
                nl.append('SileoDepiction: '+base+'/'+dest)
        m+=1; out.append('\n'.join(nl))
    else: out.append(b)
open('Packages','w',encoding='utf-8').write('\n\n'.join(out))
print('overridden packages:',m)