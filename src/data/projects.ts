import { siteConfig } from "../config/site";

export interface Project {
  /** 详情页地址：/projects/<slug> */
  slug: string;
  name: string;
  /** 一句话描述 */
  description: string;
  /** 标签，用于筛选 */
  tags: string[];
  /** 版本号（可选，展示为标签） */
  version?: string;
  /** GitHub 仓库地址；没有独立仓库时留空，会回落个人主页 */
  github?: string;
  /** 下载地址（有就显示 Download 按钮） */
  download?: string;
  /** 是否作为主推项目展示在顶部 */
  featured?: boolean;
  /** 详情页正文（数组即段落） */
  body?: string[];
}

const GITHUB_HOME = siteConfig.github;

export const projects: Project[] = [
  {
    slug: "muffin-launcher",
    name: "Muffin Launcher",
    description: "给群友同步服务器整合包用的小工具：指定启动器与 mods 目录，把本地模组对齐到服务器。",
    tags: ["工具", "整合包", "桌面端"],
    version: "alpha-v1.1",
    github: `${GITHUB_HOME}/Muffin-s-ModPack-Mod-Updated`,
    download: `${GITHUB_HOME}/Muffin-s-ModPack-Mod-Updated/releases/latest`,
    featured: true,
    body: [
      "Muffin Launcher 是给服务器群友更新整合包用的：双击运行 → 选手动模式 → 指定 HMCL.exe 和 mods 文件夹 → 点启动，本地模组就对齐到服务器端。",
      "当前版本 alpha-v1.1，2026-08-17 发布。这版的变化有两条：暂时移除了自动探测功能，新增了「帮助」按钮。发布产物是 Windows 下的 MuffinLauncher-alpha-v1.1.exe，约 15 MB。",
      "整合包「重度机械症：航空学」的模组清单就放在同一个仓库的 mods/ 目录里，本网站 /mcserver 上的模组清单也是从那儿自动同步的。",
    ],
  },
  {
    slug: "ai-toolbox",
    name: "AI Toolbox",
    description: "一组顺手的 AI 小工具：把日常重复的文本与数据处理流程脚本化。",
    tags: ["AI", "工具"],
    github: `${GITHUB_HOME}/AI`,
    body: [
      "AI Toolbox 收录的是我自己会反复用到的脚本：批量处理文本、整理数据、调用模型做摘要与分类。",
      "设计原则是能跑在本地就跑在本地，接口可替换，不绑定某一家服务商。",
    ],
  },
  {
    slug: "server-tools",
    name: "Server Tools",
    description: "备份、白名单与玩家数据管理的运维脚本合集，让服务器维护自动化。",
    tags: ["运维", "脚本"],
    // TODO: 这个仓库还不存在，暂时指向主页；建好后改成具体仓库地址
    body: [
      "服务器运维里最烦的是重复劳动：定期备份、白名单增删、玩家数据迁移。",
      "这套脚本把它们全部自动化，配合定时任务就能无人值守运行。",
    ],
  },
  {
    slug: "datapack-experiments",
    name: "Datapack Experiments",
    description: "数据包玩法实验：自定义掉落、进度与机制调整，随时可以拆开学习。",
    tags: ["数据包", "实验"],
    // TODO: 同上，仓库建好后替换成具体地址
    body: [
      "不装模组也能改玩法——这是数据包最有意思的地方。",
      "这里放的是各种实验：改掉落表、加进度、调整机制。每个包都尽量保持独立，方便单独取用和阅读。",
    ],
  },
];

/** 全部标签，供筛选按钮使用（自动去重，新增项目不用改这里） */
export const allTags: string[] = [...new Set(projects.flatMap((p) => p.tags))];

export const featuredProject = projects.find((p) => p.featured) ?? projects[0];
