#!/usr/bin/env python3
"""Daily briefing 출력 검증 Stop hook.

매일 brief 작성이 끝나면 자동 실행되어 다음을 검증:

ERRORS (exit 1 → AI 재작성 유도):
1. publish_dashboard + send_drafted_telegram 호출됐는지 (chunked draft flow)
2. 텔레그램 본문 필수 섹션 키워드 누락 여부

WARNINGS (exit 0 + stderr 메시지):
- backup_to_github 누락
- 단위 표기 오류 (원/만원 자릿수)
- 추천 0개 상황 일치 (텔레그램에 "권장 없음" 인데 대시보드 empty card 누락 의심)
- send_briefing 단일 호출 (구 flow — 새 chunked flow 권장)

원칙: AI 자율 판단을 약화시키지 않게 *형식 검증만*. narrative 품질 검증은 self-check 에 맡김.

입력: stdin 으로 hook payload (JSON) 를 받음. transcript_path 로 대화 이력 접근.
출력: stdout 은 사용 안 함. 검증 결과는 exit code + stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# Daily-briefing skill 의 트리거 키워드. 이 skill 호출이 아닌 일반 세션에서는 검증 스킵.
SKILL_NAME = "daily-briefing"

# 텔레그램 본문에 *최소한* 들어가야 할 섹션 keyword.
# 모든 모드 (안정/리마인드/액션/기회/위기) 에서 공통으로 포함되는 것만.
# 모드별로만 등장하는 섹션 (오늘의 액션 emoji 등) 은 강제 X — boilerplate 위험.
# 각 entry 는 alternatives — list 안 어느 하나라도 본문에 있으면 통과.
REQUIRED_SECTIONS: list[list[str]] = [
    ["💼", "포트폴리오"],  # part_id=3 포트폴리오 한 줄 — 모든 모드 필수
    ["💵", "현금"],         # part_id=8 현금 — 모든 모드 필수
]


def read_payload() -> dict:
    """Stop hook payload 를 stdin 에서 읽는다."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def read_transcript(transcript_path: str | None) -> str:
    """대화 transcript 전체를 문자열로 반환."""
    if not transcript_path:
        return ""
    try:
        return Path(transcript_path).read_text(encoding="utf-8", errors="replace")
    except (OSError, FileNotFoundError):
        return ""


def is_daily_briefing_session(transcript: str) -> bool:
    """이번 세션이 daily-briefing skill 호출인지 추정."""
    return SKILL_NAME in transcript or "포트폴리오 일일 브리핑" in transcript


def find_tool_call(transcript: str, tool_name: str) -> bool:
    """transcript 안에서 특정 도구 호출이 있었는지 확인."""
    # JSONL 형식 transcript 에서 tool_use 의 name 필드를 단순 substring 매칭.
    return f'"name":"{tool_name}"' in transcript or f'"name": "{tool_name}"' in transcript


def extract_telegram_text(transcript: str) -> str:
    """텔레그램 본문 추출.

    새 chunked flow (draft_telegram_section 누적 → send_drafted_telegram 발사) 우선.
    구 flow (send_briefing summary_text) 도 fallback 으로 지원.

    완벽한 파서 X — 단순 substring 추출로 검증용 텍스트 확보.
    실패 시 빈 문자열 반환.
    """
    # 새 flow: draft_telegram_section 의 text 인자 모두 모아서 합침
    draft_pattern = r'"name"\s*:\s*"draft_telegram_section"[^}]*?"text"\s*:\s*"((?:[^"\\]|\\.)*)"'
    drafts = re.findall(draft_pattern, transcript)
    if drafts:
        combined = "\n".join(d.replace("\\n", "\n").replace('\\"', '"') for d in drafts)
        return combined

    # 구 flow fallback: send_briefing summary_text
    pattern = r'"summary_text"\s*:\s*"((?:[^"\\]|\\.)*)"'
    matches = re.findall(pattern, transcript)
    if not matches:
        return ""
    return matches[-1].replace("\\n", "\n").replace('\\"', '"')


# 추천 0개 상황 텔레그램 패턴 (대시보드에 empty card 가 있어야 함)
EMPTY_RECOMMEND_PATTERNS = [
    "권장 없음",
    "현금 보유가 최선",
    "신규/추가 매수 권장 없음",
]


def check_empty_card_consistency(telegram_text: str, transcript: str) -> list[str]:
    """텔레그램에 '추천 0개' 신호가 있으면 대시보드에 empty state 카드도 있어야 함.

    dashboard-design.md § 0개 empty state 카드 - "카드 자체는 생략 X" 룰의 자동 검증.
    완벽 X — 대시보드 HTML 의 명확한 empty 신호 부재 시 경고.
    """
    warnings: list[str] = []
    has_empty_signal = any(p in telegram_text for p in EMPTY_RECOMMEND_PATTERNS)
    if not has_empty_signal:
        return warnings

    # publish_dashboard 호출의 html 인자에 empty 카드 신호 있는지 단순 substring 검색
    # (html 이 매우 길어서 정밀 parse 는 안 함 — substring 으로 충분)
    dashboard_html_match = re.search(
        r'"name"\s*:\s*"publish_dashboard"[^}]*?"html"\s*:\s*"((?:[^"\\]|\\.){0,200000})"',
        transcript,
    )
    if not dashboard_html_match:
        return warnings  # publish_dashboard 호출 없음 — 다른 check 에서 잡힘
    dashboard_html = dashboard_html_match.group(1)
    if not any(p in dashboard_html for p in EMPTY_RECOMMEND_PATTERNS):
        warnings.append(
            "텔레그램에 '추천 0개' 신호 있는데 대시보드 HTML 에 empty state 카드 신호 없음 "
            "— dashboard-design.md § '0개 empty state 카드' 룰 위반 의심 (카드 생략 금지)"
        )
    return warnings


def check_required_sections(text: str) -> list[str]:
    """필수 섹션 누락된 것 반환.

    각 REQUIRED_SECTIONS entry 는 alternatives — list 안 어느 하나라도 본문에
    있으면 통과. 모두 없으면 누락으로 보고 (첫 번째 keyword 로 표시).
    """
    return [alts[0] for alts in REQUIRED_SECTIONS if not any(a in text for a in alts)]


def check_unit_sanity(text: str) -> list[str]:
    """원/만원 단위 표기 오류 의심 사례 반환.

    매우 단순한 휴리스틱 — 정확하진 않지만 명백한 자릿수 오류는 잡힘.
    """
    warnings: list[str] = []
    # "X,XXX,XXX원" 표기에서 만원 단위 안 붙은 경우 — narrative 가독성 위해
    # (강제 reject 는 아님 — 정보 제공)
    raw_won = re.findall(r"(\d{1,3}(?:,\d{3}){2,})원(?![/-])", text)
    if raw_won:
        warnings.append(
            f"raw 원 단위 표기 발견: {raw_won[:3]} → 만원 단위 병기 권장"
        )
    return warnings


def main() -> int:
    payload = read_payload()
    transcript_path = payload.get("transcript_path") or payload.get("transcriptPath")
    transcript = read_transcript(transcript_path)

    if not transcript or not is_daily_briefing_session(transcript):
        # daily-briefing 세션이 아니면 아무것도 검증 안 함.
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    # 1. 발송 flow 확인: 새 chunked flow (publish_dashboard + send_drafted_telegram)
    #    또는 구 flow (send_briefing) 중 하나는 있어야 함
    has_new_flow = find_tool_call(transcript, "publish_dashboard") and find_tool_call(
        transcript, "send_drafted_telegram"
    )
    has_old_flow = find_tool_call(transcript, "send_briefing")
    if not has_new_flow and not has_old_flow:
        errors.append(
            "발송 호출 없음 — publish_dashboard + send_drafted_telegram (권장) "
            "또는 send_briefing (구 flow) 중 하나는 필수"
        )
    elif has_old_flow and not has_new_flow:
        warnings.append(
            "구 flow (send_briefing) 사용 — 새 chunked flow "
            "(draft_telegram_section + publish_dashboard + send_drafted_telegram) 권장"
        )

    # 2. backup_to_github 호출 확인 (경고)
    if not find_tool_call(transcript, "backup_to_github"):
        warnings.append(
            "notifier_mcp.backup_to_github() 호출 누락 — 대시보드 GitHub 백업 안 됨"
        )

    # 3. 텔레그램 본문 필수 섹션 검증
    telegram_text = extract_telegram_text(transcript)
    if telegram_text:
        missing = check_required_sections(telegram_text)
        if missing:
            errors.append(
                f"텔레그램 필수 섹션 누락: {', '.join(missing)}"
            )

        # 4. 단위 sanity (경고만)
        warnings.extend(check_unit_sanity(telegram_text))

        # 5. 추천 0개 일치 검증 (경고만 — dashboard 0개 카드 생략 위반 의심)
        warnings.extend(check_empty_card_consistency(telegram_text, transcript))
    elif has_new_flow or has_old_flow:
        warnings.append("텔레그램 본문 추출 실패 (검증 스킵)")

    # 결과 보고
    if errors:
        sys.stderr.write("⚠️ daily-briefing 검증 실패:\n")
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        if warnings:
            sys.stderr.write("\n경고:\n")
            for warn in warnings:
                sys.stderr.write(f"  - {warn}\n")
        return 1

    if warnings:
        sys.stderr.write("ℹ️ daily-briefing 경고:\n")
        for warn in warnings:
            sys.stderr.write(f"  - {warn}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
