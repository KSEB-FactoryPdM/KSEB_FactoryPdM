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
import re
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
from loguru import logger
from app.models.ae_defs import AE


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
        # 모델/스케일러는 지연 로딩으로 전환하여 불필요한 의존성 문제를 회피
        self.ae_current = None
        self.ae_vibration = None
        self.scaler_current = None
        self.scaler_vibration = None
        self.xgb_model = None
        # 입력 벡터 키 순서를 캐시 (modal_map 우선)
        self._order_keys: List[str] = []
        # XGB 메타
        self.xgb_feature_names: Optional[List[str]] = None
        self.xgb_num_features: Optional[int] = None

    def _ensure_current_loaded(self):
        if self.ae_current is None:
            self.ae_current = self._maybe_load_torch_model("ae_current.pt")
        if self.scaler_current is None:
            self.scaler_current = self._maybe_load_joblib("standard_scaler_current.joblib")

    def _ensure_vibration_loaded(self):
        if self.ae_vibration is None:
            self.ae_vibration = self._maybe_load_torch_model("ae_vibration.pt")
        if self.scaler_vibration is None:
            self.scaler_vibration = self._maybe_load_joblib("standard_scaler_vibration.joblib")

    def _ensure_xgb_loaded(self):
        if self.xgb_model is None:
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
            if not path.exists():
                logger.debug(f"AE 모델 파일 없음: {path}")
            return None
        try:
            # 1) TorchScript 로드 시도
            model = torch.jit.load(str(path), map_location="cpu")
            try:
                model.eval()
            except Exception:
                pass
            logger.info(f"AE 모델 로드 성공(TorchScript): {path}")
            return model
        except Exception as e_ts:
            # 2) 일반 PyTorch pickle 로드로 폴백
            try:
                obj = torch.load(str(path), map_location="cpu")
                # state_dict로 저장된 경우 AE 구조 재구성
                import collections
                if isinstance(obj, (collections.OrderedDict, dict)):
                    try:
                        # 입력 차원 및 기본 hidden/latent 설정
                        if "current" in filename:
                            input_dim = sum(1 for k in self.feature_spec.feature_keys if k.startswith("cur_"))
                            ae_key = "ae_current"
                            hidden_default = [128, 64]
                        else:
                            input_dim = sum(1 for k in self.feature_spec.feature_keys if k.startswith("vib_"))
                            ae_key = "ae_vibration"
                            hidden_default = [256, 128]

                        # metadata.json에서 하이퍼파라미터 추출 시도
                        cfg = {}
                        try:
                            meta_json = json.loads((self.bundle_dir / "metadata.json").read_text(encoding="utf-8"))
                            cfg = meta_json.get(ae_key, {}) or {}
                        except Exception:
                            cfg = {}

                        # 1) 메타데이터 우선
                        hidden = cfg.get("hidden", hidden_default)
                        if isinstance(hidden, str) and "," in hidden:
                            try:
                                hidden = [int(s.strip()) for s in hidden.split(",")]
                            except Exception:
                                hidden = hidden_default
                        elif isinstance(hidden, int):
                            hidden = [hidden]
                        elif not isinstance(hidden, list):
                            hidden = hidden_default
                        latent_dim = int(cfg.get("latent_dim", 16))

                        # 2) state_dict로부터 아키텍처 자동 추론 (메타가 없거나 불일치 시)
                        try:
                            enc_weight_keys = []
                            for k, v in state_dict.items():
                                m = re.match(r"^(enc|encoder|enc_mlp)\.(\d+)\.weight$", k)
                                if m:
                                    try:
                                        enc_weight_keys.append((int(m.group(2)), v))
                                    except Exception:
                                        continue
                            if enc_weight_keys:
                                enc_weight_keys.sort(key=lambda x: x[0])
                                shapes = [w.shape for _, w in enc_weight_keys]
                                # 첫 Linear: [h1, input_dim], 마지막 Linear: [latent_dim, hN]
                                inferred_input = int(shapes[0][1]) if len(shapes[0]) == 2 else None
                                inferred_hidden = [int(s[0]) for s in shapes[:-1] if len(s) == 2]
                                inferred_latent = int(shapes[-1][0]) if len(shapes[-1]) == 2 else None
                                # 입력 차원/latent가 유효하면 덮어쓰기
                                if inferred_input and inferred_latent and inferred_hidden:
                                    input_dim = inferred_input
                                    hidden = inferred_hidden
                                    latent_dim = inferred_latent
                                    logger.info(
                                        f"AE 아키텍처 자동 추론: input_dim={input_dim}, hidden={hidden}, latent={latent_dim}"
                                    )
                        except Exception as _e_arch:
                            logger.debug(f"AE 아키텍처 자동 추론 건너뜀: {_e_arch}")

                        model = AE(input_dim=input_dim, hidden=hidden, latent_dim=latent_dim)
                        state_dict = obj
                        # DataParallel 저장 대비 'module.' 접두 제거
                        if any(k.startswith("module.") for k in state_dict.keys()):
                            state_dict = {k.replace("module.", "", 1): v for k, v in state_dict.items()}
                        # 학습시 encoder/decoder 명명 → 런타임 enc/dec 명명 보정
                        # 일반적으로 Sequential 기반이면 다음 매핑으로 충분
                        #  - 'encoder.' → 'enc.'
                        #  - 'decoder.' → 'dec.'
                        #  - 과거 접두 'autoencoder.' 제거
                        def _remap_key(n: str) -> str:
                            n2 = n
                            if n2.startswith("autoencoder."):
                                n2 = n2.replace("autoencoder.", "", 1)
                            if n2.startswith("encoder."):
                                n2 = n2.replace("encoder.", "enc.", 1)
                            if n2.startswith("decoder."):
                                n2 = n2.replace("decoder.", "dec.", 1)
                            # 일부 구현에서 enc_mlp/dec_mlp 사용
                            if n2.startswith("enc_mlp."):
                                n2 = n2.replace("enc_mlp.", "enc.", 1)
                            if n2.startswith("dec_mlp."):
                                n2 = n2.replace("dec_mlp.", "dec.", 1)
                            return n2

                        if any(k.startswith("encoder.") or k.startswith("decoder.") or k.startswith("autoencoder.") or k.startswith("enc_mlp.") or k.startswith("dec_mlp.") for k in state_dict.keys()):
                            state_dict = { _remap_key(k): v for k, v in state_dict.items() }
                            logger.info("AE state_dict 키 접두사 보정 적용(encoder/decoder → enc/dec)")
                        missing, unexpected = model.load_state_dict(state_dict, strict=False)
                        if missing:
                            logger.warning(f"AE state_dict 로드: 누락 파라미터 {len(missing)}개")
                        if unexpected:
                            logger.warning(f"AE state_dict 로드: 예상치 못한 파라미터 {len(unexpected)}개")
                        try:
                            model.eval()
                        except Exception:
                            pass
                        logger.info(
                            f"AE 모델 재구성 및 state_dict 로드 성공: {path} (input_dim={input_dim}, hidden={hidden}, latent={latent_dim})"
                        )
                        return model
                    except Exception as e_recon:
                        logger.warning(f"AE state_dict 로드 실패(재구성 불가): {path} - {e_recon}")
                        return None

                # nn.Module로 저장된 경우 그대로 사용
                model = obj
                try:
                    model.eval()
                except Exception:
                    pass
                logger.info(f"AE 모델 로드 성공(torch.load 폴백): {path}")
                return model
            except Exception as e_pk:
                logger.warning(f"AE 모델 로드 실패: {path} - TorchScript: {e_ts} / torch.load: {e_pk}")
                return None

    def _maybe_load_joblib(self, filename: str):
        path = self.bundle_dir / filename
        if not path.exists() or joblib is None or np is None:
            return None
        try:
            return joblib.load(path)
        except Exception:
            class _IdentityScaler:
                def transform(self, X):
                    X = np.asarray(X, dtype=np.float32)
                    return np.clip(X, -1e6, 1e6)
            return _IdentityScaler()

    def _maybe_load_xgb_json(self, filename: str):
        path = self.bundle_dir / filename
        if not path.exists():
            logger.debug(f"XGB 모델 파일 없음: {path}")
            return None
        # 기본값: 환경변수로 활성화하지 않으면 XGBoost 비활성화
        if os.getenv("SERVE_ML_ENABLE_XGB", "false").lower() != "true":
            return None
        try:
            import xgboost as xgb
            booster = xgb.Booster()
            booster.load_model(str(path))
            logger.info(f"XGB 모델 로드 성공: {path}")
            # feature names/num_feature 파악
            try:
                names = booster.feature_names
            except Exception:
                names = None
            if names:
                self.xgb_feature_names = list(names)
                logger.debug(f"XGB feature_names 감지: {len(self.xgb_feature_names)}개")
            try:
                import json as _json
                cfg = _json.loads(booster.save_config())
                nfeat = cfg.get('learner', {}).get('learner_model_param', {}).get('num_feature')
                if nfeat is not None:
                    self.xgb_num_features = int(nfeat)
                    logger.debug(f"XGB num_feature 감지: {self.xgb_num_features}")
            except Exception:
                pass
            return booster
        except Exception as e:
            logger.warning(f"XGB 모델 로드 실패: {path} - {e}")
            return None

    def _extract_tensor_output(self, output):
        """모델 출력에서 텐서를 추출한다. (tuple/list/dict 대응)"""
        try:
            # list/tuple → 첫 요소 사용
            if isinstance(output, (list, tuple)) and len(output) > 0:
                output = output[0]
            # dict → 자주 쓰는 키 우선 사용, 없으면 첫 값
            elif isinstance(output, dict):
                for key in ("recon", "output", "x_hat", "decoded", "y"):
                    if key in output:
                        output = output[key]
                        break
                if isinstance(output, dict):
                    # 키를 못 찾았으면 첫 값
                    output = next(iter(output.values()))
            if not torch.is_tensor(output):
                output = torch.as_tensor(output)
            return output
        except Exception as e:
            logger.warning(f"모델 출력 텐서 변환 실패: {e}")
            return None

    def _compute_reconstruction_mse(self, t: torch.Tensor, recon_output) -> Optional[float]:
        """재구성 MSE를 안전하게 계산한다."""
        try:
            recon = self._extract_tensor_output(recon_output)
            if recon is None:
                return None
            # 배치 차원 정규화
            if recon.ndim == 1:
                recon = recon.unsqueeze(0)
            if t.shape != recon.shape:
                if recon.numel() == t.numel():
                    recon = recon.reshape_as(t)
                else:
                    logger.warning(f"AE 출력/입력 shape 불일치: input={tuple(t.shape)}, output={tuple(recon.shape)}")
                    return None
            mse = torch.mean((t - recon) ** 2).item()
            return float(mse)
        except Exception as e:
            logger.warning(f"재구성 MSE 계산 실패: {e}")
            return None

    def build_feature_vector(self, features: Dict[str, Any]) -> Tuple[Optional["np.ndarray"], Dict[str, float]]:
        ordered_list: List[float] = []
        used: Dict[str, float] = {}
        mapping = self.feature_spec.mapping or {}
        order_keys: List[str]
        # modal_map/mapping이 있으면 현재/진동 순서대로 결합
        if isinstance(mapping, dict) and (mapping.get("current") or mapping.get("vibration")):
            cur_keys = list(mapping.get("current", []) or [])
            vib_keys = list(mapping.get("vibration", []) or [])
            order_keys = cur_keys + vib_keys
        else:
            # feature_keys가 있으면 그대로 사용
            order_keys = list(self.feature_spec.feature_keys or [])
        # 마지막 방어: 그래도 비어있으면 입력 features 키의 정렬된 목록 사용
        if not order_keys:
            order_keys = sorted([k for k in features.keys()])
        # 벡터 생성
        for key in order_keys:
            try:
                value = float(features.get(key, 0.0))
            except Exception:
                value = 0.0
            ordered_list.append(value)
            used[key] = value
        # 순서 캐시
        self._order_keys = order_keys
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

        # 0) 시뮬/단순 매핑 등으로 생성된 "퇴화(degenerate)" 특성 감지 시 AE를 건너뛰고 간단 규칙 기반으로 판정
        #   - current 그룹에서 고유값 개수가 전체의 20% 미만 (예: cur_x_*가 전부 동일 x 값 등)
        #   - vibration 그룹에서 고유값 개수가 전체의 20% 미만 (예: vib_*가 전부 동일 vibe 값 등)
        try:
            mapping = self.feature_spec.mapping or {}
            order_keys = self._order_keys or list(used.keys())
            cur_names = list(mapping.get("current", []) or [k for k in order_keys if isinstance(k, str) and k.startswith("cur_")])
            vib_names = list(mapping.get("vibration", []) or [k for k in order_keys if isinstance(k, str) and k.startswith("vib_")])

            def _unique_ratio(names: List[str]) -> float:
                if not names:
                    return 1.0
                vals = [used.get(k) for k in names]
                # 부동소수 근사치로 고유값 집합 계산
                uniq = set()
                for v in vals:
                    try:
                        vv = float(v)
                    except Exception:
                        vv = 0.0
                    # 소수점 6자리 반올림으로 군집화
                    uniq.add(round(vv, 6))
                return float(len(uniq)) / float(len(vals)) if vals else 1.0

            cur_unique_ratio = _unique_ratio(cur_names)
            vib_unique_ratio = _unique_ratio(vib_names)
            is_degenerate = (cur_unique_ratio < 0.2) and (vib_unique_ratio < 0.2)
        except Exception:
            is_degenerate = False

        if is_degenerate:
            # 임계값 준비
            thresholds = self.metadata.thresholds or {}
            th_v = float(thresholds.get("vibration") or thresholds.get("th_ae", {}).get("vibration") or 0.0)
            th_c = float(thresholds.get("current") or thresholds.get("th_ae", {}).get("current") or 0.0)

            vib_rms = float(features.get("vib_rms", features.get("vib_mean", 0.0)))
            cur_rms_vals = [
                float(features.get(k, 0.0)) for k in ("cur_x_rms", "cur_y_rms", "cur_z_rms")
            ]
            cur_rms = float(np.mean([v for v in cur_rms_vals if v != 0.0])) if (np is not None and any(cur_rms_vals)) else (sum(cur_rms_vals) / max(1, sum(1 for v in cur_rms_vals if v != 0.0)) if any(cur_rms_vals) else 0.0)

            is_anom = (vib_rms > th_v) or (cur_rms > th_c)
            confs: List[float] = []
            if th_v > 0:
                confs.append(min(1.0, vib_rms / th_v))
            if th_c > 0:
                confs.append(min(1.0, cur_rms / th_c))
            confidence = float(np.mean(confs)) if (np is not None and confs) else (float(sum(confs) / len(confs)) if confs else 0.0)

            results: Dict[str, Any] = {
                "used_features": used,
                "scores": {
                    "current": cur_rms,
                    "vibration": vib_rms,
                    "xgb": None,
                },
                "thresholds": thresholds,
                "modalities": self.metadata.modalities,
                "case": self.metadata.case,
                "is_anomaly": bool(is_anom),
                "confidence": confidence,
            }
            return results

        if "current" in self.metadata.modalities:
            self._ensure_current_loaded()
        _use_current = "current" in self.metadata.modalities
        logger.debug(f"current 모달리티 사용 여부={_use_current}, 모델 로드={(self.ae_current is not None)}")
        if (
            np is not None
            and torch is not None
            and _use_current
            and self.ae_current is not None
            and vec is not None
        ):
            # modal_map 우선 마스크 구성
            mapping = self.feature_spec.mapping or {}
            order_keys = self._order_keys or list(used.keys())
            cur_names = list(mapping.get("current", []) or [])
            if not cur_names:
                # 접두사 기반 추정
                cur_names = [k for k in order_keys if isinstance(k, str) and k.startswith("cur_")]
            cur_set = set(cur_names)
            cur_mask = np.array([k in cur_set for k in order_keys])
            cur_vec = vec[cur_mask] if cur_mask.any() else np.array([], dtype=np.float32)
            if cur_vec.size > 0:
                try:
                    cur_vec = (
                        self.scaler_current.transform(cur_vec.reshape(1, -1))
                        if self.scaler_current
                        else np.clip(cur_vec, -1e6, 1e6)
                    ).reshape(-1)
                except Exception:
                    cur_vec = np.clip(cur_vec, -1e6, 1e6)
                with torch.no_grad():
                    try:
                        t = torch.from_numpy(cur_vec.astype(np.float32)).unsqueeze(0)
                        recon = self.ae_current(t)
                        current_score = self._compute_reconstruction_mse(t, recon)
                        logger.debug(f"current 스코어 계산 완료: {current_score}")
                    except Exception as e:
                        logger.warning(f"current AE 추론 실패: {e}")
                        current_score = None

        if "vibration" in self.metadata.modalities:
            self._ensure_vibration_loaded()
        _use_vibration = "vibration" in self.metadata.modalities
        logger.debug(f"vibration 모달리티 사용 여부={_use_vibration}, 모델 로드={(self.ae_vibration is not None)}")
        if (
            np is not None
            and torch is not None
            and _use_vibration
            and self.ae_vibration is not None
            and vec is not None
        ):
            mapping = self.feature_spec.mapping or {}
            order_keys = self._order_keys or list(used.keys())
            vib_names = list(mapping.get("vibration", []) or [])
            if not vib_names:
                vib_names = [k for k in order_keys if isinstance(k, str) and k.startswith("vib_")]
            vib_set = set(vib_names)
            vib_mask = np.array([k in vib_set for k in order_keys])
            vib_vec = vec[vib_mask] if vib_mask.any() else np.array([], dtype=np.float32)
            if vib_vec.size > 0:
                try:
                    vib_vec = (
                        self.scaler_vibration.transform(vib_vec.reshape(1, -1))
                        if self.scaler_vibration
                        else np.clip(vib_vec, -1e6, 1e6)
                    ).reshape(-1)
                except Exception:
                    vib_vec = np.clip(vib_vec, -1e6, 1e6)
                with torch.no_grad():
                    try:
                        t = torch.from_numpy(vib_vec.astype(np.float32)).unsqueeze(0)
                        recon = self.ae_vibration(t)
                        vibration_score = self._compute_reconstruction_mse(t, recon)
                        logger.debug(f"vibration 스코어 계산 완료: {vibration_score}")
                    except Exception as e:
                        logger.warning(f"vibration AE 추론 실패: {e}")
                        vibration_score = None

        # XGB 스코어 (case B 등)
        xgb_score: Optional[float] = None
        self._ensure_xgb_loaded()
        if self.xgb_model is not None and vec is not None:
            try:
                import xgboost as xgb
                xgb_input = vec
                expected = self.xgb_num_features
                # 현재 순서/이름들
                order_keys = self._order_keys or list(used.keys())
                mapping = self.feature_spec.mapping or {}
                cur_names = list(mapping.get("current", []) or [])
                vib_names = list(mapping.get("vibration", []) or [])
                if not cur_names:
                    cur_names = [k for k in order_keys if isinstance(k, str) and k.startswith("cur_")]
                if not vib_names:
                    vib_names = [k for k in order_keys if isinstance(k, str) and k.startswith("vib_")]

                # 1) feature_names가 있으면 그 순서대로 매핑
                if self.xgb_feature_names:
                    vals: List[float] = []
                    missing = 0
                    for fname in self.xgb_feature_names:
                        v = used.get(fname)
                        if v is None:
                            missing += 1
                            v = 0.0
                        vals.append(float(v))
                    if missing:
                        logger.warning(f"XGB feature_names 중 입력에 없는 키 {missing}개를 0으로 채움")
                    xgb_input = np.asarray(vals, dtype=np.float32)
                # 2) 기대 열 수가 있으면 휴리스틱 매핑
                elif expected is not None and expected != vec.size:
                    # 이름 기반 벡터 구성
                    name_to_val = used
                    cur_vec = np.asarray([float(name_to_val.get(n, 0.0)) for n in cur_names], dtype=np.float32) if cur_names else np.array([], dtype=np.float32)
                    vib_vec = np.asarray([float(name_to_val.get(n, 0.0)) for n in vib_names], dtype=np.float32) if vib_names else np.array([], dtype=np.float32)
                    if vib_vec.size == expected:
                        xgb_input = vib_vec
                        logger.debug("XGB 입력: vibration 벡터 사용")
                    elif cur_vec.size == expected:
                        xgb_input = cur_vec
                        logger.debug("XGB 입력: current 벡터 사용")
                    elif (cur_vec.size + vib_vec.size) == expected:
                        xgb_input = np.concatenate([cur_vec, vib_vec], axis=0)
                        logger.debug("XGB 입력: current+vibration 결합 사용")
                    else:
                        logger.warning(f"XGB 기대 특성수 {expected}와 입력 {vec.size} 불일치. 선두 {expected}개로 절삭")
                        xgb_input = vec[:expected]

                d = xgb.DMatrix(xgb_input.reshape(1, -1))
                xgb_score = float(self.xgb_model.predict(d)[0])
            except Exception as e:
                logger.warning(f"XGB 추론 실패: {e}")
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


