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

- `assets/js/main.js` 顶部的 `SERVER` 对象：`ip`、`version`、`players/max`、`motd`、
  以及 `liveStatus`（为 `true` 时会请求 `api.mcsrvstat.us` 读取实时状态，失败自动回落静态值）。
- 全局搜索 `https://github.com/your-name`，换成你的 GitHub 主页与各仓库地址。
- Projects 区的下载链接目前是 `href="#"` 占位，指向你的 Release 页即可。

## 技术说明

- 纯静态三件套（HTML/CSS/JS），无构建步骤、无依赖。
- 字体策略：Inter / JetBrains Mono 以 woff2 自托管在 `assets/fonts/`（8 个文件共 ~182KB），
  首屏用到的三个字重加了 `<link rel="preload">`；中文走系统字体栈（PingFang SC / 微软雅黑 /
  Noto Sans SC），零下载。**不依赖任何外部 CDN**，国内网络下也能立即渲染。
  若确实需要统一的中文呈现（例如 Linux 访客较多），可按同样方式自托管 Noto Sans SC 的子集文件。
- 动效全部克制：Hero 淡入上移、Scroll Reveal 600ms、卡片 hover 上浮 4px、在线点呼吸；
  `prefers-reduced-motion` 下全部关闭。
- 无障碍：Lightbox 支持 Esc / ←→ / 焦点圈定，复制按钮有 aria-label，对比度达 WCAG AA。

## 重新生成占位图（可选）

```bash
python tools/gen-art.py        # 生成 assets/img/*.svg
python tools/preview.py all    # 输出 tools/preview/*.png 便于预览
```
