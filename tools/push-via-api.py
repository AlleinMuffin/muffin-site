#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
git push 的备用通道：当环境代理屏蔽 github.com（CONNECT 502）时，
改用 api.github.com 的 Git Data API 提交。

凭证通过 `git credential fill` 向系统凭证管理器索取（不会打印、不会落盘）。
只会推送当前分支相对远端领先的那几个提交（合并成一个提交）。

用法：
    python tools/push-via-api.py
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = None  # 从 git remote 自动读取


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, timeout=120, **kw)


def get_remote():
    out = run(["git", "remote", "get-url", "origin"]).stdout.decode().strip()
    # https://github.com/owner/repo.git -> owner/repo
    out = out.replace(".git", "") if out.endswith(".git") else out
    return "/".join(out.split("/")[-2:])


def get_token():
    """
    取 PAT：优先读环境变量 GITHUB_TOKEN / GH_TOKEN，
    否则向 git 凭证管理器索取（只取 password，不打印）。
    """
    for k in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    p = subprocess.run(
        ["git", "credential", "fill"],
        input=b"protocol=https\nhost=github.com\n\n",
        capture_output=True, timeout=60,
    )
    for line in p.stdout.decode(errors="ignore").splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    return None


def api(method, path, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "muffinlab-push",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.stderr.write("HTTP %s %s\n%s\n" % (e.code, path, e.read().decode()[:300]))
        raise


def main():
    root = run(["git", "rev-parse", "--show-toplevel"]).stdout.decode().strip()
    os.chdir(root)
    repo = get_remote()
    branch = run(["git", "branch", "--show-current"]).stdout.decode().strip()

    token = get_token()
    if not token:
        sys.stderr.write("拿不到凭证：请先在终端里成功 push 一次（或配置 credential.helper）\n")
        return 1

    # 找出相对远端变化的文件
    diff = run(["git", "diff", "--name-status", f"origin/{branch}..{branch}"])
    changes = []
    for line in diff.stdout.decode(errors="ignore").splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        changes.append((status.strip(), path.strip()))
    if not changes:
        print("没有需要推送的改动")
        return 0

    print(f"仓库 {repo}  分支 {branch}  改动 {len(changes)} 个文件")
    ref = api("GET", f"/repos/{repo}/git/ref/heads/{branch}", token)
    parent = ref["object"]["sha"]
    base_commit = api("GET", f"/repos/{repo}/git/commits/{parent}", token)
    base_tree = base_commit["tree"]["sha"]

    tree = []
    for status, path in changes:
        if status == "D":
            tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            print("  删除", path)
            continue
        full = os.path.join(root, path)
        with open(full, "rb") as f:
            raw = f.read()
        blob = api("POST", f"/repos/{repo}/git/blobs", token,
                   {"content": raw.decode("utf-8"), "encoding": "utf-8"})
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("  %-6s %-38s %6.1f KB" % (status, path, len(raw) / 1024))

    new_tree = api("POST", f"/repos/{repo}/git/trees", token,
                   {"base_tree": base_tree, "tree": tree})

    msg = run(["git", "log", "-1", "--pretty=%B", branch]).stdout.decode().strip()
    commit = api("POST", f"/repos/{repo}/git/commits", token,
                 {"message": msg, "tree": new_tree["sha"], "parents": [parent]})
    api("PATCH", f"/repos/{repo}/git/refs/heads/{branch}", token, {"sha": commit["sha"]})

    print("\n已推送：%s" % commit["sha"][:8])
    print("https://github.com/%s/commit/%s" % (repo, commit["sha"][:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
