from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


class TextToSpeech:
    """텍스트 → 음성. pyttsx3 없으면 콘솔 폴백."""

    def __init__(self, enabled: bool = True, rate: int = 170, volume: float = 1.0) -> None:
        self.enabled = enabled
        self._engine = None
        self._lock = threading.Lock()

        if not enabled:
            return

        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", rate)
            self._engine.setProperty("volume", volume)
            self._prefer_korean_voice()
            logger.info("TTS 엔진 준비 완료 (pyttsx3)")
        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS 사용 불가, 콘솔 출력으로 대체: %s", exc)
            self._engine = None

    def _prefer_korean_voice(self) -> None:
        if self._engine is None:
            return
        try:
            for voice in self._engine.getProperty("voices"):
                name = (voice.name or "").lower()
                vid = (voice.id or "").lower()
                if "korean" in name or "ko-" in vid or "heami" in name or "ko_kr" in vid:
                    self._engine.setProperty("voice", voice.id)
                    logger.info("한국어 TTS 음성 선택: %s", voice.name)
                    return
        except Exception:  # noqa: BLE001
            pass

    def speak(self, text: str) -> None:
        if not self.enabled or not text:
            return
        logger.info("[TTS] %s", text)
        if self._engine is None:
            return
        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()
