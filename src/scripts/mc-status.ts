/**
 * MC 服务器状态查询。
 *
 * 三个源并行投票的原因：这些 API 都在 CDN 后面，边缘节点会缓存某次失败的探测
 * 结果，访客命中那个节点就会看到假的 OFFLINE。所以：
 *   1) URL 带随机时间戳 —— 每次都是新缓存键；
 *   2) 多源投票 —— 任一源确认在线即判在线，单个坏缓存无法一票否决。
 * 严格区分「没答案」(null，不参与投票) 与「明确回答离线」(false)。
 */
import { siteConfig, splitMcHost } from "../config/site";

const mc = siteConfig.mc;

type Json = Record<string, any>;

interface Probe {
  online: boolean;
  players?: number;
  max?: number;
  version?: string;
  motd?: string;
  via?: string;
}

type State = "checking" | "online" | "offline" | "unknown";

const stripColorCodes = (s: unknown): string =>
  String(s ?? "").replace(/§[0-9a-fk-orA-FK-OR]/g, "").trim();

const [HOST, PORT] = splitMcHost(mc.host);
const bust = (u: string): string => u + (u.indexOf("?") > -1 ? "&" : "?") + "_=" + Date.now();

const SOURCES: { name: string; url: () => string; parse: (d: Json) => Probe }[] = [
  {
    name: "mcsrvstat.us",
    url: () => bust(`https://api.mcsrvstat.us/3/${mc.host}`),
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
    url: () => bust(`https://api.mcstatus.io/v2/status/java/${mc.host}`),
    parse: (d) => ({
      online: d.online,
      players: d.players && d.players.online,
      max: d.players && d.players.max,
      version: d.version && d.version.name_clean,
      motd: d.motd && d.motd.clean,
    }),
  },
  {
    // 注意：这个源服务器离线时也返回 HTTP 200，body 变成 {"error": "..."}，
    // 所以只能靠 players.online 是否存在判断，不能看状态码。
    name: "minetools.eu",
    url: () => bust(`https://api.minetools.eu/ping/${HOST}/${PORT}`),
    parse: (d) => ({
      online: Boolean(d.players && typeof d.players.online === "number"),
      players: d.players && d.players.online,
      max: d.players && d.players.max,
      version: d.version && d.version.name,
      motd: stripColorCodes(d.description),
    }),
  },
];

async function probe(source: (typeof SOURCES)[number]): Promise<Probe | null> {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), mc.timeoutMs);
  try {
    const res = await fetch(source.url(), { signal: ctrl.signal, cache: "no-store" });
    window.clearTimeout(timer);
    if (!res.ok) return null;
    const data = (await res.json()) as Json;
    if (!data || typeof data !== "object") return null;
    const parsed = source.parse(data);
    if (typeof parsed.online !== "boolean") return null; // 没明确结论就不投票
    parsed.via = source.name;
    return parsed;
  } catch {
    window.clearTimeout(timer);
    return null;
  }
}

function paint(card: HTMLElement, state: State, p: Partial<Probe>, note: string): void {
  const pill = card.querySelector<HTMLElement>("[data-status-pill]");
  const text = card.querySelector<HTMLElement>("[data-status-text]");
  const meta = card.querySelector<HTMLElement>("[data-status-meta]");
  const playersEl = card.querySelector<HTMLElement>("[data-stat-players]");
  const maxEl = card.querySelector<HTMLElement>("[data-stat-max]");
  const versionEl = card.querySelector<HTMLElement>("[data-stat-version]");
  const motdEl = card.querySelector<HTMLElement>("[data-stat-motd]");
  const fill = card.querySelector<HTMLElement>("[data-bar-fill]");
  const bar = card.querySelector<HTMLElement>(".bar");

  if (pill && text) {
    pill.classList.toggle("is-offline", state === "offline");
    pill.classList.toggle("is-pending", state === "checking" || state === "unknown");
    text.textContent =
      state === "online"
        ? "ONLINE"
        : state === "offline"
          ? "OFFLINE"
          : state === "checking"
            ? "CHECKING"
            : "NO SIGNAL";
  }

  // 离线时人数未知，显示占位符而不是上一次的旧数字
  const unknown =
    state === "offline" || p.players === undefined || p.players === null || Number.isNaN(p.players);
  const max = p.max ?? mc.fallback.max;

  if (playersEl) playersEl.textContent = unknown ? "–" : String(p.players);
  if (maxEl) maxEl.textContent = String(max);
  if (versionEl && p.version) versionEl.textContent = p.version;
  if (motdEl && p.motd) motdEl.textContent = p.motd;

  const pct = unknown ? 0 : Math.min(100, Math.round(((p.players ?? 0) / (max || 1)) * 100));
  if (fill) fill.style.setProperty("--pct", pct + "%");
  if (bar) {
    bar.setAttribute(
      "aria-label",
      unknown ? "服务器离线，人数未知" : `玩家占用 ${p.players} / ${max}`
    );
  }

  if (meta) {
    const t = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    meta.textContent = `${note} · ${t}`;
  }
}

async function refresh(): Promise<void> {
  const cards = Array.from(document.querySelectorAll<HTMLElement>("[data-mc-status]"));
  if (!cards.length) return;

  cards.forEach((c) =>
    paint(c, "checking", { max: mc.fallback.max }, "checking")
  );

  const answered = (await Promise.all(SOURCES.map(probe))).filter(
    (r): r is Probe => r !== null
  );
  const agree = `${answered.length}/${SOURCES.length} sources`;

  const live = answered.find((r) => r.online === true);
  if (live) {
    cards.forEach((c) =>
      paint(c, "online", { ...live, motd: live.motd || mc.name }, agree)
    );
    return;
  }

  if (answered.length > 0) {
    // 所有能访问到的源都说离线，可以采信
    cards.forEach((c) =>
      paint(c, "offline", { players: null, version: mc.fallback.version, max: mc.fallback.max }, agree)
    );
    return;
  }

  cards.forEach((c) =>
    paint(
      c,
      "unknown",
      { players: null, max: mc.fallback.max, version: mc.fallback.version, motd: mc.name },
      "sources unreachable"
    )
  );
}

export function initMcStatus(): void {
  if (!mc.liveStatus || !navigator.onLine) {
    // 关闭实时查询时不发请求，只把静态值标成「未验证」，不假装在线
    document.querySelectorAll<HTMLElement>("[data-mc-status]").forEach((c) =>
      paint(c, "unknown", { version: mc.fallback.version, max: mc.fallback.max, motd: mc.name }, "static")
    );
    return;
  }

  void refresh();

  if (mc.refreshMs > 0) {
    window.setInterval(() => {
      if (!document.hidden) void refresh(); // 标签页不可见时不浪费请求
    }, mc.refreshMs);

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) void refresh();
    });
  }
}

/** 整卡点击进入详情页（点复制按钮不触发） */
export function initCardLinks(): void {
  document.querySelectorAll<HTMLElement>("[data-href]").forEach((card) => {
    const href = card.dataset.href;
    if (!href) return;
    card.style.cursor = "pointer";
    card.addEventListener("click", (e) => {
      const t = e.target as HTMLElement | null;
      if (t && t.closest("button, a")) return; // 按钮和链接自己处理
      window.location.href = href;
    });
  });
}
