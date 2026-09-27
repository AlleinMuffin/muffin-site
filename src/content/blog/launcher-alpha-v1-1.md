---
title: 启动器 alpha-v1.1 发布
description: 暂时移除自动探测功能，新增「帮助」按钮。版本信息以 GitHub Release 为准。
pubDate: 2026-08-17
updatedDate: 2026-09-26
tags: ["发布", "工具"]
---

Muffin Launcher 是用来给群友更新服务器整合包的：双击运行 → 选手动模式 → 选
`HMCL.exe` 和 `mods` 文件夹 → 点启动，本地模组就对齐到服务器端。它服务的是服务器
在跑的「重度机械症：航空学」整合包。

## alpha-v1.1（2026-08-17）

更新内容照 Release 原文：

1. 暂时移除了自动探测功能
2. 添加「帮助」按钮

发布产物：`MuffinLauncher-alpha-v1.1.exe`，15,763,089 字节（约 15 MB）。
下载地址见 [Releases 页面](https://github.com/AlleinMuffin/Muffin-s-ModPack-Mod-Updated/releases/latest)。

## 为什么移除自动探测

alpha-v1.0 的说明里写明了「自动探测有 bug，务必选手动」，这版索性移除。

## 使用前提

- 需要本地已装好 HMCL（指定它的 exe 路径）
- 需要指定游戏目录里的 `mods` 文件夹
- 目前只有 Windows 版

整合包「重度机械症：航空学」的模组清单放在同一个仓库的 `mods/` 目录，
本站 `/mcserver` 上的 192 个模组也是从那自动同步的。
