#!/usr/bin/env python3
"""건강 체크 + 음성 AI + 응급 연락 로봇 진입점.

사용 예:
  python main.py
  python main.py --scenario fall --voice-mock ok
  python main.py --scenario fall --voice-mock help
  python main.py --scenario fall --stt mic
  python main.py --no-voice
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.health_analyzer import HealthAnalyzer
from emergency.contact import EmergencyContactService
from robot.agent import CareRobotAgent
from sensors.mock_sensor import MockHealthSensor
from voice.assistant import VoiceAI

logger = logging.getLogger(__name__)


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_voice(config: dict, args: argparse.Namespace) -> VoiceAI | None:
    if args.no_voice:
        return None

    voice_cfg = dict(config.get("voice", {}))
    if args.stt:
        voice_cfg["stt_mode"] = args.stt

    # CLI mock 응답 프리셋
    if args.voice_mock == "ok":
        voice_cfg["stt_mode"] = "mock"
        voice_cfg["mock_replies"] = ["괜찮아요"]
    elif args.voice_mock == "help":
        voice_cfg["stt_mode"] = "mock"
        voice_cfg["mock_replies"] = ["도와주세요"]
    elif args.voice_mock == "silence":
        voice_cfg["stt_mode"] = "mock"
        voice_cfg["mock_replies"] = []
    elif args.voice_mock == "status":
        voice_cfg["stt_mode"] = "mock"
        voice_cfg["mock_replies"] = ["지금 건강 상태 어때?"]

    return VoiceAI(voice_cfg)


def build_agent(config: dict, scenario: str, voice: VoiceAI | None) -> CareRobotAgent:
    mon = config["monitoring"]
    em = config["emergency"]
    robot_cfg = config.get("robot", {})
    voice_cfg = config.get("voice", {})

    sensor = MockHealthSensor(scenario=scenario)
    analyzer = HealthAnalyzer(
        thresholds=config["thresholds"],
        history_size=mon.get("history_size", 30),
    )
    emergency = EmergencyContactService(
        contacts=em["contacts"],
        message_template=em["message_template"],
        dry_run=em.get("dry_run", True),
    )
    return CareRobotAgent(
        sensor=sensor,
        analyzer=analyzer,
        emergency=emergency,
        interval_seconds=mon.get("interval_seconds", 2.0),
        confirm_timeout_seconds=em.get("confirm_timeout_seconds", 15.0),
        speak_alerts=robot_cfg.get("speak_alerts", True),
        robot_name=robot_cfg.get("name", "CareBot"),
        voice=voice,
        listen_between_steps=bool(voice_cfg.get("listen_between_steps", False)),
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="건강 로봇 AI (음성 지원)")
    p.add_argument(
        "--config",
        default=str(ROOT / "config" / "settings.json"),
        help="설정 파일 경로",
    )
    p.add_argument(
        "--scenario",
        default="random_emergency",
        choices=["normal", "tachycardia", "hypoxia", "fever", "fall", "random_emergency"],
        help="시뮬레이션 시나리오",
    )
    p.add_argument("--steps", type=int, default=15, help="실행 스텝 수 (0=무한)")
    p.add_argument("--no-voice", action="store_true", help="음성 AI 비활성화")
    p.add_argument(
        "--stt",
        choices=["auto", "mic", "mock"],
        default=None,
        help="음성 인식 모드",
    )
    p.add_argument(
        "--voice-mock",
        choices=["ok", "help", "silence", "status"],
        default=None,
        help="마이크 없이 음성 응답 시뮬레이션",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = load_config(Path(args.config))
    voice = build_voice(config, args)
    if voice is not None:
        logger.info("음성 AI 활성 (STT=%s)", voice.stt.mode)
    else:
        logger.info("음성 AI 비활성")

    agent = build_agent(config, args.scenario, voice)
    max_steps = None if args.steps == 0 else args.steps
    agent.run(max_steps=max_steps)


if __name__ == "__main__":
    main()
