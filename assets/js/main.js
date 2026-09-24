/* ==========================================================================
   MUFFIN — interactions
   ========================================================================== */
"use strict";

/* --------------------------------------------------------------------------
 * Edit this block to plug in your real server / links.
 * 实时状态会依次尝试 STATUSES 里的多个数据源，全部失败才回落到这里的静态值
 * （此时胶囊显示 NO SIGNAL，不会伪装成 ONLINE）。
 * ------------------------------------------------------------------------ */
const SERVER = {
  name: "Mechanomania Aeronautics",
  ip: "play.simpfun.cn:32883", // 自定义端口，和 IP 一起显示、一起复制
  version: "1.21.1",
  players: 0,
  max: 20,
  motd: "Mechanomania Aeronautics",
  liveStatus: true, // set false to skip the online lookup entirely
  refreshMs: 60000, // 自动刷新间隔
  timeoutMs: 6000, // 单个数据源的超时上限（跨洲探测较慢，别设太短）
};

/* --------------------------------------------------------------------------
 * 状态探测：三个源并行查询，投票决定结果。
 *
 * 为什么要三个？这些 API 都在 CDN 后面，某个边缘节点会把一次"失败探测"的结果
 * 缓存下来；访客下次正好命中那个节点就会看到莫名其妙的 OFFLINE。
 * 解决办法有两条：
 *   1) URL 带随机时间戳 —— 每次都是全新缓存键，拿到的必然是源站新鲜数据；
 *   2) 多源投票 —— 只要有任何一个源确认在线就判定在线，单个节点的坏缓存无法一票否决。
 * ------------------------------------------------------------------------ */
const stripColorCodes = (s) => String(s || "").replace(/§[0-9a-fk-orA-FK-OR]/g, "").trim();

// 拆出 host / port，minetools 用的是 /ping/<host>/<port> 这种路径形式
const HOST_PORT = (() => {
  const i = SERVER.ip.lastIndexOf(":");
  return i > -1 ? [SERVER.ip.slice(0, i), SERVER.ip.slice(i + 1)] : [SERVER.ip, "25565"];
})();

// 加随机参数穿透 CDN 缓存
const bust = (u) => u + (u.indexOf("?") > -1 ? "&" : "?") + "_=" + Date.now();

const STATUS_SOURCES = [
  {
    name: "mcsrvstat.us",
    url: () => bust("https://api.mcsrvstat.us/3/" + SERVER.ip),
    parse: (d) => ({
      online: d.online,
      players: d.players && d.players.online,
      max: d.players && d.players.max,
      version: d.version,
      motd: d.motd && d.motd.clean && d.motd.clean[0],
    }),
  },
  {
    name: "mcstatus.io",
    url: () => bust("https://api.mcstatus.io/v2/status/java/" + SERVER.ip),
    parse: (d) => ({
      online: d.online,
      players: d.players && d.players.online,
      max: d.players && d.players.max,
      version: d.version && d.version.name_clean,
      motd: d.motd && d.motd.clean,
    }),
  },
  {
    // 注意：这个源离线时也返回 HTTP 200，只是 body 变成 {"error": "..."}，
    // 所以只能靠"有没有 players.online"来判断，不能看状态码。
    name: "minetools.eu",
    url: () => bust("https://api.minetools.eu/ping/" + HOST_PORT[0] + "/" + HOST_PORT[1]),
    parse: (d) => ({
      online: Boolean(d.players && typeof d.players.online === "number"),
      players: d.players && d.players.online,
      max: d.players && d.players.max,
      version: d.version && d.version.name,
      motd: stripColorCodes(d.description),
    }),
  },
];

/* --------------------------------------------------------------------------
 * Small helpers
 * ------------------------------------------------------------------------ */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* --------------------------------------------------------------------------
 * Server status (static values + optional live lookup)
 * ------------------------------------------------------------------------ */
function renderStatus({ state, players, max, version, motd, note }) {
  const pill = $("#status-pill");
  const statusText = $("#status-text");

  if (pill && statusText) {
    pill.classList.toggle("is-offline", state === "offline");
    pill.classList.toggle("is-pending", state === "checking" || state === "unknown");
    pill.dataset.state = state;
    statusText.textContent =
      state === "online" ? "ONLINE" : state === "offline" ? "OFFLINE" : state === "checking" ? "CHECKING" : "NO SIGNAL";
  }

  // 离线时人数是未知的，显示占位符而不是上一次的旧数字，避免"写着离线却还有人数"的矛盾
  const unknownPlayers = state === "offline" || players === undefined || players === null;
  $("#stat-players").textContent = unknownPlayers ? "–" : String(players);
  $("#stat-max").textContent = String(max !== undefined && max !== null ? max : SERVER.max);
  if (version) $("#stat-version").textContent = version;
  if (motd) $("#stat-motd").textContent = motd;

  const fill = $(".bar__fill");
  const bar = $(".stat--players .bar");
  const pct = unknownPlayers ? 0 : Math.min(100, Math.round((players / (max || SERVER.max)) * 100));
  if (fill) fill.style.setProperty("--pct", pct + "%");
  if (bar) {
    bar.setAttribute(
      "aria-label",
      unknownPlayers ? "服务器离线，人数未知" : "玩家占用 " + players + " / " + (max || SERVER.max)
    );
  }

  const checked = $("#status-checked");
  if (checked) {
    const t = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    checked.textContent = note ? note + " · " + t : "updated " + t;
  }
}

/* 数据源全部不可用时的兜底：保留静态值，但明确标注"未经验证" */
function applyStaticStatus(state = "unknown", note = "no data") {
  renderStatus({
    state,
    note,
    version: SERVER.version,
    motd: SERVER.motd,
    max: SERVER.max,
    players: SERVER.players,
  });
}

/* 探测单个数据源。返回 null 表示"这个源没给我有效答案"（超时/被墙/格式异常），
 * 注意区分"没答案"和"明确回答离线"——两者含义完全不同。 */
async function probe(source) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), SERVER.timeoutMs);
  try {
    const res = await fetch(source.url(), { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(timer);
    if (!res.ok) return null;
    const data = await res.json();
    if (!data || typeof data !== "object") return null;
    const parsed = source.parse(data);
    if (typeof parsed.online !== "boolean") return null; // 拿不到明确结论就不参与投票
    parsed.via = source.name;
    if (window.console && console.debug) console.debug("[status]", source.name, data);
    return parsed;
  } catch {
    clearTimeout(timer);
    return null;
  }
}

/* 三个源并行查询 + 投票：
 * 任何一个源确认在线 → ONLINE（防止单个边缘节点的坏缓存误判宕机）
 * 全部源都明确回答离线 → OFFLINE（这个结论可信）
 * 全部源都拿不到答案 → NO SIGNAL（无法验证，不假装在线） */
async function fetchLiveStatus() {
  renderStatus({ state: "checking", note: "checking", players: undefined, max: SERVER.max });

  const answered = (await Promise.all(STATUS_SOURCES.map(probe))).filter(Boolean);
  const agree = answered.length + "/" + STATUS_SOURCES.length;

  const live = answered.find((r) => r.online === true);
  if (live) {
    renderStatus({
      state: "online",
      note: agree + " sources agree",
      players: live.players,
      max: live.max,
      version: live.version,
      // 优先显示服务器真实 MOTD（可能带季节活动文案），取不到再用本地配置
      motd: live.motd || SERVER.motd,
    });
    return;
  }

  if (answered.length > 0) {
    // 所有能访问到的源都说离线，可以采信
    renderStatus({ state: "offline", note: agree + " sources agree", players: null, version: SERVER.version });
    return;
  }

  applyStaticStatus("unknown", "sources unreachable");
}

applyStaticStatus("checking", "waiting");
if (SERVER.liveStatus && navigator.onLine) {
  fetchLiveStatus();

  if (SERVER.refreshMs > 0) {
    setInterval(() => {
      if (document.hidden) return; // 标签页不可见时不浪费请求
      fetchLiveStatus();
    }, SERVER.refreshMs);

    // 重新回到页面时，如果离开得比较久就立刻刷新一次
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) fetchLiveStatus();
    });
  }
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


