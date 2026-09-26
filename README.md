# MUFFIN — Server & Projects Portal

深色、克制的个人服务器门户。以服务器世界截图为视觉核心，用开发者 UI 语言包装。

## 本地预览

直接双击 `index.html` 即可；推荐起一个本地服务以获得完整体验：

```bash
python -m http.server 8000
# 打开 http://localhost:8000
```

## 把占位图换成你自己的截图（最重要）

当前 `assets/img/` 里的图是脚本生成的像素风占位图（`tools/gen-art.py`），替换方式：

| 位置 | 文件 | 建议尺寸 |
| --- | --- | --- |
| Hero 背景 | `assets/img/hero.svg` → 换成 `hero.jpg/png` | ≥1920×1080，暗色/夜景最佳 |
| Gallery 六宫格 | `assets/img/gallery-0X.svg` → `gallery-0X.jpg/png` | 横图 16:10 左右 |

替换后同步改两处引用：

1. `assets/css/style.css` 中 `.hero__media` 的 `background: url("../img/hero.svg")`
2. `index.html` Gallery 区每个 `<img src>` 与 `data-full`

## 改成你的真实信息

- `assets/js/main.js` 顶部的 `SERVER` 对象（当前已填入真实值）：

  | 字段 | 当前值 |
  | --- | --- |
  | `name` | Mechanomania Aeronautics |
  | `ip` | `play.simpfun.cn:32883`（带自定义端口，和 IP 一起显示、一起复制） |
  | `version` | 1.21.1 |
  | `players` / `max` | 静态兜底值（0 / 20） |
  | `motd` | Mechanomania Aeronautics |
  | `liveStatus` | `true` |

  `liveStatus: true` 时页面会请求 `api.mcsrvstat.us` 读取真实在线状态；该接口的 `"online"`、
  `"version"`、`"players"`、`"motd.clean[0]"` 四个字段都会被用到，取不到时静默回落到上面的静态值，
  所以即使接口被墙也不会白屏。带端口的地址接口是支持的（`IP:端口` 直接拼在 URL 里即可）。
- Projects 区的下载链接目前是 `href="#"` 占位，指向你的 Release 页即可。
- GitHub 链接已接入真实账号 `AlleinMuffin`：
  - 导航栏 / Hero / GitHub 区 → <https://github.com/AlleinMuffin>
  - 主项目卡 Muffin Launcher → `Muffin-s-ModPack-Mod-Updated` 仓库
  - Server Tools / Datapack Experiments 两张卡**暂无对应仓库**，暂时指向主页，
    `index.html` 里已留 `TODO` 注释，仓库建好后替换 `href` 即可。

## 技术说明

- 纯静态三件套（HTML/CSS/JS），无构建步骤、无依赖。
- 字体策略：Inter / JetBrains Mono 以 woff2 自托管在 `assets/fonts/`（8 个文件共 ~182KB），
  首屏用到的三个字重加了 `<link rel="preload">`；中文走系统字体栈（PingFang SC / 微软雅黑 /
  Noto Sans SC），零下载。**不依赖任何外部 CDN**，国内网络下也能立即渲染。
  若确实需要统一的中文呈现（例如 Linux 访客较多），可按同样方式自托管 Noto Sans SC 的子集文件。
- 动效全部克制：Hero 淡入上移、Scroll Reveal 600ms、卡片 hover 上浮 4px、在线点呼吸；
  `prefers-reduced-motion` 下全部关闭。
- 服务器状态：`assets/js/main.js` 的 `STATUS_SOURCES` 会依次尝试多个数据源
  （`api.mcsrvstat.us` → `api.mcstatus.io`），任一返回确定结果即采用，避免单源被墙或抽风。
  显示四态：`ONLINE` / `OFFLINE` / `CHECKING` / `NO SIGNAL`。查不到时**不会**伪装成在线；
  服务器离线时人数显示 `–` 而不是上一次的旧数字。默认 60 秒自动刷新，标签页不可见时跳过。
- 无障碍：Lightbox 支持 Esc / ←→ / 焦点圈定，复制按钮有 aria-label，对比度达 WCAG AA。

## 上线与版本管理

- 当前线上地址：<https://muffin-server.app.workbuddy.host/>
- 管理入口：**设置 — 数据管理 — 应用**
- 本目录已初始化 Git 仓库并做了首次提交（`core.autocrlf=false`，源文件统一 LF）。
- **重要**：修改文件属于本地改动，不会自动同步到线上。要更新线上内容，需要显式再发布一次，
  链接保持不变但线上现有内容会被覆盖。
- 远端仓库：<https://github.com/AlleinMuffin/muffin-site>（分支 `main`，已与本地同步）
- 日常改动流程：

```bash
git add -A
git commit -m "描述这次改了什么"
git push                 # 推 GitHub，做异地备份
# 想让改动出现在 muffin-server.app.workbuddy.host 上，还需要再发布一次
```

- 站点是纯静态的，所以换托管平台零成本——这份源码推到任何支持静态托管的平台都能重建。

### ⚠ 改 CSS / JS 后必须递增版本号

托管平台的 CDN 会**按文件路径**缓存静态资源。源文件明明已经更新，但 `assets/css/style.css`
和 `assets/js/main.js` 这些路径仍会被下发旧内容，而且返回 `200`（只有 HTML 能正常刷新）。
**症状**：线上表现明显是旧版本，比如代码里改过的值在页面上一分未变。

因此这两个文件在 `index.html` 里的引用带了版本号，**每次改动都要 +1**：

```html
<link rel="stylesheet" href="assets/css/style.css?v=5" />
<script src="assets/js/main.js?v=5" defer></script>
```

发布后用内容校验，别只看状态码：

```bash
diff <(curl -s https://muffin-server.app.workbuddy.host/assets/js/main.js?v=5) assets/js/main.js
```

## 迁移到你自己的域名

这份源码是完全自包含的静态站点（无构建步骤、无 npm/pip 依赖、字体与图片全部本地化），
所以换托管平台等于复制文件。**已实测**：从 GitHub 全新 clone 到本地，直接起静态服务即可正常运行。

```bash
git clone https://github.com/AlleinMuffin/muffin-site.git
cd muffin-site
python -m http.server 8000     # 打开 http://127.0.0.1:8000 即可
```

整个目录上传到任何支持静态托管的地方（Cloudflare Pages / GitHub Pages / Vercel / Netlify /
自己的 Nginx / 对象存储）都能直接用，不需要改任何代码。

**唯一需要改的地方**：绑定自己的域名后，把 `index.html` 里的站点地址换成你的域名——
搜索 `muffin-server.app.workbuddy.host`，目前有 3 处：

```html
<link rel="canonical" href="https://你的域名/" />
<meta property="og:url" content="https://你的域名/" />
<meta property="og:image" content="https://你的域名/assets/img/hero.svg" />
```

作用分别是：告诉搜索引擎哪个是权威页面、社交分享卡片的链接、分享卡片的缩略图。
**`og:image` 必须是绝对地址**，写成相对路径的话微信 / Facebook / Twitter 抓不到图。

可选的进一步建议：

- `og:image` 现在是 SVG，**部分平台（含微信）不支持 SVG 缩略图**。
  换成真实截图时导出成 1200×630 的 JPG/PNG，分享卡片才能正常显示。
- 顺手加 `robots.txt` 和 `sitemap.xml`，方便搜索引擎收录。
- 运行时唯一的网络请求是服务器状态查询（三个公开 API），
  如果你自己的服务器在国内且不想依赖它们，把 `assets/js/main.js` 里的
  `liveStatus` 设为 `false` 即可完全静态化。

## 重新生成占位图（可选）

```bash
python tools/gen-art.py        # 生成 assets/img/*.svg
python tools/preview.py all    # 输出 tools/preview/*.png 便于预览
```
