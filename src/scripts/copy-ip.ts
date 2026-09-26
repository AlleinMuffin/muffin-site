/** 复制服务器地址：优先 Clipboard API，失败回落隐藏 textarea（兼容 file:// / 老浏览器）。 */
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

export function initCopyIp(host: string): void {
  document.querySelectorAll<HTMLButtonElement>("[data-copy-ip]").forEach((btn) => {
    const label = btn.querySelector<HTMLElement>("[data-copy-label]");
    let timer: number | undefined;

    btn.addEventListener("click", async () => {
      const ok = await copyText(host);
      if (!label) return;
      label.textContent = ok ? "✓ COPIED" : "手动复制";
      btn.classList.toggle("is-copied", ok);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        label.textContent = "Copy IP";
        btn.classList.remove("is-copied");
      }, 1500);
    });
  });
}
