from __future__ import annotations

from enum import Enum


class VoiceIntent(str, Enum):
    OK = "ok"                 # 괜찮다 / 네
    HELP = "help"             # 도움 요청 / 아니요
    STATUS = "status"         # 상태 물어보기
    STOP = "stop"             # 모니터링 중단
    UNKNOWN = "unknown"
    SILENCE = "silence"


# 간단 키워드 의도 분류 (오프라인, 의존성 없음)
_OK_KEYWORDS = (
    "괜찮", "괜찬", "네", "예", "응", "어", "좋아", "문제없", "정상",
    "yes", "ok", "okay", "fine", "i'm fine", "im fine",
)
_HELP_KEYWORDS = (
    "도와", "응급", "아파", "안 괜찮", "안괜찮", "아니", "싫어", "위험",
    "help", "emergency", "no", "hurt", "pain",
)
_STATUS_KEYWORDS = (
    "상태", "건강", "심박", "산소", "체온", "어때", "어떻게",
    "status", "health", "heart",
)
_STOP_KEYWORDS = (
    "멈춰", "중지", "종료", "그만", "stop", "quit", "exit",
)


def classify_intent(text: str | None) -> VoiceIntent:
    if text is None or not str(text).strip():
        return VoiceIntent.SILENCE

    t = text.strip().lower()

    # 부정+괜찮 패턴을 도움으로 우선 처리
    if any(k in t for k in ("안 괜찮", "안괜찮", "괜찮지 않", "괜찮지않")):
        return VoiceIntent.HELP
    if any(k in t for k in _HELP_KEYWORDS):
        return VoiceIntent.HELP
    if any(k in t for k in _OK_KEYWORDS):
        return VoiceIntent.OK
    if any(k in t for k in _STATUS_KEYWORDS):
        return VoiceIntent.STATUS
    if any(k in t for k in _STOP_KEYWORDS):
        return VoiceIntent.STOP
    return VoiceIntent.UNKNOWN
