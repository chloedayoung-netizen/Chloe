/**
 * 캐릭터챗 실험 로그 수집 + 요약 (Google Apps Script)
 * 1) 새 스프레드시트 → 확장 프로그램 → Apps Script → 이 파일 붙여넣기
 * 2) 프로젝트 설정 → 스크립트 속성에 SHEET_TOKEN 추가 (Worker의 SHEET_TOKEN과 같은 값)
 * 3) 배포 → 새 배포 → 웹 앱, 실행: 나, 액세스: 모든 사용자 → URL을 Worker의 SHEET_WEBHOOK_URL 로
 * 4) 시트 메뉴 '실험' → '요약 갱신' 을 누르면 summary 탭이 다시 계산된다.
 */
const HEAD = ['ts', 'uid', 'sid', 'type', 'char', 'src', 'variant', 'data'];

function doPost(e) {
  const body = JSON.parse(e.postData.contents || '{}');
  const token = PropertiesService.getScriptProperties().getProperty('SHEET_TOKEN');
  if (!token || body.token !== token) return ContentService.createTextOutput('denied');
  const sh = sheet_('events');
  if (sh.getLastRow() === 0) sh.appendRow(HEAD);
  sh.appendRow(HEAD.map((k) => body[k] || ''));
  return ContentService.createTextOutput('ok');
}

function onOpen() {
  SpreadsheetApp.getUi().createMenu('실험').addItem('요약 갱신', 'summarize').addToUi();
}

function sheet_(name) {
  const ss = SpreadsheetApp.getActive();
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

// 서울 기준 날짜
function day_(ts) {
  return Utilities.formatDate(new Date(ts), 'Asia/Seoul', 'yyyy-MM-dd');
}
function addDays_(d, n) {
  const x = new Date(d + 'T00:00:00+09:00');
  x.setDate(x.getDate() + n);
  return Utilities.formatDate(x, 'Asia/Seoul', 'yyyy-MM-dd');
}

function summarize() {
  const rows = sheet_('events').getDataRange().getValues().slice(1)
    .map((r) => ({ ts: r[0], uid: r[1], sid: r[2], type: r[3], char: r[4], src: r[5], variant: r[6], data: safe_(r[7]) }));
  const users = {};
  const chars = {};
  let costUsd = 0, costKnown = 0, replies = 0, safety = 0, errors = 0;
  const pay = { day: 0, month: 0, tomorrow: 0 }, paywallViews = new Set(), payUsers = new Set();
  const fb = { up: 0, down: 0 }, comments = [];

  rows.forEach((e) => {
    const u = users[e.uid] || (users[e.uid] = { src: e.src, days: new Set(), msgs: 0, started: false, firstDay: null });
    const d = day_(e.ts);
    if (e.type === 'user_msg') {
      u.msgs++; u.started = true; u.days.add(d);
      if (!u.firstDay || d < u.firstDay) u.firstDay = d;
      const c = chars[e.char] || (chars[e.char] = { users: new Set(), msgs: 0, sessions: new Set(), retUsers: new Set() });
      c.users.add(e.uid); c.msgs++; c.sessions.add(e.uid + d);
    }
    if (e.type === 'session_start' && e.data.dayIndex >= 2 && chars[e.char]) chars[e.char].retUsers.add(e.uid);
    if (e.type === 'ai_reply' || e.type === 'ai_goodbye') {
      replies++;
      if (typeof e.data.costUsd === 'number') { costUsd += e.data.costUsd; costKnown++; }
    }
    if (e.type === 'safety_crisis') safety++;
    if (e.type === 'error') errors++;
    if (e.type === 'paywall_view') paywallViews.add(e.uid);
    if (e.type === 'paywall_choice') { pay[e.data.choice] = (pay[e.data.choice] || 0) + 1; if (e.data.choice !== 'tomorrow') payUsers.add(e.uid); }
    if (e.type === 'feedback') { if (e.data.score) fb[e.data.score]++; if (e.data.text) comments.push([day_(e.ts), e.char, e.data.text]); }
  });

  const all = Object.keys(users).map((k) => users[k]);
  const visitors = all.length;
  const starters = all.filter((u) => u.started);
  const d1 = starters.filter((u) => u.days.has(addDays_(u.firstDay, 1))).length;
  const r7 = starters.filter((u) => [...u.days].some((d) => d > u.firstDay && d <= addDays_(u.firstDay, 7))).length;
  const pct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 + '%' : '-');
  const sessions = starters.reduce((n, u) => n + u.days.size, 0);

  const out = [
    ['지표', '값', '분모/메모'],
    ['방문자(uid)', visitors, ''],
    ['첫 메시지 보낸 사람', starters.length, pct(starters.length, visitors) + ' of 방문자'],
    ['다음 날 재방문(D1)', d1, pct(d1, starters.length) + ' of 시작한 사람'],
    ['7일 안 재방문', r7, pct(r7, starters.length) + ' of 시작한 사람'],
    ['사람-일 세션당 평균 메시지', sessions ? Math.round(starters.reduce((n, u) => n + u.msgs, 0) / sessions * 10) / 10 : '-', '세션 = 한 사람이 하루 동안'],
    ['무료 한도 도달(결제창 본 사람)', paywallViews.size, pct(paywallViews.size, starters.length) + ' of 시작한 사람'],
    ['결제 의향 선택(하루/월)', pay.day + ' / ' + pay.month, '사람 수 ' + payUsers.size + ' · 실제 결제 아님'],
    ['내일 올게요 선택', pay.tomorrow, ''],
    ['AI 응답 수', replies, ''],
    ['AI 비용 합계(USD)', Math.round(costUsd * 10000) / 10000, '비용 확인된 응답 ' + costKnown + '건'],
    ['사람-일 세션당 AI 비용(USD)', sessions ? Math.round(costUsd / sessions * 10000) / 10000 : '-', ''],
    ['위기 신호 안내', safety, '대화 원문은 저장 안 함'],
    ['오류', errors, ''],
    ['피드백 좋아요/별로', fb.up + ' / ' + fb.down, ''],
    [],
    ['캐릭터', '시작한 사람', '메시지', '세션', '이틀 이상 온 사람'],
  ];
  Object.keys(chars).forEach((k) => {
    const c = chars[k];
    out.push([k, c.users.size, c.msgs, c.sessions.size, c.retUsers.size]);
  });
  out.push([], ['유입 경로', '방문자', '시작한 사람', 'D1']);
  const bySrc = {};
  all.forEach((u) => {
    const s = bySrc[u.src] || (bySrc[u.src] = [0, 0, 0]);
    s[0]++; if (u.started) { s[1]++; if (u.days.has(addDays_(u.firstDay, 1))) s[2]++; }
  });
  Object.keys(bySrc).forEach((k) => out.push([k].concat(bySrc[k])));
  out.push([], ['날짜', '캐릭터', '자유 의견']);
  comments.forEach((c) => out.push(c));

  const sh = sheet_('summary');
  sh.clear();
  const width = Math.max.apply(null, out.map((r) => r.length || 1));
  sh.getRange(1, 1, out.length, width).setValues(out.map((r) => { const x = r.slice(); while (x.length < width) x.push(''); return x; }));
  sh.getRange(1, 1, 1, width).setFontWeight('bold');
  sh.getRange(out.length + 2, 1).setValue('갱신: ' + new Date());
}

function safe_(s) {
  try { return JSON.parse(s || '{}'); } catch (e) { return {}; }
}
