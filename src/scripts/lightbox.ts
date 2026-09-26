/** 全屏图片查看器：←→ 切换、Esc 关闭、打开时把焦点圈在弹层内。 */
export function initLightbox(): void {
  const box = document.querySelector<HTMLElement>("#lightbox");
  const img = document.querySelector<HTMLImageElement>("[data-lightbox-img]");
  const caption = document.querySelector<HTMLElement>("[data-lightbox-caption]");
  const triggers = Array.from(document.querySelectorAll<HTMLElement>("[data-lightbox-open]"));
  if (!box || !img || !triggers.length) return;

  let index = 0;
  let lastFocused: Element | null = null;

  const show = (i: number) => {
    const t = triggers[i];
    if (!t) return;
    index = i;
    const full = t.dataset.full || "";
    img.src = full;
    img.alt = t.getAttribute("aria-label") || "";
    if (caption) caption.textContent = t.dataset.caption || "";
  };

  const open = (i: number) => {
    lastFocused = document.activeElement;
    box.hidden = false;
    document.body.style.overflow = "hidden";
    show(i);
    const close = box.querySelector<HTMLElement>("[data-lightbox-close]");
    if (close) close.focus();
  };

  const close = () => {
    box.hidden = true;
    document.body.style.overflow = "";
    if (lastFocused instanceof HTMLElement) lastFocused.focus();
  };

  triggers.forEach((t, i) => {
    t.addEventListener("click", () => open(i));
  });

  box.querySelector("[data-lightbox-close]")?.addEventListener("click", close);
  box.querySelector("[data-lightbox-prev]")?.addEventListener("click", () => {
    show((index - 1 + triggers.length) % triggers.length);
  });
  box.querySelector("[data-lightbox-next]")?.addEventListener("click", () => {
    show((index + 1) % triggers.length);
  });

  // 点遮罩空白处关闭
  box.addEventListener("click", (e) => {
    if (e.target === box) close();
  });

  document.addEventListener("keydown", (e) => {
    if (box.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") show((index - 1 + triggers.length) % triggers.length);
    else if (e.key === "ArrowRight") show((index + 1) % triggers.length);
  });
}
