#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把页面实时推送给支持 IndexNow 的搜索引擎（Bing / Yandex / Seznam 等）。

和 sitemap 的区别：sitemap 是被动等爬虫来取，IndexNow 是主动敲门，
通常几分钟到几小时内就能收录，适合刚发文章/改动页面后立刻用。

用法：
    python tools/ping-indexnow.py              # 推送 dist/sitemap-0.xml 里的全部 URL
    python tools/ping-indexnow.py URL1 URL2    # 只推送指定的 URL

前提：
    1. public/<key>.txt 已存在并已上线（IndexNow 规范要求密钥文件能被公开访问）
    2. 已 npm run build 过（脚本从 dist/sitemap-0.xml 取页面清单和域名）
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "dist", "sitemap-0.xml")
ENDPOINT = "https://api.indexnow.org/indexnow"


def find_key():
    """在 public/ 里找 IndexNow 密钥文件：文件名就是密钥，内容也等于密钥。"""
    pub = os.path.join(ROOT, "public")
    try:
        for name in sorted(os.listdir(pub)):
            path = os.path.join(pub, name)
            if not os.path.isfile(path):
                continue
            stem, ext = os.path.splitext(name)
            if ext != ".txt":
                continue
            # IndexNow 密钥：8-128 位，只允许字母数字和连字符
            if not re.fullmatch(r"[a-zA-Z0-9-]{8,128}", stem):
                continue
            with open(path, encoding="utf-8") as f:
                if f.read().strip() == stem:
                    return stem
    except FileNotFoundError:
        pass
    sys.exit("没找到 IndexNow 密钥文件（public/<key>.txt），请先生成并上线")


def read_urls():
    """从构建产物 sitemap 里取页面清单，避免手写漏掉。"""
    if not os.path.exists(SITEMAP):
        sys.exit("找不到 %s，请先执行 npm run build" % SITEMAP)
    with open(SITEMAP, encoding="utf-8") as f:
        return re.findall(r"<loc>(.*?)</loc>", f.read())


def main():
    urls = sys.argv[1:]
    if not urls:
        urls = read_urls()
    if not urls:
        sys.exit("没有要推送的 URL")

    host = urllib.parse.urlparse(urls[0]).netloc
    if any(urllib.parse.urlparse(u).netloc != host for u in urls):
        sys.exit("IndexNow 一次只能推同一个域名，请分开调用")

    key = find_key()
    key_location = "https://%s/%s.txt" % (host, key)

    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8",
                 "User-Agent": "muffinlab-indexnow"},
    )

    print("推送 %d 个 URL 到 IndexNow（%s）" % (len(urls), host))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print("成功：HTTP %s %s" % (r.status, r.reason))
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:300]
        sys.exit("失败：HTTP %s %s\n%s" % (e.code, e.reason, detail))


if __name__ == "__main__":
    main()
