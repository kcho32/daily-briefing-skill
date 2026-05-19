#!/usr/bin/env python3
"""Daily briefing 출력 검증 Stop hook.

매일 brief 작성이 끝나면 자동 실행되어 다음을 검증:
1. 텔레그램 발송 (notifier_mcp.send_briefing) 이 호출됐는지
2. GitHub 백업 (notifier_mcp.backup_to_github) 이 호출됐는지
3. 텔레그램 본문에 필수 섹션 키워드가 포함됐는지
4. 단위 표기 오류 (원/만원 자릿수) 가 없는지

검증 실패 시 stderr 로 사유를 보고하고 exit 1 — Claude Code 가 AI 에게 재작성 유도.
경고만 줄 사안은 stderr 로 메시지만 출력하고 exit 0.

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

# 텔레그램 본문에 *최소한* 들어가야 할 섹션 키워드.
REQUIRED_SECTIONS = [
    "거시",          # 시장·거시 환경
    "포트폴리오",    # 보유 현황
    "오늘의 액션",   # 모드별 액션
    "신규 매수 후보",  # 후보 발굴
    "매수 전 확인사항",  # 체크리스트
]

# 회고 트리거일에 추가로 들어가야 할 키워드.
# 한국 시간 기준 요일 확인 (날짜 컨텍스트는 transcript 에서 가져옴).
RETRO_KEYWORD = "회고"


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
    """가장 최근 send_briefing 호출의 summary_text 인자를 추출.

    완벽한 파서는 아님 — 단순 substring 추출로 검증용 텍스트 확보.
    실패 시 빈 문자열 반환.
    """
    # send_briefing 호출 근처의 summary_text 인자 추출 시도
    pattern = r'"summary_text"\s*:\s*"((?:[^"\\]|\\.)*)"'
    matches = re.findall(pattern, transcript)
    if not matches:
        return ""
    # 가장 마지막 호출 사용 (한 세션에 여러 번 호출됐을 경우 대비)
    return matches[-1].replace("\\n", "\n").replace('\\"', '"')


def check_required_sections(text: str) -> list[str]:
    """필수 섹션 키워드 누락된 것 반환."""
    return [section for section in REQUIRED_SECTIONS if section not in text]


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

    # 1. send_briefing 호출 확인
    if not find_tool_call(transcript, "send_briefing"):
        errors.append(
            "notifier_mcp.send_briefing() 호출이 없음 — 텔레그램·대시보드 미발송"
        )

    # 2. backup_to_github 호출 확인 (경고 — reject 까지는 X)
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
        unit_warnings = check_unit_sanity(telegram_text)
        warnings.extend(unit_warnings)
    elif find_tool_call(transcript, "send_briefing"):
        # send_briefing 은 호출됐는데 텍스트 추출 실패 — 파서 한계, 경고만.
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
