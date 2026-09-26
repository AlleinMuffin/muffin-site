/** 全站入口：按职责组合各模块。 */
import { initNav } from "./nav";
import { initReveal } from "./reveal";
import { initLightbox } from "./lightbox";
import { initCopyIp } from "./copy-ip";
import { initMcStatus, initCardLinks } from "./mc-status";
import { siteConfig } from "../config/site";

function boot(): void {
  initNav();
  initReveal();
  initLightbox();
  initCopyIp(siteConfig.mc.host);
  initMcStatus();
  initCardLinks();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
