// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import { readBlogLastmod } from "./src/lib/blog-lastmod.mjs";

// 站点地址只在这里写一次；换正式域名时改这里（或设 PUBLIC_SITE_URL 环境变量）。
// 页面里一律用相对路径，不写死域名，所以改域名不需要动任何组件。
// sitemap 的绝对地址也由这里推导，换域名时 sitemap 会跟着变，不需要另外维护。
const SITE_URL = process.env.PUBLIC_SITE_URL || "https://muffinlab.dpdns.org";

// 文章路径 -> 最后更新时间，构建时从 src/content/blog/*.md 的 frontmatter 读出
const blogLastmod = readBlogLastmod();

export default defineConfig({
  site: SITE_URL,
  // 纯静态输出，可直接托管到 Cloudflare Pages / GitHub Pages / 任意静态服务器
  output: "static",
  build: {
    // 生成 /mcserver/index.html 这类目录结构，静态托管更友好
    format: "directory",
  },
  integrations: [
    sitemap({
      // 给文章单独标 lastmod（优先 updatedDate，其次 pubDate），爬虫能看出哪篇是新的。
      // 不用插件的全局 lastmod 选项——那个会把所有页面标成同一个构建时间，等于没标。
      serialize: (item) => {
        const lastmod = blogLastmod.get(new URL(item.url).pathname);
        return lastmod ? { ...item, lastmod } : item;
      },
    }),
  ],
  markdown: {
    shikiConfig: {
      theme: "github-dark-default",
      wrap: true,
    },
  },
});
