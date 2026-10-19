"""실제 로봇/라즈베리파이 이식 예시 (참고용, 기본 실행에는 미사용).

MAX30102(심박/SpO2) + MPU6050(가속도) 등을 SensorInterface로 감싸면
main.py의 MockHealthSensor만 교체하면 됩니다.
"""

from __future__ import annotations

from .base import HealthReading, SensorInterface


class HardwareHealthSensor(SensorInterface):
    def __init__(self) -> None:
        # TODO: I2C/시리얼 초기화
        # self.pulse_ox = Max30102(...)
        # self.imu = Mpu6050(...)
        # self.temp = MlX90614(...)
        raise NotImplementedError("실제 센서 드라이버를 연결하세요.")

    def read(self) -> HealthReading:
        # hr, spo2 = self.pulse_ox.read()
        # ax, ay, az = self.imu.acceleration
        # acc = (ax**2 + ay**2 + az**2) ** 0.5
        # temp = self.temp.read()
        # return HealthReading(hr, spo2, temp, acc)
        raise NotImplementedError

    def close(self) -> None:
        pass
