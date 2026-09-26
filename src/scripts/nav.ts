/** 导航栏：滚动后加毛玻璃背景；移动端 ☰ 展开/收起。 */
export function initNav(): void {
  const nav = document.querySelector<HTMLElement>("#nav");
  const toggle = document.querySelector<HTMLButtonElement>("#nav-toggle");
  const links = document.querySelector<HTMLElement>("#nav-links");

  if (nav) {
    const onScroll = () => {
      nav.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  if (!toggle || !links) return;

  const setOpen = (open: boolean) => {
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "关闭菜单" : "打开菜单");
    links.classList.toggle("is-open", open);
  };

  toggle.addEventListener("click", () => {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  // 点任意导航项后收起（移动端跳转后不该挡着内容）
  links.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => setOpen(false));
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setOpen(false);
  });

  // 视口放大回桌面时，确保菜单状态不会残留
  window.addEventListener("resize", () => {
    if (window.innerWidth > 640) setOpen(false);
  });
}
