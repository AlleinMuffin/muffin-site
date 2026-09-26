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
    description: "轻量启动器：一键同步整合包的模组、配置与资源包，开服即玩。",
    tags: ["工具", "整合包", "桌面端"],
    version: "v1.2.0",
    github: `${GITHUB_HOME}/Muffin-s-ModPack-Mod-Updated`,
    featured: true,
    body: [
      "Muffin Launcher 是为了解决「整合包更新一次，所有人的客户端就要重新配一遍」这个问题做的。",
      "它读取服务器端的模组清单，和本地做差异比对，只下载真正变化的部分；配置文件和资源包同理。玩家点一次就能回到和服务器完全一致的状态。",
      "目前支持 Windows，依赖 Java 17+。后续计划加上多版本隔离与启动参数预设。",
    ],
  },
  {
    slug: "industry-craft",
    name: "IndustryCraft Modpack",
    description: "以机械与航空为主题的 1.21.1 NeoForge 整合包，服务器正在跑的就是它。",
    tags: ["整合包", "Mod"],
    version: "1.21.1",
    github: `${GITHUB_HOME}/IndustryCraft-1.21.1-NeoForge`,
    body: [
      "IndustryCraft 是 Mechanomania Aeronautics 服务器当前使用的整合包，基于 NeoForge 1.21.1。",
      "核心是机械自动化与航空：从最基础的动力开始，一路做到自动产线、飞行器和跨维度物流。",
      "整合包配置与模组清单都放在仓库里，玩家可以直接对照排查本地环境问题。",
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
