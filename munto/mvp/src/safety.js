// 안전 장치 — LLM에 맡기지 않고 코드로 먼저 거른다.
// 기준: 위기 신호는 캐릭터 연기를 멈추고 고정 안내로 응답한다.
// 대화 원문은 로그에 남기지 않는다(유형과 길이만).

const CRISIS = [
  /죽고\s*싶/, /자살/, /자해/, /극단적\s*(인\s*)?선택/, /살기\s*싫/, /사라지고\s*싶/,
  /목숨을\s*끊/, /손목을\s*긋/, /뛰어내리/, /유서/,
];

export function detectCrisis(text = "") {
  return CRISIS.some((re) => re.test(text));
}

export const CRISIS_REPLY = [
  "(잠깐 캐릭터 대신 운영자가 말씀드려요)",
  "지금 많이 힘드신 것 같아요. 혼자 견디지 않으셨으면 해요.",
  "자살예방상담전화 109 (24시간), 정신건강위기상담 1577-0199 로 바로 이야기 나눌 수 있어요.",
  "위급하면 112·119로 연락해 주세요. 원하시면 이 대화는 여기서 잠시 쉬어 가도 괜찮아요.",
].join("\n");

const MEMORY_TAG = /\[\[기억:\s*([^\]]+?)\]\]/g;
const HOOK_TAG = /\[\[내일:\s*([^\]]+?)\]\]/g;

// 모델 답변에서 시스템 태그를 떼어 낸다.
export function splitTags(raw = "") {
  const memories = [...raw.matchAll(MEMORY_TAG)].map((m) => m[1].trim()).slice(0, 1);
  const hooks = [...raw.matchAll(HOOK_TAG)].map((m) => m[1].trim());
  const text = raw.replace(MEMORY_TAG, "").replace(HOOK_TAG, "").replace(/\n{3,}/g, "\n\n").trim();
  return { text, memory: memories[0] || "", hook: hooks[0] || "" };
}

// 기억 메모에 개인정보로 보이는 것이 섞이면 버린다.
const PII = [/\d{2,3}-?\d{3,4}-?\d{4}/, /@[\w.-]+\.\w+/, /\d{6}-?\d{7}/, /(로|길)\s*\d+/];
export function cleanMemory(m = "") {
  if (!m || m.length > 80) return "";
  return PII.some((re) => re.test(m)) ? "" : m;
}
