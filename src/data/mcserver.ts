/**
 * /mcserver 页面的内容配置。
 * 以后改模组清单、公告、规则都只动这个文件，页面结构不用碰。
 */

/**
 * 模组清单不在本文件 —— 它由 tools/sync-mods.py 从整合包仓库生成到 ./mods.ts。
 * 仓库里加了/删了模组，跑一次 `python tools/sync-mods.py` 即可。
 */

export interface Announcement {
  date: string;
  text: string;
}

export const announcements: Announcement[] = [
  { date: "2026-09-26", text: "服务器性能优化完成，TPS 已恢复到 19.8，欢迎回来挖矿。" },
  { date: "2026-09-20", text: "主城周边 4000×4000 区块已预生成，跑图不再卡顿。" },
  { date: "2026-09-15", text: "启动器 v1.2 发布，整合包更新现在走增量同步。" },
];

export const rules: string[] = [
  "不破坏他人建筑、不偷取他人物品 —— 这是唯一没有商量余地的规则。",
  "大型红石机械请做开关，长期高频运行的装置会被要求改造。",
  "农场类实体请控制规模，超量会被自动清理（清理前会有提示）。",
  "不在主城周边 200 格内乱挖乱建，给公共空间留点余地。",
  "遇到 bug 或卡顿，先记下时间与坐标再反馈，方便定位。",
];

/** 加入步骤；{host} 会被替换成配置里的真实 MC 地址 */
export const joinSteps: string[] = [
  "安装 Java 21（推荐 Temurin 发行版），并在启动器里指定好路径。",
  "下载整合包：用 Muffin Launcher 一键同步，或直接从整合包仓库手动安装。",
  "启动游戏 → 多人游戏 → 添加服务器，地址填 <code>{host}</code>。",
  "进服后先在聊天栏输入 /rules 查看完整规则，然后就可以开工了。",
];
