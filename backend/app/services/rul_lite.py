"""
RUL-lite 엔진: 간단한 캘리브레이션 임계치 기반 RUL% 추정기

- 히스테리시스: on_k/off_k 카운트로 알람 토글
- 감가: 알람 상태에서 보수적으로 rul_units 감소
- 회복: 안정 상태 지속 시 완만한 회복, 상한(cap) 적용

환경변수:
  - RUL_CALIB_PATH: 캘리브레이션 JSON 경로 (기본값 "configs/rul_calib.json")

캘리브레이션 파일 스키마(예):
{
  "EQ001::ON": {"cur_mag_thr": 1.2, "vibe_thr": 0.05},
  "EQ001::OFF": {"cur_mag_thr": 0.6}
}
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


DEFAULTS: Dict[str, object] = dict(
    margin=0.005,
    on_k=2,
    off_k=3,
    decay_gain=1.0,
    recovery_wait=60,
    recovery_gain=0.1,
    recovery_cap="last_alarm",  # "100" | "last_alarm"
    max_rul_units=20000.0,
    severity_divisor=0.20,  # (ratio-1.0)/divisor → 1.0에서 0~1로 정규화 (완만한 감소)
)


@dataclass
class _Hys:
    on_k: int
    off_k: int
    c: int = 0
    state: bool = False

    def step(self, high: bool) -> bool:
        if not self.state and high:
            self.c += 1
            if self.c >= self.on_k:
                self.state, self.c = True, 0
        elif self.state and not high:
            self.c += 1
            if self.c >= self.off_k:
                self.state, self.c = False, 0
        else:
            self.c = 0
        return self.state


@dataclass
class RULState:
    max_units: float
    cfg: Dict
    rul_units: float = None
    hys: _Hys = None
    calm: int = 0
    rec_cap: float = None
    last_update: float = field(default_factory=time.time)

    def __post_init__(self):
        self.rul_units = float(self.max_units)
        self.hys = _Hys(int(self.cfg["on_k"]), int(self.cfg["off_k"]))
        self.rec_cap = float(self.max_units)

    def update_by_ratio(self, ratio: float) -> Dict:
        alarm = self.hys.step(ratio > (1.0 + float(self.cfg["margin"])) )
        decay = 0.0
        rec = 0.0
        if alarm:
            div = float(self.cfg.get("severity_divisor", 0.20)) or 0.20
            sev = max(0.0, min(1.0, (ratio - 1.0) / div))
            decay = float(self.cfg["decay_gain"]) * sev
            self.rul_units = max(0.0, self.rul_units - decay)
            if self.cfg.get("recovery_cap") == "last_alarm":
                self.rec_cap = min(self.rec_cap, self.rul_units)
            self.calm = 0
        else:
            self.calm += 1
            if self.calm >= int(self.cfg["recovery_wait"]):
                cap = self.max_units if self.cfg.get("recovery_cap") == "100" else self.rec_cap
                rec = float(self.cfg["recovery_gain"])
                self.rul_units = min(cap, self.rul_units + rec)
        pct = 100.0 * self.rul_units / self.max_units
        return {
            "alarm": int(alarm),
            "ratio": ratio,
            "rul_pct": float(max(0.0, min(100.0, pct))),
            "step_decay": decay,
            "step_recover": rec,
        }


class RULLiteEngine:
    def __init__(self, calib: Dict, cfg: Optional[Dict] = None):
        self.calib = calib or {}
        self.cfg = {**DEFAULTS, **(cfg or {})}
        self.states: Dict[str, RULState] = {}

    def _state(self, key: str) -> RULState:
        if key not in self.states:
            self.states[key] = RULState(float(self.cfg["max_rul_units"]), self.cfg)
        return self.states[key]

    def step(self, equipment_id: str, power: str, x: float, y: float, z: float, vibe: float) -> Dict:
        key = f"{equipment_id}::{power}"
        cal = self.calib.get(key, {})
        cur_mag = math.sqrt(x * x + y * y + z * z)

        ratios = []
        if cal.get("cur_mag_thr", 0) > 0:
            ratios.append(cur_mag / float(cal["cur_mag_thr"]))
        if cal.get("vibe_thr", 0) > 0:
            ratios.append(vibe / float(cal["vibe_thr"]))

        ratio = max(ratios) if ratios else 0.5
        st = self._state(key)
        out = st.update_by_ratio(ratio)
        return {"equipment_id": equipment_id, "power": power, **out}

    def status(self, equipment_id: str, power: str) -> Dict:
        key = f"{equipment_id}::{power}"
        st = self._state(key)
        pct = 100.0 * st.rul_units / st.max_units
        return {
            "equipment_id": equipment_id,
            "power": power,
            "rul_pct": float(max(0.0, min(100.0, pct))),
        }


def _safe_load_json(path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


_ENGINE: Optional[RULLiteEngine] = None


def get_engine() -> RULLiteEngine:
    global _ENGINE
    if _ENGINE is None:
        calib_path = os.getenv("RUL_CALIB_PATH", "configs/rul_calib.json")
        calib = _safe_load_json(calib_path)
        # 환경변수 기반 튜닝 값 적용
        cfg_env: Dict[str, object] = {}
        def _maybe_set_float(k: str, env: str):
            v = os.getenv(env)
            if v is not None:
                try:
                    cfg_env[k] = float(v)
                except Exception:
                    pass
        def _maybe_set_int(k: str, env: str):
            v = os.getenv(env)
            if v is not None:
                try:
                    cfg_env[k] = int(v)
                except Exception:
                    pass
        # 개별 매핑
        _maybe_set_float("margin", "RUL_MARGIN")
        _maybe_set_int("on_k", "RUL_ON_K")
        _maybe_set_int("off_k", "RUL_OFF_K")
        _maybe_set_float("decay_gain", "RUL_DECAY_GAIN")
        _maybe_set_int("recovery_wait", "RUL_RECOVERY_WAIT")
        _maybe_set_float("recovery_gain", "RUL_RECOVERY_GAIN")
        cap = os.getenv("RUL_RECOVERY_CAP")
        if cap is not None:
            cfg_env["recovery_cap"] = cap
        _maybe_set_float("max_rul_units", "RUL_MAX_UNITS")
        _maybe_set_float("severity_divisor", "RUL_SEVERITY_DIVISOR")

        _ENGINE = RULLiteEngine(calib, cfg_env)
    return _ENGINE


