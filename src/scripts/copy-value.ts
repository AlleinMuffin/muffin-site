/** 通用复制：任何带 data-copy-value 的按钮，点击复制该属性的值。 */
async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* 落到下面的兜底方案 */
  }

  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "-1000px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

export function initCopyValue(): void {
  document.querySelectorAll<HTMLButtonElement>("[data-copy-value]").forEach((btn) => {
    const label = btn.querySelector<HTMLElement>("[data-copy-label]");
    const original = label?.textContent ?? "";
    let timer: number | undefined;

    btn.addEventListener("click", async () => {
      const ok = await copyText(btn.dataset.copyValue ?? "");
      if (!label) return;
      label.textContent = ok ? "✓ 已复制" : "手动复制";
      btn.classList.toggle("is-copied", ok);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        label.textContent = original;
        btn.classList.remove("is-copied");
      }, 1500);
    });
  });
}
