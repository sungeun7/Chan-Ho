from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class SpeechToText:
    """마이크 → 텍스트.

    mode:
      - auto: speech_recognition 가능하면 마이크, 아니면 mock
      - mic: 실제 마이크 (Google Web Speech API, 인터넷 필요)
      - mock: 시뮬레이션 (미응답 / 스크립트 응답)
    """

    def __init__(
        self,
        mode: str = "auto",
        language: str = "ko-KR",
        mock_replies: list[str] | None = None,
    ) -> None:
        self.language = language
        self.mock_replies = list(mock_replies or [])
        self._mock_index = 0
        self._recognizer = None
        self._microphone = None

        if mode == "mock":
            self.mode = "mock"
            logger.info("STT: mock 모드")
            return

        try:
            import speech_recognition as sr

            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
            self.mode = "mic"
            logger.info("STT: 마이크 모드 준비 완료")
        except Exception as exc:  # noqa: BLE001
            if mode == "mic":
                logger.error("마이크 STT 초기화 실패: %s", exc)
            else:
                logger.warning("마이크 STT 불가 → mock으로 대체: %s", exc)
            self.mode = "mock"
            self._recognizer = None
            self._microphone = None

    def listen(self, timeout: float = 5.0, phrase_time_limit: float = 4.0) -> str | None:
        if self.mode == "mock":
            return self._listen_mock(timeout)
        return self._listen_mic(timeout, phrase_time_limit)

    def _listen_mock(self, timeout: float) -> str | None:
        if self._mock_index < len(self.mock_replies):
            text = self.mock_replies[self._mock_index]
            self._mock_index += 1
            time.sleep(min(0.3, timeout))
            logger.info("[STT-mock] 인식: %s", text)
            return text
        logger.info("[STT-mock] 응답 없음 (timeout=%.0fs)", timeout)
        time.sleep(min(0.5, timeout))
        return None

    def _listen_mic(self, timeout: float, phrase_time_limit: float) -> str | None:
        import speech_recognition as sr

        assert self._recognizer is not None and self._microphone is not None
        try:
            with self._microphone as source:
                logger.info("듣는 중... (최대 %.0fs)", timeout)
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            text = self._recognizer.recognize_google(audio, language=self.language)
            logger.info("[STT] 인식: %s", text)
            return text.strip()
        except sr.WaitTimeoutError:
            logger.info("[STT] 시간 초과 — 음성 없음")
            return None
        except sr.UnknownValueError:
            logger.info("[STT] 음성을 이해하지 못함")
            return None
        except sr.RequestError as exc:
            logger.error("[STT] 인식 서비스 오류: %s", exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.error("[STT] 예외: %s", exc)
            return None
