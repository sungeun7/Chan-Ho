from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Callable

from ai.health_analyzer import AlertLevel, HealthAnalyzer
from emergency.contact import EmergencyContactService
from sensors.base import HealthReading, SensorInterface

if TYPE_CHECKING:
    from voice.assistant import VoiceAI

logger = logging.getLogger(__name__)


class CareRobotAgent:
    """건강 모니터링 + 음성 AI + 응급 연락 로봇 에이전트."""

    def __init__(
        self,
        sensor: SensorInterface,
        analyzer: HealthAnalyzer,
        emergency: EmergencyContactService,
        interval_seconds: float = 2.0,
        confirm_timeout_seconds: float = 15.0,
        speak_alerts: bool = True,
        robot_name: str = "CareBot",
        voice: VoiceAI | None = None,
        on_speak: Callable[[str], None] | None = None,
        confirm_user_ok: Callable[[float], bool] | None = None,
        listen_between_steps: bool = False,
    ) -> None:
        self.sensor = sensor
        self.analyzer = analyzer
        self.emergency = emergency
        self.interval_seconds = interval_seconds
        self.confirm_timeout_seconds = confirm_timeout_seconds
        self.speak_alerts = speak_alerts
        self.robot_name = robot_name
        self.voice = voice
        self.listen_between_steps = listen_between_steps
        self._last_reading: HealthReading | None = None
        self._running = False

        if voice is not None:
            self.on_speak = on_speak or voice.speak
            self.confirm_user_ok = confirm_user_ok or voice.confirm_user_ok
        else:
            self.on_speak = on_speak or self._default_speak
            self.confirm_user_ok = confirm_user_ok or self._default_confirm

    def _default_speak(self, text: str) -> None:
        logger.info("[%s 음성] %s", self.robot_name, text)

    def _default_confirm(self, timeout: float) -> bool:
        logger.info("사용자 확인 대기 중... (%.0fs, 미응답 시 응급 연락)", timeout)
        time.sleep(min(timeout, 1.0))
        return False

    def speak(self, text: str) -> None:
        if self.speak_alerts:
            self.on_speak(text)

    def handle_alert(self, alert) -> None:
        if alert.level == AlertLevel.NORMAL:
            return

        msg = f"주의: {alert.reason_text()}"
        self.speak(msg)
        logger.warning("경보 [%s] %s", alert.level.value, alert.reason_text())

        if not alert.needs_emergency:
            return

        self.speak("괜찮으신가요? 괜찮아요, 또는 도와주세요라고 말씀해 주세요.")
        user_ok = self.confirm_user_ok(self.confirm_timeout_seconds)

        if user_ok:
            self.speak("확인되었습니다. 모니터링을 계속합니다.")
            logger.info("사용자가 정상 응답 → 응급 연락 취소")
            return

        self.speak("응급 연락을 시작합니다.")
        sent = self.emergency.notify(alert)
        if sent:
            self.speak(f"{', '.join(sent)}에게 알림을 보냈습니다.")

    def step(self) -> bool:
        """한 주기 실행. False면 루프 종료 요청."""
        reading = self.sensor.read()
        self._last_reading = reading
        alert = self.analyzer.analyze(reading)
        logger.info(
            "측정 HR=%.0f SpO2=%.0f Temp=%.1f Acc=%.1f → %s",
            reading.heart_rate,
            reading.spo2,
            reading.temperature_c,
            reading.acceleration_g,
            alert.level.value,
        )
        self.handle_alert(alert)

        if self.listen_between_steps and self.voice is not None and alert.level == AlertLevel.NORMAL:
            from voice.intent import VoiceIntent

            intent = self.voice.handle_free_speech(reading)
            if intent == VoiceIntent.HELP:
                self.speak("응급 연락을 시작합니다.")
                self.emergency.notify(alert)
            elif intent == VoiceIntent.STOP:
                return False
        return True

    def run(self, max_steps: int | None = None) -> None:
        self._running = True
        self.speak(f"{self.robot_name} 건강 모니터링을 시작합니다.")
        if self.voice is not None:
            self.speak("이상이 감지되면 음성으로 확인하겠습니다.")
        steps = 0
        try:
            while self._running:
                keep_going = self.step()
                steps += 1
                if not keep_going:
                    break
                if max_steps is not None and steps >= max_steps:
                    break
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            logger.info("사용자 중단")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        self.sensor.close()
        self.speak("모니터링을 종료합니다.")
