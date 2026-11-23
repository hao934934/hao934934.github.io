#!/usr/bin/env python3
"""把 debs/ 里安装包 control 的真实内容同步进 overrides.json。

以前源上的「详情」是手写的，经常出现描述停在旧版本、包里却是新版的情况。
现在改成直接读最新 deb 的 Version / Description / Installed-Size：
  - desc          → control 的 Description 原文（写回 Packages 的 Description 字段）
  - detail        → 详情页用的 markdown（标题 + 正文 + 版本/架构/体积）
  - changes       → 插件源码 CHANGELOG.md 的最近若干段
所以「详情」永远等于安装包里真正写的内容，不会和包对不上。

用法：
  python3 scripts/sync-meta.py [--changelog /path/to/CHANGELOG.md] [--keep 8]
"""
import argparse
import glob
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBS = os.path.join(ROOT, 'debs')
OVERRIDES = os.path.join(ROOT, 'overrides.json')


def deb_fields(path):
    out = subprocess.run(['dpkg-deb', '-f', path],
                         capture_output=True, text=True, check=True).stdout
    fields, key = {}, None
    for line in out.splitlines():
        if line[:1] in (' ', '\t') and key:
            fields[key] += '\n' + line
        elif ':' in line:
            k, v = line.split(':', 1)
            key = k.strip()
            fields[key] = v.strip()
    return fields


def ver_key(v):
    m = re.search(r'-(\d+(?:\.\d+)*)$', v or '')
    return tuple(int(x) for x in m.group(1).split('.')) if m else (0,)


def pick_latest(pkg):
    best = None
    for path in glob.glob(os.path.join(DEBS, '*.deb')):
        try:
            f = deb_fields(path)
        except Exception:
            continue
        if f.get('Package') != pkg:
            continue
        if best is None or ver_key(f.get('Version')) > ver_key(best[1].get('Version')):
            best = (path, f)
    return best


def changelog_md(path, keep):
    """取 CHANGELOG.md 最近的 keep 个版本段，转成 depiction 的二级标题。"""
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    sections, cur = [], None
    for line in lines:
        if line.startswith('## '):
            if cur:
                sections.append(cur)
            cur = ['### ' + line[3:].strip()]
        elif cur is not None:
            if line.startswith('当前版本：'):
                continue
            cur.append(line)
    if cur:
        sections.append(cur)
    out = []
    for sec in sections[:keep]:
        text = '\n'.join(sec).strip()
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        out.append(text)
    return '\n\n'.join(out)


def human_size(kb):
    if not kb:
        return None
    kb = int(kb)
    return f'{kb / 1024:.1f} MB' if kb >= 1024 else f'{kb} KB'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--changelog', default=os.path.join(ROOT, 'CHANGELOG.md'))
    ap.add_argument('--keep', type=int, default=8)
    args = ap.parse_args()

    ov = json.load(open(OVERRIDES, encoding='utf-8'))
    changed = 0

    for key, entry in ov.items():
        if not entry.get('descFromDeb'):
            continue
        pkg = key.split(':', 1)[1] if key.startswith('pkg:') else entry.get('package')
        if not pkg:
            continue
        latest = pick_latest(pkg)
        if not latest:
            print(f'(跳过 {pkg}：debs/ 里没有对应安装包)')
            continue
        path, f = latest
        version = f.get('Version', '')
        desc = f.get('Description', '').strip()
        lines = [x.strip() for x in desc.splitlines() if x.strip()]
        title = lines[0] if lines else pkg
        body = ' '.join(lines[1:])

        detail = [f'### {title}']
        if body:
            detail.append(body)
        meta = [f'- 版本：{version}',
                f'- 包名：{pkg}',
                f'- 架构：{f.get("Architecture", "iphoneos-arm64")}（rootless）']
        size = human_size(f.get('Installed-Size'))
        if size:
            meta.append(f'- 安装体积：{size}')
        detail.append('\n'.join(meta))
        detail.append('> 本页内容直接取自安装包 control。')

        entry['desc'] = desc
        entry['descVersion'] = version
        entry['changesVersion'] = version
        entry['detail'] = '\n\n'.join(detail)
        if os.path.exists(args.changelog):
            md = changelog_md(args.changelog, args.keep)
            if md:
                entry['changes'] = md
        print(f'{pkg} ← {os.path.basename(path)}  {version}  '
              f'desc {len(desc)} 字 / 详情 {len(entry["detail"])} 字 / '
              f'日志 {len(entry.get("changes", ""))} 字')
        changed += 1

    with open(OVERRIDES, 'w', encoding='utf-8') as fh:
        json.dump(ov, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    print(f'同步完成：{changed} 个包')


if __name__ == '__main__':
    main()
