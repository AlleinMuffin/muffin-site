/** 滚动揭示：元素进入视口时淡入上移。不支持 IntersectionObserver 时直接全部显示。 */
export function initReveal(): void {
  const items = Array.from(document.querySelectorAll<HTMLElement>("[data-reveal]"));
  if (!items.length) return;

  if (!("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        (entry.target as HTMLElement).classList.add("is-visible");
        io.unobserve(entry.target);
      });
    },
    { rootMargin: "0px 0px -10% 0px", threshold: 0.08 }
  );

  items.forEach((el) => io.observe(el));
}
