/* ---------- 콘텐츠 데이터: 여기만 고치면 섹션 내용이 바뀜 ---------- */
const PROGRAMS = [
  { name: 'Global', color: 'var(--key-1)', tagline: '해외 시장에 도전하는 초기 소프트웨어 스타트업의 여정을 만나보세요.',
    teams: [
      ['오르빗', '김하늘', '여러 나라의 크리에이터와 브랜드를 연결하는 마케팅 플랫폼을 만듭니다.', 128],
      ['레저랩', '이도윤', '해외 중소기업의 반복적인 회계 업무를 자동화하는 AI 소프트웨어를 개발합니다.', 96],
      ['모션웍스', '박서준', 'AI 판단과 로봇 움직임을 잇는 피지컬 AI 인프라를 만듭니다.', 112],
      ['글로우', '최유나', '전 세계 소비자에게 K-뷰티 제품 정보와 구매 경로를 연결합니다.', 74],
    ] },
  { name: 'Climate Tech', color: 'var(--key-2)', tagline: '기후 위기를 기술로 풀어가는 스타트업의 해법을 만나보세요.',
    teams: [
      ['그린셀', '정민재', '폐배터리를 재사용해 소형 에너지 저장 장치를 만듭니다.', 88],
      ['에어루프', '한지우', '건물 공조 데이터로 탄소 배출을 줄이는 소프트웨어를 개발합니다.', 61],
      ['바이오팜', '오세린', '음식물 부산물로 친환경 사료 원료를 생산합니다.', 103],
      ['써큘러', '윤태오', '의류 재고를 수거해 재생 섬유로 되돌리는 순환 플랫폼입니다.', 57],
    ] },
  { name: 'Newcomer', color: 'var(--key-3)', tagline: '첫 창업에 나선 팀들이 증명해낸 가능성을 만나보세요.',
    teams: [
      ['스터디로그', '강다은', '학습 기록을 바탕으로 맞춤 복습 일정을 짜주는 앱입니다.', 92],
      ['펫노트', '서지호', '반려동물 건강 기록과 동물병원 예약을 한곳에서 관리합니다.', 69],
      ['로컬픽', '임하준', '동네 소상공인의 재고를 실시간으로 보여주는 지도 서비스입니다.', 81],
      ['핏메이트', '배수아', '운동 파트너를 연결하고 루틴을 함께 관리하는 커뮤니티입니다.', 44],
    ] },
  { name: 'Beginner', color: 'var(--key-4)', tagline: '아이디어를 처음 시장에 꺼내 든 예비 창업가를 만나보세요.',
    teams: [
      ['노크', '조은우', '1인 가구를 위한 안부 확인 알림 서비스를 준비하고 있습니다.', 38],
      ['메뉴판', '신예린', '외국인을 위한 메뉴 번역·알레르기 안내 서비스입니다.', 52],
      ['리폼', '문시우', '버려지는 가구를 수선해 다시 판매하는 업사이클링 브랜드입니다.', 29],
      ['캠퍼스잡', '홍채원', '대학생과 지역 기업을 잇는 단기 프로젝트 매칭 플랫폼입니다.', 47],
    ] },
];

const PERKS = [
  ['Cloudly', 'var(--key-1)', '팀의 문서와 업무를 하나로 연결하는\n협업 워크스페이스입니다.', '프로 플랜 6개월 무료 이용권\n(*당일 현장 체크인 시 제공)'],
  ['Brainy', 'var(--key-2)', '개발자를 위한 AI 코딩 어시스턴트입니다.', 'API 크레딧 $100\n(*선착순 500명)'],
  ['Stackly', 'var(--key-4)', '초기 스타트업을 위한 클라우드 인프라를 제공합니다.', '클라우드 크레딧 $1,000'],
  ['Learnly', 'var(--key-3)', '실무 중심 온라인 강의 플랫폼입니다.', '전체 강의 30% 할인 쿠폰'],
  ['Notebox', 'var(--key-1)', '회의를 자동으로 기록하고 요약하는 AI 노트입니다.', '프로 플랜 3개월 무료'],
  ['Pixelo', 'var(--key-4)', '누구나 쉽게 쓰는 AI 이미지·영상 생성 도구입니다.', '크리에이터 플랜 2개월 무료'],
  ['Mediaon', 'var(--key-2)', '창업가 인터뷰와 인사이트를 다루는 미디어입니다.', '프리미엄 멤버십 1개월'],
  ['Goodsy', 'var(--key-3)', '넥스트 스테이지 X Goodsy 한정판 굿즈', '에코백·노트 세트\n(*한정 수량 1,000개)'],
];

const FAQ = {
  '행사 안내': [
    ['넥스트 스테이지는 어떤 행사인가요?', '한 해 동안 육성 프로그램을 거친 스타트업 12팀이 성장의 결실을 선보이는 무대입니다.\n창업에 관심 있는 누구나 참가해 피칭과 키노트를 듣고 혜택을 받을 수 있습니다.'],
    ['언제, 어디서 열리나요?', '2026년 11월 20일 (금) 13시부터 서울 컨벤션홀에서 진행됩니다.'],
    ['온라인으로 생중계되나요?', '오프라인 행사이며, 하이라이트 영상은 행사 종료 후 공개됩니다.'],
  ],
  '참가신청': [
    ['참가 대상과 참가비가 궁금해요.', '누구나 참관할 수 있으며 무료입니다.'],
    ['응원하기 투표는 어떻게 반영되나요?', '응원 수는 인기상 선정의 참고 지표로 활용됩니다. 팀당 1회 응원할 수 있습니다.'],
  ],
  '현장안내': [
    ['참가자 혜택은 어떻게 받나요?', '당일 현장 QR 체크인을 완료한 분께 메일로 혜택 수령 방법을 안내해 드립니다.'],
    ['문의는 어디로 하면 되나요?', 'hello@example.com 으로 문의해 주세요.'],
  ],
};

const HERITAGE = [
  [2016, '첫 번째 데모데이, 8개 팀으로 시작한 무대'],
  [2017, '멘토 30인과 함께한 1박 2일 부트캠프'],
  [2018, '지역 설명회를 시작해 전국으로 넓힌 해'],
  [2019, '졸업팀 중 첫 시리즈 B 투자 유치'],
  [2020, '처음 시도한 온라인 데모데이 중계'],
  [2021, '클라이밋 테크 트랙 신설'],
  [2022, '누적 참가자 1만 명 돌파'],
  [2023, '글로벌 트랙과 해외 파트너 프로그램 시작'],
  [2024, '졸업팀이 멘토로 돌아온 첫 해'],
  [2025, '10주년, 다시 처음의 마음으로'],
];
const KEYS = ['var(--key-1)', 'var(--key-4)', 'var(--key-2)', 'var(--key-3)'];

/* ---------- 유틸 ---------- */
const $ = (s, el = document) => el.querySelector(s);
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('is-on');
  clearTimeout(toast.t);
  toast.t = setTimeout(() => el.classList.remove('is-on'), 1800);
}

// 사진 대신 쓰는 추상 그래픽 (실제 이미지로 교체 시 background-image만 넣으면 됨)
function art(seed, color) {
  const r = (n) => ((Math.sin(seed * 9301 + n * 49297) + 1) / 2);
  const a = KEYS[(seed + 1) % 4], b = KEYS[(seed + 2) % 4];
  return `radial-gradient(circle at ${20 + r(1) * 60}% ${15 + r(2) * 40}%, ${a} 0 ${18 + r(3) * 14}%, transparent ${30 + r(3) * 14}%),
          radial-gradient(circle at ${r(4) * 100}% ${50 + r(5) * 40}%, ${b} 0 ${12 + r(6) * 10}%, transparent ${26 + r(6) * 10}%),
          ${color}`;
}

/* ---------- GNB ---------- */
const gnb = $('#gnb');
const burger = $('.gnb__burger');
burger.addEventListener('click', () => {
  const open = gnb.classList.toggle('is-open');
  burger.setAttribute('aria-expanded', open);
  burger.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
});
gnb.querySelectorAll('.gnb__nav a').forEach((a) => a.addEventListener('click', () => {
  gnb.classList.remove('is-open');
  burger.setAttribute('aria-expanded', 'false');
}));

/* ---------- Hero 캔버스: 키 컬러 블롭이 천천히 흐름 ---------- */
(function hero() {
  const canvas = $('.hero__canvas');
  const ctx = canvas.getContext('2d');
  const colors = ['#8278ff', '#78f0e6', '#ffe400', '#19e173'];
  const blobs = colors.map((c, i) => ({ c, phase: i * 1.7, speed: .00018 + i * .00004 }));
  let w, h;
  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function frame(t) {
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'multiply';
    const R = Math.max(w, h) * .38;
    blobs.forEach((b, i) => {
      const x = w * (.5 + .32 * Math.cos(t * b.speed + b.phase));
      const y = h * (.5 + .28 * Math.sin(t * b.speed * 1.3 + b.phase * 1.4));
      const g = ctx.createRadialGradient(x, y, 0, x, y, R);
      g.addColorStop(0, b.c + 'cc'); g.addColorStop(1, b.c + '00');
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    });
    if (!reduced) requestAnimationFrame(frame);
  }
  resize(); addEventListener('resize', resize);
  requestAnimationFrame(frame);
})();

/* ---------- 스크롤 연동: Floating CTA, GNB 배경, Film, Heritage ---------- */
const floating = $('#floating');
const filmSec = $('#film'), filmBox = $('#filmBox');
const herSec = $('#heritage');
herSec.style.setProperty('--steps', HERITAGE.length);

function progress(sec) {
  const r = sec.getBoundingClientRect();
  const total = r.height - innerHeight;
  return Math.min(1, Math.max(0, -r.top / total));
}
function onScroll() {
  const y = scrollY;
  gnb.classList.toggle('is-scrolled', y > 40);
  const nearEnd = y + innerHeight > document.documentElement.scrollHeight - 200;
  floating.classList.toggle('is-on', y > innerHeight * .6 && !nearEnd);
  filmBox.style.setProperty('--p', progress(filmSec).toFixed(4));
  setHeritage(Math.min(HERITAGE.length - 1, Math.floor(progress(herSec) * HERITAGE.length)));
}
addEventListener('scroll', onScroll, { passive: true });
addEventListener('resize', onScroll);

$('[data-share]').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(location.href); toast('링크를 복사했어요'); }
  catch { toast('링크 복사에 실패했어요'); }
});

/* ---------- About 아트 ---------- */
document.querySelectorAll('.about__art').forEach((el, i) => {
  el.style.background = art(i + 3, `var(--cardColor)`);
});

/* ---------- Programs ---------- */
const voted = new Set();
function renderProgram(idx) {
  const p = PROGRAMS[idx];
  $('#programTabs').querySelectorAll('.tab').forEach((t, i) => {
    t.setAttribute('aria-selected', i === idx);
    t.tabIndex = i === idx ? 0 : -1;
  });
  $('#programTagline').textContent = p.tagline;
  $('#teams').innerHTML = p.teams.map(([name, ceo, desc, votes], i) => {
    const key = `${idx}-${i}`, on = voted.has(key);
    return `<li class="team" style="--cardColor:${p.color}">
      <div class="team__art" style="background:${art(idx * 7 + i, p.color)}"></div>
      <div class="team__shade"></div>
      <div class="team__body">
        <span class="team__name">${esc(name)}</span>
        <span class="team__ceo">${esc(ceo)}</span>
        <span class="team__desc">${esc(desc)}</span>
        <button type="button" class="vote" data-key="${key}" data-votes="${votes}" aria-pressed="${on}" aria-label="${esc(name)} 응원하기">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6C6.2 8 6 8.5 6 9v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z"/></svg>
          <span>${votes + (on ? 1 : 0)}</span>
        </button>
      </div>
    </li>`;
  }).join('');
}
$('#programTabs').innerHTML = PROGRAMS.map((p) =>
  `<button role="tab" class="tab" style="--tabColor:${p.color};--tabText:var(--ink)">${esc(p.name)}</button>`).join('');
$('#programTabs').addEventListener('click', (e) => {
  const t = e.target.closest('.tab'); if (!t) return;
  renderProgram([...t.parentNode.children].indexOf(t));
});
$('#teams').addEventListener('click', (e) => {
  const b = e.target.closest('.vote'); if (!b) return;
  const key = b.dataset.key, on = !voted.has(key);
  on ? voted.add(key) : voted.delete(key);
  b.setAttribute('aria-pressed', on);
  b.querySelector('span').textContent = +b.dataset.votes + (on ? 1 : 0);
  b.classList.add('is-pop'); setTimeout(() => b.classList.remove('is-pop'), 180);
  if (on) toast('응원했어요!');
});
renderProgram(0);

/* ---------- Perks ---------- */
const panel = $('#perkPanel');
function renderPerk(idx) {
  const [brand, color, intro, reward] = PERKS[idx];
  $('#perkLogos').querySelectorAll('.perks__logo').forEach((b, i) => b.setAttribute('aria-pressed', i === idx));
  panel.style.setProperty('--c', color);
  panel.innerHTML = `<p class="perks__brand">${esc(brand)}</p>
    <p class="perks__intro pre">${esc(intro)}</p>
    <p class="perks__reward pre">${esc(reward)}</p>`;
  panel.classList.remove('is-swap'); void panel.offsetWidth; panel.classList.add('is-swap');
}
$('#perkLogos').innerHTML = PERKS.map(([brand, color]) =>
  `<li><button type="button" class="perks__logo" style="--c:${color}" aria-label="${esc(brand)} 혜택 보기"><i></i>${esc(brand)}</button></li>`).join('');
$('#perkLogos').addEventListener('click', (e) => {
  const b = e.target.closest('.perks__logo'); if (!b) return;
  renderPerk([...$('#perkLogos').querySelectorAll('.perks__logo')].indexOf(b));
});
renderPerk(0);

/* ---------- FAQ ---------- */
const faqCats = Object.keys(FAQ);
function renderFaq(idx) {
  $('#faqTabs').querySelectorAll('.tab').forEach((t, i) => t.setAttribute('aria-selected', i === idx));
  $('#faqList').innerHTML = FAQ[faqCats[idx]].map(([q, a]) => `<li class="faq__item">
    <button type="button" class="faq__q" aria-expanded="false"><span>${esc(q)}</span><span class="chev" aria-hidden="true"><i></i><i></i></span></button>
    <div class="faq__a-wrap"><div><p class="faq__a pre">${esc(a)}</p></div></div>
  </li>`).join('');
}
$('#faqTabs').innerHTML = faqCats.map((c) => `<button role="tab" class="tab">${esc(c)}</button>`).join('');
$('#faqTabs').addEventListener('click', (e) => {
  const t = e.target.closest('.tab'); if (!t) return;
  renderFaq([...t.parentNode.children].indexOf(t));
});
$('#faqList').addEventListener('click', (e) => {
  const q = e.target.closest('.faq__q'); if (!q) return;
  q.setAttribute('aria-expanded', q.getAttribute('aria-expanded') !== 'true');
});
renderFaq(0);

/* ---------- Quote: 화면에 들어오면 창이 열림 ---------- */
new IntersectionObserver((entries, io) => entries.forEach((en) => {
  if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
}), { threshold: .35 }).observe($('#quote'));

/* ---------- Heritage ---------- */
const stage = $('#hStage');
stage.innerHTML = HERITAGE.map((_, i) =>
  `<div class="heritage__slide" style="background:${art(i + 11, KEYS[i % 4])}"></div>`).join('');
let herIdx = -1;
function swapText(el, text) {
  el.textContent = text;
  el.style.animation = 'none'; void el.offsetWidth; el.style.animation = '';
}
function setHeritage(i) {
  if (i === herIdx) return;
  herIdx = i;
  stage.querySelectorAll('.heritage__slide').forEach((s, k) => {
    s.dataset.state = k < i ? 'past' : k === i ? 'current' : k === i + 1 ? 'next' : 'waiting';
  });
  swapText($('#hYear'), HERITAGE[i][0]);
  swapText($('#hRound'), `${i + 1}회`);
  swapText($('#hCaption'), HERITAGE[i][1]);
  $('#hBar').parentNode.style.setProperty('--prog', (i + 1) / HERITAGE.length);
}

onScroll();
