#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
git push 的备用通道：当环境代理屏蔽 github.com（CONNECT 502 / Recv failure /
RPC failed curl 55）时，改用 api.github.com 的 Git Data API 提交。

相对原始版本的三处增强：
  1. 支持二进制文件（jar/png 等）——原先统一 utf-8 编码，遇到二进制必然报错或写坏内容
  2. 支持首次推送到空仓库——远端还没有分支时，自动以空树为基准、创建无父提交的初始提交
  3. 每个请求带重试——代理间歇性抽风时不会整轮白做

凭证通过 `git credential fill` 向系统凭证管理器索取（不会打印、不会落盘）。
注意：GitHub 单个 blob 上限 100MB，超过的文件只能用真正的 git push。

用法（在目标仓库根目录执行）：
    python push-via-api.py
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPO = None  # 从 git remote 自动读取
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git 的空树常量
MAX_RETRY = 3
# 已上传 blob 的记录（内容哈希 -> GitHub blob sha），放在 .git 下，不进版本控制。
# 作用：中途失败重跑时不用重新上传已经传过的文件，大仓库能省下大量时间。
CACHE_FILE = ".git/api-blob-cache.json"
# 上次推送的对应关系。本机 fetch 不了远端对象时，靠它判断「是不是已经推过了」，
# 否则每次跑都会因为拿不到远端基准而重新推一遍所有文件。
STATE_FILE = ".git/api-push-state.json"


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass  # 缓存/状态写失败不影响推送本身


def load_cache():
    return load_json(CACHE_FILE)


def save_cache(cache):
    """记录「内容哈希 -> 远端 blob sha」，让下一次运行能跳过已上传的文件。"""
    save_json(CACHE_FILE, cache)


def content_hash(path):
    """文件内容的 git blob 哈希，用来判断内容有没有变过。"""
    return run(["git", "hash-object", path]).stdout.decode().strip()


def blob_exists(repo, sha, token):
    """只确认 blob 存不存在。

    注意必须用 HEAD：GET 这个接口会把整个 blob 内容回传给我们（最大几十 MB），
    既慢又容易在弱网下被掐断，纯粹赔本。
    """
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/git/blobs/%s" % (repo, sha), method="HEAD",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "muffinlab-push"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60):
            return True
    except Exception:
        return False


def run(cmd, timeout=180, **kw):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, **kw)


def git(*args, timeout=180):
    """统一走 core.quotePath=false，否则含非 ASCII 的路径会被转义成八进制再加引号。"""
    return run(["git", "-c", "core.quotePath=false"] + list(args), timeout=timeout)


def unquote_path(path):
    """兜底：万一还是拿到了被引号包起来的八进制转义路径，把它还原。"""
    if not (path.startswith('"') and path.endswith('"')):
        return path
    inner = path[1:-1]
    out, i = [], 0
    while i < len(inner):
        if inner[i] == "\\" and i + 3 < len(inner) and inner[i + 1:i + 4].isdigit():
            out.append(chr(int(inner[i + 1:i + 4], 8)))
            i += 4
        elif inner[i] == "\\" and i + 1 < len(inner):
            out.append(inner[i + 1])
            i += 2
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


def get_remote():
    out = run(["git", "remote", "get-url", "origin"]).stdout.decode().strip()
    out = out[:-4] if out.endswith(".git") else out
    return "/".join(out.split("/")[-2:])


def get_token():
    """取 PAT：优先环境变量 GITHUB_TOKEN / GH_TOKEN，否则问 git 凭证管理器。"""
    for k in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    # 凭证管理器偶尔会卡住（等待 GUI 提示或锁），给足时间，避免白等一轮又崩在起点
    p = run(["git", "credential", "fill"], timeout=600,
            input=b"protocol=https\nhost=github.com\n\n")
    for line in p.stdout.decode(errors="ignore").splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    return None


def api(method, path, token, payload=None):
    """带重试的 GitHub API 请求。"""
    data = json.dumps(payload).encode() if payload is not None else None
    last = None
    for attempt in range(1, MAX_RETRY + 1):
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
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:300]
            # 4xx 是请求本身有问题，重试也没用
            if e.code < 500:
                sys.stderr.write("HTTP %s %s\n%s\n" % (e.code, path, body))
                raise
            last = "HTTP %s" % e.code
        except (urllib.error.URLError, TimeoutError) as e:
            last = "%s" % e
        if attempt < MAX_RETRY:
            sys.stderr.write("  请求失败（%s），%d 秒后重试...\n" % (last, attempt * 3))
            time.sleep(attempt * 3)
    sys.stderr.write("连续 %d 次失败：%s %s\n" % (MAX_RETRY, path, last))
    raise SystemExit(1)


def is_binary(raw):
    """按 git 的判断习惯：含 NUL 字节即视为二进制。"""
    return b"\x00" in raw


def bootstrap_empty_repo(repo, branch, token, root):
    """给完全空白的仓库创建第一个提交，返回新的 HEAD sha。

    坑：GitHub 的 Git Data API 对「一个提交都还没有」的仓库会一律返回
    409 "Git Repository is empty."，连创建 blob 都不行。必须先用 Contents API
    落地一个文件把分支建出来，后面的 Git Data API 才能正常使用。
    """
    readme = os.path.join(root, "README.md")
    if os.path.exists(readme):
        target = "README.md"
        with open(readme, "rb") as f:
            raw = f.read()
    else:
        target = ".gitkeep"
        raw = b"init\n"
    api("PUT", "/repos/%s/contents/%s" % (repo, target), token, {
        "message": "Initial commit",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": branch,
    })
    print("空仓库已用 %s 创建初始提交" % target, flush=True)
    return remote_head_sha(repo, branch, token)


def remote_head_sha(repo, branch, token):
    """取远端分支最新 commit；仓库还没有任何提交时返回 None。"""
    try:
        ref = api("GET", "/repos/%s/git/ref/heads/%s" % (repo, branch), token)
        return ref["object"]["sha"]
    except urllib.error.HTTPError as e:
        # 还没有任何提交的仓库：GET ref 会返回 409 "Git Repository is empty."，
        # 有时也可能是 404，两种情况都当成「空仓库」处理
        if e.code in (404, 409):
            return None
        raise


def local_changes(branch, remote_sha):
    """找出本地相对远端有变化的文件，返回 [(status, path), ...]。

    本地不一定拉得到远端对象（代理屏蔽时 fetch 不了），所以按可用性依次降级：
    远端真实 commit -> 本地缓存的 origin/<branch> -> 空树（等于把全部文件当新增）。
    """
    candidates = []
    if remote_sha:
        candidates.append(remote_sha)
    candidates.append("origin/%s" % branch)
    candidates.append(EMPTY_TREE)

    for base in candidates:
        if base == "origin/%s" % branch:
            # 真实的远端 commit 优先用这个入口，本地引用单独判断一次
            p = git("rev-parse", "--verify", "--quiet", base)
            base_ref = p.stdout.decode().strip() if p.returncode == 0 else None
        else:
            base_ref = base
        if not base_ref:
            continue
        p = git("diff", "--name-status", base_ref, branch)
        if p.returncode != 0:
            continue  # 这个基准在本机不可用（对象缺失），换下一个
        out = p.stdout.decode("utf-8", "replace")
        changes = [line.split("\t", 1) for line in out.splitlines() if "\t" in line]
        return [(status.strip(), unquote_path(path.strip())) for status, path in changes]
    return []


def main():
    root = run(["git", "rev-parse", "--show-toplevel"]).stdout.decode().strip()
    os.chdir(root)
    repo = get_remote()
    branch = run(["git", "branch", "--show-current"]).stdout.decode().strip() or "main"

    token = get_token()
    if not token:
        sys.stderr.write("拿不到凭证：请先在终端里成功 push 一次（或配置 credential.helper）\n")
        return 1

    remote_sha = remote_head_sha(repo, branch, token)
    if remote_sha is None:
        remote_sha = bootstrap_empty_repo(repo, branch, token, root)

    local_head = git("rev-parse", branch).stdout.decode().strip()
    state = load_json(STATE_FILE)
    if (state.get("repo") == repo and state.get("local_head") == local_head
            and state.get("remote_sha") == remote_sha):
        print("本地与远端一致，没有需要推送的改动")
        return 0

    changes = local_changes(branch, remote_sha)

    if not changes:
        print("没有需要推送的改动（本地与远端一致）")
        return 0

    print("仓库 %s  分支 %s  改动 %d 个文件%s"
          % (repo, branch, len(changes), "（空仓库，将创建初始提交）" if not remote_sha else ""),
          flush=True)

    # 基准树：有远端提交就用它的树，否则用空树
    if remote_sha:
        base_commit = api("GET", "/repos/%s/git/commits/%s" % (repo, remote_sha), token)
        base_tree = base_commit["tree"]["sha"]
    else:
        base_tree = None

    tree = []
    cache = load_cache()
    for index, (status, path) in enumerate(changes, 1):
        status = status.strip()
        path = path.strip()
        if status == "D":
            tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            print("  删除  %s" % path, flush=True)
            continue
        full = os.path.join(root, path)
        with open(full, "rb") as f:
            raw = f.read()

        sha = None
        cached = cache.get(content_hash(full))
        if cached and blob_exists(repo, cached, token):
            sha = cached
            print("  [%3d/%d] 复用已上传  %s" % (index, len(changes), path), flush=True)
        else:
            if is_binary(raw):
                payload = {"content": base64.b64encode(raw).decode("ascii"), "encoding": "base64"}
                kind = "二进制"
            else:
                payload = {"content": raw.decode("utf-8", "replace"), "encoding": "utf-8"}
                kind = "文本"
            blob = api("POST", "/repos/%s/git/blobs" % repo, token, payload)
            sha = blob["sha"]
            cache[content_hash(full)] = sha
            save_cache(cache)
            print("  [%3d/%d] %-6s %-46s %7.1f KB  %s"
                  % (index, len(changes), status, path, len(raw) / 1024, kind), flush=True)

        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": sha})

    body = {"tree": tree}
    if base_tree:
        body["base_tree"] = base_tree
    new_tree = api("POST", "/repos/%s/git/trees" % repo, token, body)

    msg = run(["git", "log", "-1", "--pretty=%B", branch]).stdout.decode().strip()
    payload = {"message": msg, "tree": new_tree["sha"]}
    payload["parents"] = [remote_sha] if remote_sha else []
    commit = api("POST", "/repos/%s/git/commits" % repo, token, payload)

    if remote_sha:
        api("PATCH", "/repos/%s/git/refs/heads/%s" % (repo, branch),
            token, {"sha": commit["sha"]})
    else:
        api("POST", "/repos/%s/git/refs" % repo,
            token, {"ref": "refs/heads/%s" % branch, "sha": commit["sha"]})

    save_json(STATE_FILE, {"repo": repo, "branch": branch,
                           "local_head": local_head, "remote_sha": commit["sha"]})
    print("\n已推送：%s" % commit["sha"][:8])
    print("https://github.com/%s/commit/%s" % (repo, commit["sha"][:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
