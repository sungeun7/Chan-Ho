from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sensors.base import HealthReading


class AlertLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class HealthAlert:
    level: AlertLevel
    reasons: list[str] = field(default_factory=list)
    reading: HealthReading | None = None

    @property
    def needs_emergency(self) -> bool:
        return self.level == AlertLevel.CRITICAL

    def reason_text(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "이상 없음"


class HealthAnalyzer:
    """규칙 기반 건강 상태 분석기.

    나중에 ML 모델(이상 탐지)을 같은 analyze() 인터페이스로 교체/결합 가능.
    """

    def __init__(self, thresholds: dict[str, Any], history_size: int = 30) -> None:
        self.thresholds = thresholds
        self.history: deque[HealthReading] = deque(maxlen=history_size)

    def analyze(self, reading: HealthReading) -> HealthAlert:
        self.history.append(reading)
        reasons: list[str] = []
        level = AlertLevel.NORMAL

        hr = self.thresholds["heart_rate"]
        if reading.heart_rate < hr["low"]:
            reasons.append(f"심박 저하 ({reading.heart_rate:.0f}bpm)")
            level = AlertLevel.CRITICAL
        elif reading.heart_rate > hr["high"]:
            reasons.append(f"심박 상승 ({reading.heart_rate:.0f}bpm)")
            level = AlertLevel.CRITICAL

        if reading.spo2 < self.thresholds["spo2"]["low"]:
            reasons.append(f"산소포화도 저하 ({reading.spo2:.0f}%)")
            level = AlertLevel.CRITICAL

        temp = self.thresholds["temperature_c"]
        if reading.temperature_c < temp["low"]:
            reasons.append(f"저체온 ({reading.temperature_c:.1f}°C)")
            level = self._escalate(level, AlertLevel.WARNING)
        elif reading.temperature_c > temp["high"]:
            reasons.append(f"고열 ({reading.temperature_c:.1f}°C)")
            level = self._escalate(level, AlertLevel.WARNING)
            if reading.temperature_c >= temp["high"] + 0.5:
                level = AlertLevel.CRITICAL

        if reading.acceleration_g >= self.thresholds["fall_acceleration_g"]:
            reasons.append(f"낙상 의심 (가속도 {reading.acceleration_g:.1f}g)")
            level = AlertLevel.CRITICAL

        # 연속 WARNING이면 CRITICAL로 상향 (예: 고열이 여러 번)
        if level == AlertLevel.WARNING and self._persistent_warning(reasons):
            level = AlertLevel.CRITICAL
            reasons.append("이상 징후 지속")

        return HealthAlert(level=level, reasons=reasons, reading=reading)

    @staticmethod
    def _escalate(current: AlertLevel, candidate: AlertLevel) -> AlertLevel:
        order = [AlertLevel.NORMAL, AlertLevel.WARNING, AlertLevel.CRITICAL]
        return candidate if order.index(candidate) > order.index(current) else current

    def _persistent_warning(self, current_reasons: list[str]) -> bool:
        if len(self.history) < 5:
            return False
        recent = list(self.history)[-5:]
        # 최근 5회 모두 고열/저체온이면 지속으로 판단
        temp = self.thresholds["temperature_c"]
        feverish = sum(
            1
            for r in recent
            if r.temperature_c > temp["high"] or r.temperature_c < temp["low"]
        )
        return feverish >= 5 and any("열" in r or "체온" in r for r in current_reasons)
