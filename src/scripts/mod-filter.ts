/**
 * /mcserver 的模组清单筛选：搜索框 + 分类按钮。
 * 纯前端过滤，192 个模组也不需要分页。
 */
export function initModFilter(): void {
  const list = document.getElementById("mod-list");
  const input = document.getElementById("mod-search") as HTMLInputElement | null;
  const chips = document.getElementById("mod-chips");
  const countEl = document.getElementById("mod-count");
  const emptyEl = document.getElementById("mod-empty");
  if (!list || !input || !chips || !countEl) return;

  const items = Array.from(list.querySelectorAll<HTMLElement>(".mod-item"));
  const total = items.length;
  let activeCat = "all";
  let keyword = "";

  function apply(): void {
    let shown = 0;
    for (const el of items) {
      const catOk = activeCat === "all" || el.dataset.cat === activeCat;
      const keyOk = !keyword || (el.dataset.key || "").includes(keyword);
      const visible = catOk && keyOk;
      el.classList.toggle("is-hidden", !visible);
      if (visible) shown += 1;
    }
    countEl.innerHTML = `显示 <b>${shown}</b> / ${total}`;
    if (emptyEl) emptyEl.classList.toggle("is-hidden", shown !== 0);
  }

  input.addEventListener("input", () => {
    keyword = input.value.trim().toLowerCase();
    apply();
  });

  chips.addEventListener("click", (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>(".mod-chip");
    if (!btn) return;
    activeCat = btn.dataset.cat || "all";
    for (const c of chips.querySelectorAll<HTMLElement>(".mod-chip")) {
      c.classList.toggle("is-active", c === btn);
    }
    apply();
  });

  // Esc 清空搜索
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      input.value = "";
      keyword = "";
      apply();
    }
  });
}
