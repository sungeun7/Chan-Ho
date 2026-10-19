from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class HealthReading:
    """한 시점의 생체/동작 측정값."""

    heart_rate: float          # bpm
    spo2: float                # %
    temperature_c: float       # °C
    acceleration_g: float      # 낙상 감지용 가속도 크기
    timestamp: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SensorInterface(ABC):
    """실제 센서/웨어러블을 이 인터페이스로 교체하면 로봇에 이식 가능."""

    @abstractmethod
    def read(self) -> HealthReading:
        raise NotImplementedError

    def close(self) -> None:
        """하드웨어 리소스 정리 (선택)."""
