#!/usr/bin/env python3
"""待發區自動上線（浮汕老人社論）。
用法：release_scheduled.py <site_dir> <staged_dir>
- staged_dir 內每個 <日期>/ 資料夾含 index.html（已上鎖成品）與 meta.json
  {"publish_at": "2026-12-09T10:00:00+08:00", "title": "...", "free": false}
- publish_at 已到：搬到 <site_dir>/editorial/<日期>/index.html，更新 articles.json、editorial/index.html 清單、sitemap.xml。
- 冪等：目標已存在就只清掉待發檔，不重複。
- 另支援 meta {"kind":"test"}：到時間只寫 editorial/_cron_test.txt，用來測試排程。
輸出（stdout 最後一行）：released=<N>
"""
import html, json, os, re, shutil, sys
from datetime import datetime, timezone
e = html.escape
site, staged = sys.argv[1], sys.argv[2]
SITE = "https://shezidao.com.tw/"
now = datetime.now(timezone.utc)
done = []
if not os.path.isdir(staged):
    print("released=0"); sys.exit(0)
for name in sorted(os.listdir(staged)):
    d = os.path.join(staged, name); mf = os.path.join(d, "meta.json")
    if not os.path.isfile(mf): continue
    meta = json.load(open(mf, encoding="utf-8"))
    if datetime.fromisoformat(meta["publish_at"]) > now: continue
    if meta.get("kind") == "test":
        open(os.path.join(site, "editorial", "_cron_test.txt"), "w").write(f"released {now.isoformat()} for {name}\n")
        shutil.rmtree(d); done.append(name); continue
    dest = os.path.join(site, "editorial", name); os.makedirs(dest, exist_ok=True)
    if not os.path.exists(os.path.join(dest, "index.html")):
        shutil.copy(os.path.join(d, "index.html"), os.path.join(dest, "index.html"))
    reg_f = os.path.join(site, "editorial", "articles.json")
    reg = json.load(open(reg_f, encoding="utf-8")) if os.path.exists(reg_f) else {}
    reg[name] = {"title": meta["title"], "free": bool(meta.get("free", False))}
    json.dump(reg, open(reg_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    def roc(s):
        y, m, dd = s.split("-"); return f"{int(y)-1911} 年 {int(m)} 月 {int(dd)} 日"
    cards = "".join(f'<a class="card {"c1" if v["free"] else "c2"}" href="{k}/"><h2>{e(v["title"])}</h2><p>{roc(k)}｜{"免費閱讀" if v["free"] else "🔒 VIP"}</p><span class="go">閱讀全文 →</span></a>'
                    for k, v in sorted(reg.items(), reverse=True))
    ix_f = os.path.join(site, "editorial", "index.html"); ix = open(ix_f, encoding="utf-8").read()
    ix = re.sub(r'(<!--LIST-->).*?(<!--/LIST-->)', lambda m: m.group(1) + cards + m.group(2), ix, flags=re.S)
    open(ix_f, "w", encoding="utf-8").write(ix)
    sm_f = os.path.join(site, "sitemap.xml"); sm = open(sm_f).read(); u = f"{SITE}editorial/{name}/"
    if u not in sm: open(sm_f, "w").write(sm.replace("</urlset>", f"<url><loc>{u}</loc></url></urlset>"))
    shutil.rmtree(d); done.append(name)
print("released=" + str(len(done)), " ".join(done))
