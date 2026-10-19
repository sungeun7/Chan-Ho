from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ai.health_analyzer import HealthAlert
from sensors.base import HealthReading

logger = logging.getLogger(__name__)


@dataclass
class Contact:
    name: str
    phone: str
    priority: int = 1


class EmergencyContactService:
    """응급 연락 서비스.

    dry_run=True: 실제 전송 없이 로그만 (기본, 개발용)
    Twilio 연동: send_sms() 내 twilio 주석 해제 후 환경변수 설정
      TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
    """

    def __init__(
        self,
        contacts: list[dict[str, Any]],
        message_template: str,
        dry_run: bool = True,
    ) -> None:
        self.contacts = sorted(
            [Contact(**c) for c in contacts],
            key=lambda x: x.priority,
        )
        self.message_template = message_template
        self.dry_run = dry_run
        self._last_alert_at: datetime | None = None
        self._cooldown_seconds = 60

    def build_message(self, alert: HealthAlert) -> str:
        reading = alert.reading or HealthReading(0, 0, 0, 0)
        return self.message_template.format(
            level=alert.level.value,
            reason=alert.reason_text(),
            heart_rate=f"{reading.heart_rate:.0f}",
            spo2=f"{reading.spo2:.0f}",
            temperature_c=f"{reading.temperature_c:.1f}",
            timestamp=reading.timestamp or datetime.now(timezone.utc).isoformat(),
        ).strip()

    def notify(self, alert: HealthAlert) -> list[str]:
        """우선순위 순으로 연락. 전송한 연락처 이름 목록 반환."""
        now = datetime.now(timezone.utc)
        if self._last_alert_at is not None:
            elapsed = (now - self._last_alert_at).total_seconds()
            if elapsed < self._cooldown_seconds:
                logger.info("응급 연락 쿨다운 중 (%.0fs 남음)", self._cooldown_seconds - elapsed)
                return []

        message = self.build_message(alert)
        sent: list[str] = []

        for contact in self.contacts:
            ok = self.send_sms(contact.phone, message)
            if ok:
                logger.warning("응급 연락 완료 → %s (%s)", contact.name, contact.phone)
                sent.append(contact.name)
            else:
                logger.error("응급 연락 실패 → %s (%s)", contact.name, contact.phone)

        if sent:
            self._last_alert_at = now
        return sent

    def send_sms(self, phone: str, message: str) -> bool:
        if self.dry_run:
            logger.warning("[DRY-RUN SMS] to=%s | %s", phone, message.replace("\n", " / "))
            return True

        # --- Twilio 실제 전송 예시 ---
        # import os
        # from twilio.rest import Client
        # client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
        # client.messages.create(
        #     body=message,
        #     from_=os.environ["TWILIO_FROM_NUMBER"],
        #     to=phone,
        # )
        # return True

        logger.error("dry_run=False인데 SMS 백엔드가 설정되지 않았습니다.")
        return False
