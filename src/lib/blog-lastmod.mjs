/**
 * 给 sitemap 用的「文章最后更新时间」表。
 *
 * 为什么需要这个：@astrojs/sitemap 只会从页面自身的 frontmatter 里认 `lastmod`，
 * 但博客是走 src/pages/blog/[slug].astro 动态路由渲染的，插件看到的是那个 .astro
 * 文件、不是每篇 .md，所以拿不到文章的 pubDate / updatedDate。
 * 这里直接读 src/content/blog/*.md 的 frontmatter 补上，让爬虫能分清哪篇是新的。
 *
 * 只在构建时执行，不参与浏览器打包。
 */
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const BLOG_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "content", "blog");

/** 从 frontmatter 文本里取一个形如 `pubDate: 2026-09-26` 的字段 */
function pickField(field, frontmatter) {
  const m = frontmatter.match(new RegExp(`^${field}:\\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\\s*$`, "m"));
  return m ? m[1] : null;
}

/**
 * @returns {Map<string, string>} 页面路径 -> ISO 时间字符串，例如 "/blog/demo/" -> "2026-09-26T00:00:00.000Z"
 */
export function readBlogLastmod() {
  const map = new Map();

  let files;
  try {
    files = readdirSync(BLOG_DIR);
  } catch {
    // 目录不存在时静默降级：sitemap 照常生成，只是没有 lastmod
    return map;
  }

  for (const file of files) {
    if (!file.endsWith(".md")) continue;

    let raw;
    try {
      raw = readFileSync(join(BLOG_DIR, file), "utf8");
    } catch {
      continue;
    }

    // 只取开头两个 --- 之间的 frontmatter 块
    const parts = raw.split(/^---[ \t]*$/m);
    const frontmatter = parts.length > 2 ? parts[1] : raw.slice(0, 1000);

    // 草稿不上线，sitemap 里也不该出现
    if (/^draft:[ \t]*true/m.test(frontmatter)) continue;

    // 有 updatedDate 就用它，否则退回 pubDate
    const date = pickField("updatedDate", frontmatter) ?? pickField("pubDate", frontmatter);
    if (!date) continue;

    const path = `/blog/${file.replace(/\.md$/, "")}/`;
    map.set(path, new Date(`${date}T00:00:00Z`).toISOString());
  }

  return map;
}
