"""
serve_ml 디렉토리의 모델 번들을 로드/선택/추론하기 위한 서비스

디렉토리 구조: serve_ml/<equipment_id>/<power>/<model_version>/
  - ae_current.pt (optional)
  - ae_vibration.pt (optional)
  - standard_scaler_current.joblib (optional)
  - standard_scaler_vibration.joblib (optional)
  - xgb.json (case A면 없음)
  - feature_spec.yaml
  - metadata.json  # case, thresholds, modalities, class_map, sha256...

FAQ 반영:
- 원시신호 입력도 가능하지만 초기엔 feature 입력 권장 (feature_spec.yaml 키 기준)
- power는 요청 지정이 가장 확실. 미지정 시 자동 버킷 선택 레이어 제공
- case A는 xgb.json 없음 → 게이트만 수행
- 싱글모달이면 thresholds 하나만 존재, modalities만 사용
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import joblib  # optional
except Exception:  # pragma: no cover
    joblib = None  # type: ignore
import os
try:
    import numpy as np  # optional
except Exception:  # pragma: no cover
    np = None  # type: ignore
import yaml

try:
    import torch  # optional
except Exception:  # pragma: no cover
    torch = None  # type: ignore
from sqlalchemy import text
import warnings

# NumPy ABI 호환 문제 회피용: serve_ml 추론 경로에서 NumPy 내부 모듈 에러 발생 시 안전하게 우회
try:
    import numpy as _np  # noqa: F401
except Exception:  # pragma: no cover
    warnings.warn("NumPy import failed in serve_ml context; certain model paths may be degraded.")


@dataclass
class FeatureSpec:
    feature_keys: List[str]
    mapping: Dict[str, str]


@dataclass
class ModelMetadata:
    case: str
    thresholds: Dict[str, float]
    modalities: List[str]
    class_map: Optional[Dict[str, int]] = None
    sha256: Optional[str] = None


class ServeMLBundle:
    def __init__(self, bundle_dir: Path):
        self.bundle_dir = bundle_dir
        self.metadata: ModelMetadata = self._load_metadata()
        self.feature_spec: FeatureSpec = self._load_feature_spec()
        self.ae_current = self._maybe_load_torch_model("ae_current.pt")
        self.ae_vibration = self._maybe_load_torch_model("ae_vibration.pt")
        self.scaler_current = self._maybe_load_joblib("standard_scaler_current.joblib")
        self.scaler_vibration = self._maybe_load_joblib("standard_scaler_vibration.joblib")
        self.xgb_model = self._maybe_load_xgb_json("xgb.json")

    def _load_metadata(self) -> ModelMetadata:
        meta_path = self.bundle_dir / "metadata.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        # thresholds 키가 th_ae, th_xgb 등 다양할 수 있어 통일
        thresholds = meta.get("thresholds") or meta.get("th_ae") or {}
        return ModelMetadata(
            case=meta.get("case", "A"),
            thresholds=thresholds,
            modalities=meta.get("modalities", []),
            class_map=meta.get("class_map"),
            sha256=(meta.get("sha256") or (meta.get("files_sha256") or {}).get("metadata.json")),
        )

    def _load_feature_spec(self) -> FeatureSpec:
        spec_path = self.bundle_dir / "feature_spec.yaml"
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        feature_keys = spec.get("feature_keys") or spec.get("features") or []
        mapping = spec.get("mapping") or spec.get("modal_map") or {}
        return FeatureSpec(feature_keys=feature_keys, mapping=mapping)

    def _maybe_load_torch_model(self, filename: str):
        path = self.bundle_dir / filename
        if not path.exists() or torch is None:
            return None
        try:
            return torch.jit.load(str(path), map_location="cpu")
        except Exception:
            return None

    def _maybe_load_joblib(self, filename: str):
        path = self.bundle_dir / filename
        if not path.exists() or joblib is None or np is None:
            return None
        try:
            return joblib.load(path)
        except Exception:
            return None

    def _maybe_load_xgb_json(self, filename: str):
        path = self.bundle_dir / filename
        if not path.exists():
            return None
        # 기본값: 환경변수로 활성화하지 않으면 XGBoost 비활성화
        if os.getenv("SERVE_ML_ENABLE_XGB", "false").lower() != "true":
            return None
        try:
            import xgboost as xgb
            booster = xgb.Booster()
            booster.load_model(str(path))
            return booster
        except Exception:
            return None

    def build_feature_vector(self, features: Dict[str, Any]) -> Tuple[Optional["np.ndarray"], Dict[str, float]]:
        ordered_list: List[float] = []
        used: Dict[str, float] = {}
        for key in self.feature_spec.feature_keys:
            mapped_key = key
            try:
                value = float(features.get(mapped_key, 0.0))
            except Exception:
                value = 0.0
            ordered_list.append(value)
            used[mapped_key] = value
        vec = None
        if np is not None:
            try:
                vec = np.array(ordered_list, dtype=np.float32)
            except Exception:
                vec = None
        return vec, used

    def infer(self, features: Dict[str, Any]) -> Dict[str, Any]:
        vec, used = self.build_feature_vector(features)

        # 모달리티 스코어
        current_score: Optional[float] = None
        vibration_score: Optional[float] = None

        if (
            np is not None
            and torch is not None
            and "current" in self.metadata.modalities
            and self.ae_current is not None
            and vec is not None
        ):
            cur_mask = np.array([k.startswith("cur_") for k in self.feature_spec.feature_keys])
            cur_vec = vec[cur_mask] if cur_mask.any() else vec
            if self.scaler_current is not None and cur_vec.size > 0:
                cur_vec = self.scaler_current.transform(cur_vec.reshape(1, -1)).reshape(-1)
            with torch.no_grad():
                try:
                    t = torch.from_numpy(cur_vec.astype(np.float32)).unsqueeze(0)
                    recon = self.ae_current(t)
                    mse = torch.mean((t - recon) ** 2).item()
                    current_score = float(mse)
                except Exception:
                    current_score = None

        if (
            np is not None
            and torch is not None
            and "vibration" in self.metadata.modalities
            and self.ae_vibration is not None
            and vec is not None
        ):
            vib_mask = np.array([k.startswith("vib_") for k in self.feature_spec.feature_keys])
            vib_vec = vec[vib_mask] if vib_mask.any() else vec
            if self.scaler_vibration is not None and vib_vec.size > 0:
                vib_vec = self.scaler_vibration.transform(vib_vec.reshape(1, -1)).reshape(-1)
            with torch.no_grad():
                try:
                    t = torch.from_numpy(vib_vec.astype(np.float32)).unsqueeze(0)
                    recon = self.ae_vibration(t)
                    mse = torch.mean((t - recon) ** 2).item()
                    vibration_score = float(mse)
                except Exception:
                    vibration_score = None

        # XGB 스코어 (case B 등)
        xgb_score: Optional[float] = None
        if self.xgb_model is not None and vec is not None:
            try:
                import xgboost as xgb
                d = xgb.DMatrix(vec.reshape(1, -1))
                xgb_score = float(self.xgb_model.predict(d)[0])
            except Exception:
                xgb_score = None

        # 임계값
        thresholds = self.metadata.thresholds or {}
        results: Dict[str, Any] = {
            "used_features": used,
            "scores": {
                "current": current_score,
                "vibration": vibration_score,
                "xgb": xgb_score,
            },
            "thresholds": thresholds,
            "modalities": self.metadata.modalities,
            "case": self.metadata.case,
        }

        is_anomaly = False
        confidences: List[float] = []

        if current_score is not None and ("current" in thresholds or "th_ae" in thresholds):
            th = thresholds.get("current") or thresholds.get("th_ae", {}).get("current") or 0.0
            is_anomaly = is_anomaly or (current_score > th)
            confidences.append(min(1.0, current_score / max(th, 1e-6)))

        if vibration_score is not None and ("vibration" in thresholds or "th_ae" in thresholds):
            th = thresholds.get("vibration") or thresholds.get("th_ae", {}).get("vibration") or 0.0
            is_anomaly = is_anomaly or (vibration_score > th)
            confidences.append(min(1.0, vibration_score / max(th, 1e-6)))

        if xgb_score is not None and ("xgb" in thresholds or "th_xgb" in thresholds):
            th = thresholds.get("xgb") or thresholds.get("th_xgb") or 0.5
            is_anomaly = is_anomaly or (xgb_score > th)
            confidences.append(min(1.0, xgb_score / max(th, 1e-6)))

        if np is not None:
            try:
                confidence = float(np.mean(confidences)) if confidences else 0.0
            except Exception:
                confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
        else:
            confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0
        results["is_anomaly"] = bool(is_anomaly)
        results["confidence"] = confidence

        # NumPy/torch 사용이 불가한 환경에서의 완전한 폴백: 간단 규칙 기반
        if (
            (self.ae_current is None and self.ae_vibration is None and self.xgb_model is None)
            or vec is None
        ):
            vib_rms = float(features.get("vib_rms", 0.0))
            cur_vals = [float(features.get(k, 0.0)) for k in ("cur_x_rms", "cur_y_rms", "cur_z_rms")]
            cur_rms = sum(cur_vals) / max(1, sum(1 for v in cur_vals if v != 0.0)) if any(cur_vals) else 0.0
            th_v = results["thresholds"].get("vibration", 0.0)
            th_c = results["thresholds"].get("current", 0.0)
            is_anom = (vib_rms > th_v) or (cur_rms > th_c)
            confs = []
            if th_v > 0:
                confs.append(min(1.0, vib_rms / th_v))
            if th_c > 0:
                confs.append(min(1.0, cur_rms / th_c))
            results["is_anomaly"] = bool(is_anom)
            results["confidence"] = float(sum(confs) / len(confs)) if confs else 0.0
            results["scores"]["current"] = cur_rms
            results["scores"]["vibration"] = vib_rms
            results["scores"]["xgb"] = None
        return results


class ServeMLRegistry:
    def __init__(self, root_dir: Optional[str] = None):
        root = root_dir or os.getenv("SERVE_ML_ROOT") or str(Path("backend/serve_ml").resolve())
        self.root = Path(root)

    def list_equipment(self) -> List[str]:
        if not self.root.exists():
            return []
        return [p.name for p in self.root.iterdir() if p.is_dir()]

    def list_powers(self, equipment_id: str) -> List[str]:
        eq_path = self.root / equipment_id
        if not eq_path.exists():
            return []
        return [p.name for p in eq_path.iterdir() if p.is_dir()]

    def list_versions(self, equipment_id: str, power: str) -> List[str]:
        base = self.root / equipment_id / power
        if not base.exists():
            return []
        return [p.name for p in base.iterdir() if p.is_dir()]

    def resolve_bundle(self, equipment_id: str, power: Optional[str], version: Optional[str]) -> ServeMLBundle:
        powers = self.list_powers(equipment_id)
        if not powers:
            raise FileNotFoundError(f"장비 {equipment_id} 에 대한 power 디렉토리가 없습니다")

        selected_power = power or sorted(powers)[0]
        versions = self.list_versions(equipment_id, selected_power)
        if not versions:
            raise FileNotFoundError(f"{equipment_id}/{selected_power} 에 버전이 없습니다")

        selected_version = version or sorted(versions)[-1]
        bundle_dir = self.root / equipment_id / selected_power / selected_version
        return ServeMLBundle(bundle_dir)

    def select_power_by_rule(self, equipment_id: str, features: Dict[str, Any]) -> Optional[str]:
        """
        RMS/속도 기준으로 가장 가까운 power 버킷 자동 선택.
        규칙:
          - vib_rms, cur_x_rms, cur_y_rms, cur_z_rms 중 존재하는 값을 사용해 스칼라 파워지표 계산
          - power 폴더명의 숫자(kW)를 추출하여 가장 가까운 값 선택
        """
        powers = self.list_powers(equipment_id)
        if not powers:
            return None
        # 파워 지표 계산
        vib_rms = float(features.get("vib_rms", 0.0))
        cur_rms_vals = [float(features.get(k, 0.0)) for k in ("cur_x_rms", "cur_y_rms", "cur_z_rms")]
        cur_rms = float(np.mean([v for v in cur_rms_vals if v != 0.0])) if any(cur_rms_vals) else 0.0
        power_metric = vib_rms * 10.0 + cur_rms * 1.0  # 간단한 휴리스틱

        def parse_kw(s: str) -> Optional[float]:
            try:
                t = s.lower().replace("kw", "").strip()
                return float(t)
            except Exception:
                return None

        candidates: List[Tuple[str, float]] = []
        for p in powers:
            kw = parse_kw(p)
            if kw is not None:
                candidates.append((p, abs(kw - power_metric)))
        if not candidates:
            return sorted(powers)[0]
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def sync_to_db(self) -> int:
        """serve_ml 디렉토리를 스캔하여 serve_ml_models 테이블과 동기화한다.
        Returns: upsert된 레코드 수
        """
        from app.core.database import get_timescale_engine
        engine = get_timescale_engine()
        upserts = 0
        with engine.connect() as conn:
            for equipment_id in self.list_equipment():
                for power in self.list_powers(equipment_id):
                    for version in self.list_versions(equipment_id, power):
                        bundle_dir = self.root / equipment_id / power / version
                        try:
                            bundle = ServeMLBundle(bundle_dir)
                            query = text(
                                """
                                INSERT INTO serve_ml_models (
                                    equipment_id, power, model_version,
                                    modalities, thresholds, class_map, sha256, bundle_path
                                ) VALUES (
                                    :equipment_id, :power, :model_version,
                                    CAST(:modalities AS JSONB), CAST(:thresholds AS JSONB), CAST(:class_map AS JSONB), :sha256, :bundle_path
                                )
                                ON CONFLICT (equipment_id, power, model_version) DO UPDATE SET
                                    modalities = EXCLUDED.modalities,
                                    thresholds = EXCLUDED.thresholds,
                                    class_map = EXCLUDED.class_map,
                                    sha256 = EXCLUDED.sha256,
                                    bundle_path = EXCLUDED.bundle_path,
                                    updated_at = NOW()
                                """
                            )
                            import json as _json
                            conn.execute(query, {
                                "equipment_id": equipment_id,
                                "power": power,
                                "model_version": version,
                                "modalities": bundle.metadata.modalities,
                                "thresholds": _json.dumps(bundle.metadata.thresholds),
                                "class_map": _json.dumps(bundle.metadata.class_map or {}),
                                "sha256": bundle.metadata.sha256,
                                "bundle_path": str(bundle_dir),
                            })
                            upserts += 1
                        except Exception:
                            # 개별 번들 오류는 건너뜀
                            continue
            conn.commit()
        return upserts


serve_ml_registry = ServeMLRegistry()


