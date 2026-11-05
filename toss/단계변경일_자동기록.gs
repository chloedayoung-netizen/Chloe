/**
 * 리드 탭에서 담당자가 '단계'(K열)를 바꾸면
 * '단계 변경일'(L열)에 오늘 날짜를 자동으로 적습니다.
 * 담당자 입력은 단계·첫 연락일 2칸으로 유지하고, 주기·체류일 계산에 필요한 날짜는 시트가 남깁니다.
 *
 * 설치: 구글 시트로 xlsx를 연 뒤 확장 프로그램 → Apps Script → 이 코드를 붙여 넣고 저장.
 * 단순 트리거(onEdit)라 별도 권한 설정이 필요 없습니다.
 */
const SHEET_NAME = '리드';
const COL_STAGE = 11;        // K: 단계
const COL_STAGE_DATE = 12;   // L: 단계 변경일
const HEADER_ROWS = 1;

function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  if (sheet.getName() !== SHEET_NAME) return;

  const firstCol = range.getColumn();
  const lastCol = firstCol + range.getNumColumns() - 1;
  const touchesStage = firstCol <= COL_STAGE && COL_STAGE <= lastCol;
  if (!touchesStage) return;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  for (let r = range.getRow(); r < range.getRow() + range.getNumRows(); r++) {
    if (r <= HEADER_ROWS) continue;
    // 값이 비워진 경우(삭제)는 날짜를 남기지 않음
    if (sheet.getRange(r, COL_STAGE).getValue() === '') continue;
    sheet.getRange(r, COL_STAGE_DATE).setValue(today).setNumberFormat('yyyy-mm-dd');
  }
}
