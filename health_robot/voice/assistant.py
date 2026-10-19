from __future__ import annotations

import logging
from typing import Any

from sensors.base import HealthReading

from .intent import VoiceIntent, classify_intent
from .stt import SpeechToText
from .tts import TextToSpeech

logger = logging.getLogger(__name__)


class VoiceAI:
    """말하기(TTS) + 듣기(STT) + 의도 분석 음성 AI."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self.enabled = cfg.get("enabled", True)
        self.tts = TextToSpeech(
            enabled=self.enabled and cfg.get("tts", True),
            rate=int(cfg.get("rate", 170)),
            volume=float(cfg.get("volume", 1.0)),
        )
        self.stt = SpeechToText(
            mode=cfg.get("stt_mode", "auto"),
            language=cfg.get("language", "ko-KR"),
            mock_replies=cfg.get("mock_replies", []),
        )
        self.listen_timeout = float(cfg.get("listen_timeout", 5.0))
        self.max_retries = int(cfg.get("max_retries", 2))

    def speak(self, text: str) -> None:
        self.tts.speak(text)

    def listen(self, timeout: float | None = None) -> str | None:
        return self.stt.listen(timeout=timeout or self.listen_timeout)

    def confirm_user_ok(self, timeout: float) -> bool:
        """응급 전 음성 확인. True=괜찮음, False=도움필요/무응답."""
        remaining = timeout
        attempts = max(1, self.max_retries)

        for i in range(attempts):
            slice_timeout = max(2.0, remaining / (attempts - i))
            text = self.listen(timeout=slice_timeout)
            intent = classify_intent(text)
            remaining = max(0.0, remaining - slice_timeout)

            if intent == VoiceIntent.OK:
                self.speak("네, 확인했습니다.")
                return True
            if intent == VoiceIntent.HELP:
                self.speak("도움이 필요하다고 이해했습니다.")
                return False
            if intent == VoiceIntent.SILENCE:
                if i < attempts - 1:
                    self.speak("들리시나요? 괜찮으시면 괜찮아요라고 말씀해 주세요.")
                continue
            if intent == VoiceIntent.UNKNOWN:
                self.speak("잘 이해하지 못했습니다. 괜찮아요, 또는 도와주세요라고 말씀해 주세요.")
            else:
                # status/stop 등은 응급 확인 맥락에서는 재질문
                self.speak("응급 확인 중입니다. 괜찮아요, 또는 도와주세요라고 말씀해 주세요.")

        self.speak("응답이 없어 응급 절차를 진행합니다.")
        return False

    def answer_status(self, reading: HealthReading | None) -> None:
        if reading is None:
            self.speak("아직 측정된 건강 데이터가 없습니다.")
            return
        self.speak(
            f"현재 심박수는 {reading.heart_rate:.0f}, "
            f"산소포화도는 {reading.spo2:.0f}퍼센트, "
            f"체온은 {reading.temperature_c:.1f}도입니다."
        )

    def handle_free_speech(self, reading: HealthReading | None = None) -> VoiceIntent:
        """상시 대화용: 한 번 듣고 의도 처리."""
        text = self.listen()
        intent = classify_intent(text)

        if intent == VoiceIntent.STATUS:
            self.answer_status(reading)
        elif intent == VoiceIntent.OK:
            self.speak("다행입니다. 계속 지켜볼게요.")
        elif intent == VoiceIntent.HELP:
            self.speak("괜찮지 않으시군요. 바로 도움을 요청하겠습니다.")
        elif intent == VoiceIntent.STOP:
            self.speak("모니터링을 곧 종료합니다.")
        elif intent == VoiceIntent.SILENCE:
            pass
        else:
            self.speak("상태 물어보기, 괜찮아요, 도와주세요 중 하나로 말씀해 주세요.")
        return intent
