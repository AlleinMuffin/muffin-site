/**
 * MuffinLab 全站唯一配置源。
 *
 * 换域名 / 换 MC 地址 / 换 GitHub 账号，都只需要改这个文件（或设置对应的
 * 环境变量），不需要动任何页面或组件 —— 所有站内链接都用相对路径。
 *
 * 环境变量优先级高于默认值，方便在 Cloudflare Pages 的构建配置里覆盖：
 *   PUBLIC_SITE_URL     网站地址（用于 canonical / OG 等绝对地址）
 *   PUBLIC_MC_HOST      MC 服务器真实地址（注意：和网站域名是两回事）
 *   PUBLIC_GITHUB_URL   GitHub 主页
 */
const env = import.meta.env;

export const siteConfig = {
  /** 站点品牌名（导航栏 / 页脚） */
  siteName: "MuffinLab",
  /** 个人品牌 */
  brand: "Muffin",
  /** 站点一句话定位 */
  tagline: "A small world built with code, blocks and ideas.",
  description:
    "MuffinLab 是 Muffin 的个人空间：Minecraft 服务器、AI 小工具、项目展示与开发日志。",

  /** 网站地址 —— 只用于 canonical / og:url 等必须是绝对地址的场景 */
  siteUrl: env.PUBLIC_SITE_URL || "https://muffinlab.dpdns.org",

  /** GitHub 主页 */
  github: env.PUBLIC_GITHUB_URL || "https://github.com/AlleinMuffin",

  /** ================= MC 服务器 =================
   * 这里填的是 MC 服务器的真实地址，和网站域名没有任何关系。
   * 带端口就写端口（例如 play.example.com:32883），页面会原样显示并一起复制。
   */
  mc: {
    /** 服务器全名 */
    name: "Mechanomania Aeronautics",
    /** 真实 MC 地址（状态查询、复制 IP 都用它） */
    host: env.PUBLIC_MC_HOST || "play.simpfun.cn:32883",
    /** 静态兜底数据：三个状态源都查不到时才显示 */
    fallback: {
      version: "1.21.1",
      max: 20,
    },
    /** 状态查询开关；关掉则完全静态，不发任何网络请求 */
    liveStatus: true,
    /** 自动刷新间隔（毫秒） */
    refreshMs: 60_000,
    /** 单个数据源超时（毫秒）—— 跨洲探测较慢，别设太短 */
    timeoutMs: 6_000,
    /** 简介，用于 /mcserver */
    intro:
      "Mechanomania Aeronautics 是一个以机械与航空为主题的 Minecraft 生存服务器：自己造机器、修飞船、把地图一点点填满。",
  },

  /** 导航栏。以后加板块只需在这里加一项 */
  nav: [
    { label: "Server", href: "/mcserver" },
    { label: "Projects", href: "/projects" },
    { label: "Blog", href: "/blog" },
    { label: "About", href: "/about" },
  ],

  /** 页脚 */
  footer: {
    copyright: "MUFFINLAB © 2026",
    signature: "Built with curiosity & caffeine.",
  },

  /** 联系方式（/about 用；不想公开就留空字符串，对应区块会自动隐藏） */
  contact: {
    email: "",
    discord: "",
    qq: "",
  },
} as const;

/** 拼出绝对地址，仅用于 canonical / OG 这类必须绝对的场合 */
export function absoluteUrl(path: string): string {
  const base = String(siteConfig.siteUrl).replace(/\/$/, "");
  return base + (path.startsWith("/") ? path : "/" + path);
}

/** 由 MC 地址拆出 host / port，minetools 用的是 /ping/<host>/<port> 形式 */
export function splitMcHost(host: string): [string, string] {
  const i = host.lastIndexOf(":");
  return i > -1 ? [host.slice(0, i), host.slice(i + 1)] : [host, "25565"];
}
