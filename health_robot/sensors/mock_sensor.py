from __future__ import annotations

import random
import time

from .base import HealthReading, SensorInterface


class MockHealthSensor(SensorInterface):
    """개발/시뮬레이션용 가상 센서.

    scenario:
      - normal: 정상 범위
      - tachycardia: 심박 상승
      - hypoxia: 산소포화도 저하
      - fever: 고열
      - fall: 낙상 가속도
      - random_emergency: 간헐적 이상
    """

    def __init__(self, scenario: str = "normal") -> None:
        self.scenario = scenario
        self._tick = 0

    def read(self) -> HealthReading:
        self._tick += 1
        base = HealthReading(
            heart_rate=random.uniform(65, 85),
            spo2=random.uniform(96, 99),
            temperature_c=random.uniform(36.3, 36.9),
            acceleration_g=random.uniform(0.9, 1.2),
        )

        if self.scenario == "tachycardia":
            base.heart_rate = random.uniform(140, 165)
        elif self.scenario == "hypoxia":
            base.spo2 = random.uniform(82, 88)
        elif self.scenario == "fever":
            base.temperature_c = random.uniform(38.8, 39.5)
        elif self.scenario == "fall":
            base.acceleration_g = random.uniform(3.0, 5.0)
        elif self.scenario == "random_emergency":
            if self._tick % 12 == 0:
                choice = random.choice(["hr", "spo2", "temp", "fall"])
                if choice == "hr":
                    base.heart_rate = 150
                elif choice == "spo2":
                    base.spo2 = 85
                elif choice == "temp":
                    base.temperature_c = 39.2
                else:
                    base.acceleration_g = 3.5

        time.sleep(0.01)
        return base
