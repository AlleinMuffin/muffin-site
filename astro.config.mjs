// @ts-check
import { defineConfig } from "astro/config";

// 站点地址只在这里写一次；换正式域名时改这里（或设 PUBLIC_SITE_URL 环境变量）。
// 页面里一律用相对路径，不写死域名，所以改域名不需要动任何组件。
const SITE_URL = process.env.PUBLIC_SITE_URL || "https://muffinlab.dpdns.org";

export default defineConfig({
  site: SITE_URL,
  // 纯静态输出，可直接托管到 Cloudflare Pages / GitHub Pages / 任意静态服务器
  output: "static",
  build: {
    // 生成 /mcserver/index.html 这类目录结构，静态托管更友好
    format: "directory",
  },
  markdown: {
    shikiConfig: {
      theme: "github-dark-default",
      wrap: true,
    },
  },
});
