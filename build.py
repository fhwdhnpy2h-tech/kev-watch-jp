#!/usr/bin/env python3
"""Build static KEV Watch JP site from CISA's official JSON feed."""
import csv
import html
import io
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

FEED = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'
OUT = Path('site')
JST = timezone(timedelta(hours=9))
FIELDS = ['cveID', 'vendorProject', 'product', 'vulnerabilityName', 'dateAdded', 'shortDescription', 'requiredAction', 'dueDate', 'knownRansomwareCampaignUse']

def get_feed():
    local = os.environ.get('KEV_FIXTURE')
    if local:
        return json.loads(Path(local).read_text(encoding='utf-8'))
    req = Request(FEED, headers={'User-Agent':'KEV-Watch-JP/0.1 (public vulnerability catalog viewer)'})
    with urlopen(req, timeout=45) as response:
        payload = response.read(15_000_000)
    return json.loads(payload)

def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get('vulnerabilities'), list):
        raise ValueError('Unexpected CISA feed schema')
    if not data['vulnerabilities']:
        raise ValueError('Empty CISA catalog; refusing to publish')
    rows = []
    for item in data['vulnerabilities']:
        if not isinstance(item,dict) or not item.get('cveID') or not item.get('dateAdded'):
            raise ValueError('Invalid CISA entry')
        rows.append({key:str(item.get(key,'') or '') for key in FIELDS})
    return sorted(rows, key=lambda x:(x['dateAdded'],x['cveID']), reverse=True)

def build():
    data = get_feed()
    rows = validate(data)
    OUT.mkdir(parents=True,exist_ok=True)
    updated = datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')
    # Keep full catalog downloadable/searchable, show recent 200 in initial UI.
    (OUT/'data.json').write_text(json.dumps({'lastBuilt':updated,'sourceUpdated':data.get('dateReleased',''),'items':rows}, ensure_ascii=False, separators=(',',':')),encoding='utf-8')
    with (OUT/'data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n',encoding='utf-8')
    (OUT/'.nojekyll').write_text('',encoding='utf-8')
    # Generate RSS from source KEV additions, dateAdded date only (not true publication timestamps).
    latest=rows[:50]
    rss=['<?xml version="1.0" encoding="UTF-8"?>','<rss version="2.0"><channel><title>KEV Watch JP — CISA追加項目</title><link>https://www.cisa.gov/known-exploited-vulnerabilities-catalog</link><description>CISA KEV新規追加項目一覧（追加日基準）</description>']
    for item in latest:
        title=html.escape(f"{item['cveID']} | {item['vendorProject']} {item['product']}",quote=True)
        url='https://nvd.nist.gov/vuln/detail/'+item['cveID']
        desc=html.escape(item['shortDescription'],quote=True)
        rss.append(f'<item><title>{title}</title><link>{url}</link><guid isPermaLink="false">{html.escape(item["cveID"])}</guid><description>{desc}</description></item>')
    rss.append('</channel></rss>')
    (OUT/'feed.xml').write_text('\n'.join(rss),encoding='utf-8')
    page='''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="CISA公式KEVカタログの悪用確認済み脆弱性を、製品名・CVE番号で検索する無料ツール。"><title>KEV Watch JP | 悪用確認済み脆弱性検索</title><style>
:root{font-family:system-ui,-apple-system,"Hiragino Kaku Gothic ProN",Meiryo,sans-serif;color:#172436;background:#f5f7fb}*{box-sizing:border-box}body{margin:0}.wrap{max-width:1120px;margin:auto;padding:24px}header{background:#0d223b;color:white;padding:30px 0}header h1{font-size:clamp(25px,4vw,38px);margin:0 0 8px}header p{color:#cddbf0;margin:0}.pill{display:inline-block;background:#173b61;border-radius:50px;padding:6px 12px;font-size:12px;margin-bottom:12px}.panel{background:white;border:1px solid #e1e8f1;border-radius:16px;padding:22px;margin:18px 0;box-shadow:0 5px 20px rgba(13,34,59,.04)}.muted{color:#63738a;font-size:13px}.controls{display:grid;grid-template-columns:2fr 1fr auto;gap:10px}input,select,button{font:inherit;border-radius:10px;padding:12px;border:1px solid #cbd5e1}button{background:#164b78;color:white;cursor:pointer;border:0}a{color:#175887}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:13px 10px;border-bottom:1px solid #e4e9f0;vertical-align:top}th{font-size:12px;color:#607086}td{font-size:13px}td:first-child{white-space:nowrap;font-weight:700}.tableScroll{overflow-x:auto}.tags{display:flex;gap:10px;flex-wrap:wrap}.tags a{display:inline-block;background:#ecf3fb;padding:9px 13px;border-radius:9px;text-decoration:none}.notice{border-left:3px solid #d08b37;padding:8px 14px;background:#fff9ec;font-size:13px}.stat{font-size:30px;font-weight:800}.footer{padding-bottom:40px;font-size:13px;color:#63738a}@media(max-width:700px){.controls{grid-template-columns:1fr}td:nth-child(3),th:nth-child(3){display:none}.wrap{padding:16px}}
</style></head><body><header><div class="wrap"><div class="pill">公開データ × 自動更新</div><h1>KEV Watch JP</h1><p>CISAの「実際に悪用が確認された脆弱性」を、製品名やCVE番号から探せる無料ツール</p></div></header><main class="wrap"><div class="panel"><div class="muted">掲載データ総件数</div><div class="stat" id="total">読み込み中…</div><div class="muted" id="updated">更新日時を取得中…</div><p class="notice">重要：これはCISA KEV掲載情報の検索ツールです。脆弱性の影響判定やパッチ適用判断を代行するものではありません。影響バージョンや対処方法は必ずベンダーの一次情報を確認してください。掲載されていない脆弱性も安全とは限りません。</p></div><section class="panel"><h2>脆弱性を検索</h2><div class="controls"><input aria-label="製品名やCVE番号" id="query" placeholder="例：Microsoft / Fortinet / CVE-2026"><select id="range" aria-label="追加日の範囲"><option value="30">過去30日</option><option value="90">過去90日</option><option value="365">過去1年</option><option value="all">すべて</option></select><button id="clear">クリア</button></div><p class="muted" id="count">検索中…</p><div class="tableScroll"><table><thead><tr><th>CVE番号</th><th>ベンダー / 製品</th><th>内容（原文）</th><th>追加日</th></tr></thead><tbody id="results"></tbody></table></div><p class="muted">最大100件表示。検索条件を絞り込んでください。</p></section><section class="panel"><h2>データを利用する</h2><div class="tags"><a href="data.csv">CSVを取得</a><a href="data.json">JSONを取得</a><a href="feed.xml">RSSを購読</a><a href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" target="_blank" rel="noopener noreferrer">CISA公式カタログ</a></div><p class="muted">米国CISA公開情報を自動取得。英語の原文を表示しています。翻訳による誤解を避けるため原文を保持しています。</p></section><section class="panel"><h2>企業向け監視サービス（準備中）</h2><p>使用中の製品を登録し、該当する新規KEV項目だけを受け取る有料機能を検証しています。</p><p class="muted">現在、このページでは決済・契約・個別通知を提供していません。</p></section></main><footer class="wrap footer">データ提供：CISA Known Exploited Vulnerabilities Catalog。CISAによる承認・推奨を意味しません。情報は利用者ご自身で検証してください。</footer><script>
const $=id=>document.getElementById(id);let items=[];function e(tag,text){const x=document.createElement(tag);x.textContent=text;return x}function display(){const q=$('query').value.trim().toLowerCase(),r=$('range').value;const cutoff=new Date();if(r!=='all')cutoff.setDate(cutoff.getDate()-Number(r));let filtered=items.filter(x=>{const hay=[x.cveID,x.vendorProject,x.product,x.vulnerabilityName,x.shortDescription].join(' ').toLowerCase();return (!q||hay.includes(q))&&(r==='all'||new Date(x.dateAdded+'T00:00:00Z')>=cutoff)});$('count').textContent=`${filtered.length.toLocaleString('ja-JP')}件が一致`;const tbody=$('results');tbody.replaceChildren();for(const x of filtered.slice(0,100)){const tr=e('tr','');const td=e('td','');const a=e('a',x.cveID);a.href='https://nvd.nist.gov/vuln/detail/'+encodeURIComponent(x.cveID);a.target='_blank';a.rel='noopener noreferrer';td.append(a);tr.append(td,e('td',[x.vendorProject,x.product].filter(Boolean).join(' / ')),e('td',x.vulnerabilityName),e('td',x.dateAdded));tbody.append(tr)}}fetch('data.json').then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(d=>{items=d.items;$('total').textContent=items.length.toLocaleString('ja-JP')+'件';$('updated').textContent='サイト生成：'+d.lastBuilt+' / CISA公開データ：'+(d.sourceUpdated||'未記載');display()}).catch(()=>{$('total').textContent='取得できませんでした';$('count').textContent='ページを再読込してください'});$('query').addEventListener('input',display);$('range').addEventListener('change',display);$('clear').addEventListener('click',()=>{$('query').value='';$('range').value='30';display()});
</script></body></html>'''
    (OUT/'index.html').write_text(page,encoding='utf-8')
    print(f'Generated {len(rows)} records at {updated}')

if __name__ == '__main__':
    build()
