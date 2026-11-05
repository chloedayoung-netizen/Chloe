// Cloudflare Worker — 정적 화면(public/)은 assets로 서빙하고, /api/* 만 처리한다.
//   POST /api/chat   : 캐릭터 대화 (OpenRouter, OpenAI 호환)
//   POST /api/event  : 행동 로그 → Google Sheets(Apps Script 웹앱)
//   GET  /api/characters, /api/config
import { CHARACTERS, buildSystemPrompt, publicList, stageFor } from "./characters.js";
import { detectCrisis, CRISIS_REPLY, splitTags, cleanMemory } from "./safety.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const MAX_HISTORY = 20; // 최근 20개 메시지만 모델에 보낸다(비용 상한)
const MAX_USER_CHARS = 500;

function clip(s, n) {
  return typeof s === "string" ? s.slice(0, n) : "";
}

// 로그 한 줄. 대화 원문은 넣지 않는다.
async function logEvent(env, ev) {
  if (!env.SHEET_WEBHOOK_URL) return;
  const row = {
    token: env.SHEET_TOKEN || "",
    ts: new Date().toISOString(),
    uid: clip(ev.uid, 40),
    sid: clip(ev.sid, 40),
    type: clip(ev.type, 40),
    char: clip(ev.char, 20),
    src: clip(ev.src, 40),
    variant: clip(ev.variant, 10),
    data: JSON.stringify(ev.data || {}).slice(0, 1000),
  };
  try {
    await fetch(env.SHEET_WEBHOOK_URL, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(row),
    });
  } catch (_) {
    /* 로그 실패가 대화를 막지 않게 한다 */
  }
}

async function callModel(env, messages) {
  const base = env.OPENROUTER_BASE_URL || "https://openrouter.ai/api/v1";
  const t0 = Date.now();
  const res = await fetch(`${base}/chat/completions`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.OPENROUTER_API_KEY}`,
      "content-type": "application/json",
      "x-title": "character-chat-mvp",
    },
    body: JSON.stringify({
      model: env.MODEL,
      messages,
      max_tokens: Number(env.MAX_TOKENS || 400),
      temperature: 0.9,
      usage: { include: true }, // OpenRouter: 응답에 실제 비용(credits=USD) 포함
    }),
  });
  if (!res.ok) throw new Error(`model ${res.status}: ${(await res.text()).slice(0, 200)}`);
  const out = await res.json();
  const raw = out.choices?.[0]?.message?.content || "";
  const u = out.usage || {};
  return {
    raw,
    usage: {
      in: u.prompt_tokens || 0,
      out: u.completion_tokens || 0,
      costUsd: typeof u.cost === "number" ? u.cost : null,
      ms: Date.now() - t0,
    },
  };
}

async function handleChat(req, env, ctx) {
  const body = await req.json().catch(() => null);
  if (!body) return json({ error: "잘못된 요청입니다." }, 400);
  const ch = CHARACTERS[body.char];
  if (!ch) return json({ error: "없는 캐릭터입니다." }, 400);

  const history = (Array.isArray(body.history) ? body.history : [])
    .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
    .slice(-MAX_HISTORY)
    .map((m) => ({ role: m.role, content: clip(m.content, m.role === "user" ? MAX_USER_CHARS : 2000) }));
  const last = history[history.length - 1];
  const ending = body.ending === true;
  if (!ending && (!last || last.role !== "user")) return json({ error: "보낼 메시지가 없습니다." }, 400);

  const base = { uid: body.uid, sid: body.sid, char: ch.id, src: body.src, variant: body.variant };

  // 1) 위기 신호: 모델을 부르지 않고 고정 안내
  if (last && last.role === "user" && detectCrisis(last.content)) {
    ctx.waitUntil(logEvent(env, { ...base, type: "safety_crisis", data: { len: last.content.length } }));
    return json({ reply: CRISIS_REPLY, safety: true });
  }

  // 2) 모델 호출
  const bond = Math.max(0, Number(body.bond) || 0);
  const days = Math.min(365, Math.max(1, Number(body.days) || 1));
  const system = buildSystemPrompt(ch, {
    bond,
    days,
    memories: (Array.isArray(body.memories) ? body.memories : []).map((m) => clip(m, 80)),
    lastHook: clip(body.lastHook, 200),
    nickname: clip(body.nickname, 12),
    ending,
  });
  const msgs = [{ role: "system", content: system }, { role: "assistant", content: ch.opening }, ...history];
  if (ending) msgs.push({ role: "user", content: "(오늘은 이만 가 볼게)" });

  let result;
  try {
    result = await callModel(env, msgs);
  } catch (e) {
    ctx.waitUntil(logEvent(env, { ...base, type: "error", data: { msg: String(e.message).slice(0, 200) } }));
    return json({ error: "캐릭터가 잠시 자리를 비웠어요. 조금 뒤 다시 보내 주세요." }, 502);
  }

  const { text, memory, hook } = splitTags(result.raw);
  const mem = cleanMemory(memory);
  ctx.waitUntil(
    logEvent(env, {
      ...base,
      type: ending ? "ai_goodbye" : "ai_reply",
      data: {
        stage: stageFor(bond, days).name,
        days,
        userLen: last && last.role === "user" ? last.content.length : 0,
        replyLen: text.length,
        memorySaved: Boolean(mem),
        ...result.usage,
      },
    })
  );
  return json({ reply: text, memory: mem, hook: ending ? hook : "", usage: result.usage });
}

const ALLOWED_EVENTS = new Set([
  "visit", "age_ok", "char_open", "session_start", "user_msg", "end_click",
  "paywall_view", "paywall_choice", "feedback", "return_banner", "nickname_set",
  "reminder_set", "pay_link_click",
]);

async function handleEvent(req, env, ctx) {
  const ev = await req.json().catch(() => null);
  if (!ev || !ALLOWED_EVENTS.has(ev.type)) return json({ ok: false }, 400);
  // 피드백 자유 문구는 사용자가 직접 입력한 경우에만, 길이 제한
  if (ev.type === "feedback" && ev.data && typeof ev.data.text === "string") ev.data.text = ev.data.text.slice(0, 300);
  ctx.waitUntil(logEvent(env, ev));
  return json({ ok: true });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/api/characters") return json(publicList());
    if (url.pathname === "/api/config")
      return json({
        freeTurns: Number(env.FREE_TURNS_PER_DAY || 30),
        bonusTurns: Number(env.BONUS_TURNS || 10),
        payLink: env.PAY_LINK || "", // 실제 소액 송금 링크(선택). 비어 있으면 결제 의향만 기록
      });
    if (url.pathname === "/api/chat" && req.method === "POST") return handleChat(req, env, ctx);
    if (url.pathname === "/api/event" && req.method === "POST") return handleEvent(req, env, ctx);
    if (url.pathname.startsWith("/api/")) return json({ error: "not found" }, 404);
    return env.ASSETS.fetch(req);
  },
};
