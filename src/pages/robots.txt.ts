import type { APIRoute } from "astro";

/**
 * 生成 /robots.txt。
 *
 * 用端点而不是 public/ 下的静态文件，是为了让 Sitemap 地址复用 astro.config.mjs 里的
 * site 配置——以后换域名只改那一处，这里不会漏。
 * Astro 在 output:"static" 下会把这个端点直接输出成 dist/robots.txt。
 *
 * 注意：Allow: / 是显式放行，不是屏蔽。Cloudflare 会在 origin 没有 robots.txt 时
 * 自动塞一份只有注释的 content-signals 文件，我们提供了自己的就会以这份为准。
 */
export const GET: APIRoute = ({ site }) => {
  const origin = site ?? new URL("https://muffinlab.dpdns.org");
  const sitemapUrl = new URL("sitemap-index.xml", origin).href;

  const body = [
    "# muffinlab.dpdns.org",
    "User-agent: *",
    "Allow: /",
    "",
    `Sitemap: ${sitemapUrl}`,
    "",
  ].join("\n");

  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
};
