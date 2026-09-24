/* ==========================================================================
   MUFFIN — interactions
   ========================================================================== */
"use strict";

/* --------------------------------------------------------------------------
 * Edit this block to plug in your real server / links.
 * If `liveStatus` is true the page will try api.mcsrvstat.us first and
 * silently fall back to these static values when it fails.
 * ------------------------------------------------------------------------ */
const SERVER = {
  name: "Mechanomania Aeronautics",
  ip: "play.simpfun.cn:32883", // 自定义端口，和 IP 一起显示、一起复制
  version: "1.21.1",
  players: 0,
  max: 20,
  motd: "Mechanomania Aeronautics",
  liveStatus: true, // set false to skip the online lookup entirely
};

/* --------------------------------------------------------------------------
 * Small helpers
 * ------------------------------------------------------------------------ */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* --------------------------------------------------------------------------
 * Server status (static values + optional live lookup)
 * ------------------------------------------------------------------------ */
function renderStatus({ online, players, max, version, motd }) {
  const pill = $("#status-pill");
  const statusText = $("#status-text");
  if (pill && statusText) {
    pill.classList.toggle("is-offline", !online);
    statusText.textContent = online ? "ONLINE" : "OFFLINE";
  }
  if (players !== undefined) $("#stat-players").textContent = String(players);
  if (max !== undefined) $("#stat-max").textContent = String(max);
  if (version) $("#stat-version").textContent = version;
  if (motd) $("#stat-motd").textContent = motd;
  if (players !== undefined && max) {
    const pct = Math.min(100, Math.round((players / max) * 100));
    const fill = $(".bar__fill");
    if (fill) fill.style.setProperty("--pct", pct + "%");
    const bar = $(".stat--players .bar");
    if (bar) bar.setAttribute("aria-label", "玩家占用 " + players + " / " + max);
  }
  const checked = $("#status-checked");
  if (checked) {
    const t = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    checked.textContent = "updated " + t;
  }
}

function applyStaticStatus() {
  renderStatus({
    online: true,
    players: SERVER.players,
    max: SERVER.max,
    version: SERVER.version,
    motd: SERVER.motd,
  });
}

async function fetchLiveStatus() {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 6000);
  try {
    const res = await fetch("https://api.mcsrvstat.us/3/" + encodeURIComponent(SERVER.ip), {
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    if (!res.ok) return;
    const data = await res.json();
    if (!data || data.online === undefined) return;
    renderStatus({
      online: Boolean(data.online),
      players: data.players ? data.players.online : undefined,
      max: data.players ? data.players.max : undefined,
      version: data.version || undefined,
      // 优先显示服务器真实 MOTD（可能带季节活动文案），取不到再用本地配置
      motd: (data.motd && data.motd.clean && data.motd.clean[0]) || SERVER.motd,
    });
  } catch {
    /* offline / timeout -> static values already on screen */
  }
}

applyStaticStatus();
if (SERVER.liveStatus && navigator.onLine) {
  fetchLiveStatus();
}

/* --------------------------------------------------------------------------
 * Copy IP
 * ------------------------------------------------------------------------ */
const copyBtn = $("#copy-ip");
const copyLabel = $("#copy-ip-label");
let copyTimer = null;

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  // file:// or older browsers -> hidden textarea fallback
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(ta);
  }
}

if (copyBtn && copyLabel) {
  copyBtn.addEventListener("click", async () => {
    try {
      await copyText(SERVER.ip);
      copyBtn.classList.add("is-copied");
      copyLabel.textContent = "✓ Copied";
      clearTimeout(copyTimer);
      copyTimer = setTimeout(() => {
        copyBtn.classList.remove("is-copied");
        copyLabel.textContent = "Copy IP";
      }, 1500);
    } catch {
      copyLabel.textContent = "Copy failed";
      setTimeout(() => (copyLabel.textContent = "Copy IP"), 1500);
    }
  });
}

/* --------------------------------------------------------------------------
 * Navbar: scrolled state, mobile menu, scroll spy
 * ------------------------------------------------------------------------ */
const nav = $("#nav");
const navToggle = $("#nav-toggle");
const navLinks = $("#nav-links");

function onScrollNav() {
  if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 24);
}
window.addEventListener("scroll", onScrollNav, { passive: true });
onScrollNav();

function closeMenu() {
  if (!navLinks || !navToggle) return;
  navLinks.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
  navToggle.setAttribute("aria-label", "打开菜单");
}

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    const open = navLinks.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(open));
    navToggle.setAttribute("aria-label", open ? "关闭菜单" : "打开菜单");
  });
  navLinks.addEventListener("click", (e) => {
    if (e.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
}

// scroll spy — highlight the section currently in view
const spyTargets = ["server", "gallery", "projects", "github"]
  .map((id) => document.getElementById(id))
  .filter(Boolean);

if (spyTargets.length && "IntersectionObserver" in window) {
  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const link = $('.nav__link[href="#' + entry.target.id + '"]');
        if (!link) return;
        if (entry.isIntersecting) {
          $$(".nav__link").forEach((l) => l.classList.remove("is-active"));
          link.classList.add("is-active");
        }
      });
    },
    { rootMargin: "-40% 0px -55% 0px" }
  );
  spyTargets.forEach((t) => spy.observe(t));
}

/* --------------------------------------------------------------------------
 * Scroll reveal
 * ------------------------------------------------------------------------ */
const revealEls = $$("[data-reveal]");
if (revealEls.length) {
  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  }
}

/* --------------------------------------------------------------------------
 * Gallery lightbox
 * ------------------------------------------------------------------------ */
const lightbox = $("#lightbox");
const lbImg = $("#lightbox-img");
const lbCaption = $("#lightbox-caption");
const items = $$(".g-item__btn");
let lbIndex = 0;
let lastFocus = null;

function openLightbox(index) {
  if (!lightbox || !lbImg) return;
  const btn = items[index];
  if (!btn) return;
  lbIndex = index;
  lastFocus = document.activeElement;
  lbImg.src = btn.dataset.full || (btn.querySelector("img") || {}).src || "";
  lbImg.alt = (btn.querySelector("img") || {}).alt || "";
  lbCaption.textContent = btn.dataset.caption || "";
  lightbox.hidden = false;
  document.body.style.overflow = "hidden";
  $("#lightbox-close").focus();
}

function closeLightbox() {
  if (!lightbox) return;
  lightbox.hidden = true;
  document.body.style.overflow = "";
  if (lastFocus) lastFocus.focus();
}

function stepLightbox(delta) {
  openLightbox((lbIndex + delta + items.length) % items.length);
}

items.forEach((btn, i) => {
  btn.addEventListener("click", () => openLightbox(i));
});

if (lightbox) {
  $("#lightbox-close").addEventListener("click", closeLightbox);
  $("#lightbox-prev").addEventListener("click", () => stepLightbox(-1));
  $("#lightbox-next").addEventListener("click", () => stepLightbox(1));
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });
  document.addEventListener("keydown", (e) => {
    if (lightbox.hidden) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowLeft") stepLightbox(-1);
    if (e.key === "ArrowRight") stepLightbox(1);
    if (e.key === "Tab") {
      // keep focus inside the dialog
      const focusables = $$("button", lightbox);
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
}


