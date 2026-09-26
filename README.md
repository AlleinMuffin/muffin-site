# MuffinLab

> MuffinLab 是一个属于 Muffin 的个人门户：以 Minecraft 服务器为视觉核心，
> 同时承载项目、工具、博客与开发日志。

- 站点：`MuffinLab`　个人品牌：`Muffin`
- MC 服务器：`Mechanomania Aeronautics`
- 技术栈：**Astro**（静态输出，零 JS 默认）+ 原生 CSS 设计系统 + Markdown 内容集合

---

## 目录结构

```
src/
  config/site.ts        ★ 全站唯一配置源（域名 / MC 地址 / GitHub / 导航）
  data/
    projects.ts         项目数据（新增项目只改这里）
    gallery.ts          相册数据
    mcserver.ts         /mcserver 的公告 / 规则 / 加入步骤
    mods.ts             ★ 模组清单（脚本生成，不要手改）
  content/blog/*.md     开发日志（新增文章 = 新建一个 .md）
  components/           Navbar / Footer / ServerStatusCard / Gallery / 各卡片
  layouts/BaseLayout    head 元数据 + 导航 + 页脚 + 交互脚本
  pages/                index, mcserver, projects, blog, about
  scripts/              nav / reveal / lightbox / copy-ip / mc-status / mod-filter
tools/
  sync-mods.py          ★ 从整合包仓库拉取真实模组清单
  gen-art.py            生成像素风占位图
  styles/global.css     设计系统（配色 token + 组件样式）
public/
  gallery/*.svg         服务器截图（占位图，可替换）
  fonts/*.woff2         自托管 Inter / JetBrains Mono
```

## 本地开发

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # 输出到 dist/
npm run preview  # 预览构建产物
```

## ★ 换域名 / 换 MC 地址 / 换 GitHub

**只需要改 `src/config/site.ts`**，页面和组件一行都不用动 —— 站内全部使用根相对路径
（`/mcserver` 这种），域名只出现在 canonical / OG 这类**必须绝对**的元数据里。

也可以用环境变量覆盖（适合 Cloudflare Pages 的构建配置）：

```bash
PUBLIC_SITE_URL=https://你的域名       # 网站地址
PUBLIC_MC_HOST=你的真实MC地址           # MC 服务器地址（和网站域名是两回事）
PUBLIC_GITHUB_URL=https://github.com/你 # GitHub 主页
```

> 注意：`mc.host` 是 **MC 服务器真实地址**（如 `play.example.com:32883`），
> 和网站域名毫无关系，状态查询永远用它。

## 添加内容

| 想加什么 | 怎么做 |
| --- | --- |
| 新项目 | 在 `src/data/projects.ts` 里加一条；详情页 `/projects/<slug>` 自动生成 |
| 新文章 | 在 `src/content/blog/` 新建 `.md`（frontmatter：title / description / pubDate / tags）；列表与详情页自动生成 |
| 新截图 | 图片放 `public/gallery/`，改 `src/data/gallery.ts` |
| 公告 / 规则 / 加入步骤 | 改 `src/data/mcserver.ts` |
| 新板块 | 在 `src/config/site.ts` 的 `nav` 加一项 + 新建 `src/pages/<路径>.astro` |

### 同步模组清单

模组清单**不是手写的**，是从整合包仓库自动拉的：

```bash
python tools/sync-mods.py                                  # 默认仓库
python tools/sync-mods.py --repo 用户/仓库 --branch main    # 指定仓库
```

脚本会读取仓库 `mods/` 下的所有 `.jar`，解析出显示名与版本，生成
`src/data/mods.ts` 并按关键词自动分类（Create 生态 / 性能优化 / 客户端 UI …）。
整合包增删模组后跑一次，然后提交即可。

- 个别文件名解析得不好看？在 `tools/sync-mods.py` 的 `OVERRIDES` 里指定
  `文件名 -> (显示名, 版本)`，或在 `PRETTY` 里改显示名。
- 分类是关键词匹配的启发式规则，见同文件的 `CATEGORY_RULES`，可自行调整。
- 页面带搜索框（支持搜原始文件名）与分类筛选，Esc 可清空搜索。

## MC 状态是怎么查的

三个源**并行投票**，任一源确认在线即判定在线：

1. `api.mcsrvstat.us`
2. `api.mcstatus.io`
3. `api.minetools.eu`

这么做的原因：这些 API 都在 CDN 后面，边缘节点会缓存某次失败探测的结果，
访客命中该节点就会看到假的 OFFLINE。加上 URL 随机时间戳（绕过缓存）+ 多源投票后，
单个节点的坏缓存无法一票否决。

状态有四态，不会在没有数据时假装在线：

| 状态 | 含义 |
| --- | --- |
| `ONLINE` | 有源确认在线 |
| `OFFLINE` | 所有可达的源都明确回答离线 |
| `CHECKING` | 正在查询 |
| `NO SIGNAL` | 三个源都连不上，无法验证 |

默认 60 秒自动刷新，标签页不可见时跳过。不想发任何网络请求就把
`site.ts` 里的 `mc.liveStatus` 设为 `false`。

## 部署到 Cloudflare Pages（当前方案：push 即上线）

1. 把本仓库推到 GitHub
2. Cloudflare Dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. 选中本仓库，构建配置填：

   | 字段 | 值 |
   | --- | --- |
   | Framework preset | `Astro` |
   | Build command | `npm run build` |
   | Build output directory | `dist` |
   | Node version | **必须 22.12+**（Astro 7 的硬性要求，低于此版本构建直接失败） |

   推荐再显式加一个环境变量 `NODE_VERSION = 22` 兜底（仓库根目录的 `.node-version`
   也写了 22，双保险）。

4. 部署完成后 → **Custom domains** → 绑定 `muffinlab.dpdns.org`
5. 域名已在同一个 Cloudflare 账户下，DNS 记录会自动建好，等证书签发即可（几分钟）

**以后每次 `git push` 都会自动重新部署，不用再本地构建和手动上传。**

### 从 Workers 迁移到 Pages 的注意事项

`muffinlab.dpdns.org` 之前是绑在 Worker（自定义域名）上的，**同一个主机名不能同时归
Worker 和 Pages**，按这个顺序做，避免记录冲突：

1. Workers & Pages → 你的 Worker → **Settings → Domains & Routes** → 删掉 `muffinlab.dpdns.org`
   （它自动创建的那条 AAAA 记录会一并移除）
2. DNS → 删掉手动加的 A 记录（`@` → `192.0.2.1`），否则 Pages 建记录时会报"记录已存在"
3. Pages → **Custom domains** → 绑定 `muffinlab.dpdns.org`
4. 等 1–5 分钟 + 证书签发；期间站点会有几分钟不可访问，属正常

绑定后 DNS 里应该同时有 IPv4 与 IPv6 的 Cloudflare 边缘地址。

### DNS 备忘（originless 场景）

站点是纯静态 Workers/Pages，没有真实源站 IP，所以 DNS 填的是 Cloudflare 官方保留地址：

| 类型 | 值 | 说明 |
| --- | --- | --- |
| A | `192.0.2.1` | RFC 5737 保留段，开橙云后流量不会真去这里 |
| AAAA | `100::` | 同上，IPv6 的保留地址 |

**代理状态（橙云）必须开**，关掉就变成直连保留地址，站点立刻打不开。

> 仓库是纯静态输出，托管到 Vercel / Netlify / GitHub Pages / 任意 Nginx
> 也都是同一套：`npm run build` 后把 `dist/` 传上去。

## 待办 / 占位内容

- [ ] `public/gallery/` 里的 7 张图是脚本生成的像素风占位图（`python tools/gen-art.py` 可重新生成），
      换成真实服务器截图时建议导出 **WebP**，体积能从 1.1MB 降到 200KB 以内
- [ ] `og:image` 现在指向 SVG，**微信等平台不支持 SVG 缩略图**，换图时导出 1200×630 的 JPG/PNG
- [x] 模组清单已接入真实数据：192 个模组，来自 `Muffin-s-ModPack-Mod-Updated` 仓库的 `mods/`
- [ ] `Server Tools` / `Datapack Experiments` 还没有独立仓库，GitHub 链接暂指向主页
- [ ] `siteConfig.author.contact` 为空，填上后 /about 才会显示联系方式那一块
- [ ] `Server Tools` / `Datapack Experiments` 还没有独立仓库，暂时链接到 GitHub 主页
- [ ] `src/config/site.ts` 的 `contact` 为空，填了才会显示联系方式区块
- [ ] 可选：加 `robots.txt`、`sitemap.xml`（`@astrojs/sitemap`）与 RSS

## 设计约束（改样式前先看）

- 配色：`#08090B` 背景 / `#6EE7B7` 薄荷强调 / `#4ADE80` 在线状态
- 薄荷绿是**唯一**核心强调色，只出现在按钮、在线状态、链接 hover 与少量图标
- 不用大渐变、不用霓虹彩虹、不过度玻璃拟态
- 动画克制：Hero 淡入上移 0.8s、滚动揭示 600ms、卡片 hover 上浮 4px、图片 hover 放大 1.04
- `prefers-reduced-motion` 下所有动画关闭
