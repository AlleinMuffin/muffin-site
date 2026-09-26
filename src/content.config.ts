import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

/**
 * 开发日志（博客）。
 * 新增文章 = 在 src/content/blog/ 里新建一个 .md，不用改任何页面或路由。
 */
const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
