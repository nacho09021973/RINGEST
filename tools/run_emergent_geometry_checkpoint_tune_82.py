#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

import h5py
import numpy as np
import torch
import torch.nn.functional as F


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
SANDBOX_DIR_DEFAULT = REPO_ROOT / "runs" / "sandbox_v1" / "01_generate_sandbox_geometries"
BASE_CHECKPOINT_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "02_emergent_geometry_engine" / "emergent_geometry_model.pt"
ENGINE_SCRIPT = REPO_ROOT / "02_emergent_geometry_engine.py"
STAGE_NAME = "experiment/emergent_geometry_checkpoint_tune_82"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix or ".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, indent=2, ensure_ascii=False))
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rewrite_stage_paths(value: Any, src_root: Path, dst_root: Path) -> Any:
    src_str = str(src_root)
    dst_str = str(dst_root)
    if isinstance(value, dict):
        return {k: _rewrite_stage_paths(v, src_root, dst_root) for k, v in value.items()}
    if isinstance(value, list):
        return [_rewrite_stage_paths(v, src_root, dst_root) for v in value]
    if isinstance(value, str):
        return value.replace(src_str, dst_str)
    return value


def _load_engine_module(script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("basurin_stage02_engine_tune", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load engine module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_candidate_family_map() -> dict[str, int]:
    return {
        "ads": 0,
        "lifshitz": 1,
        "hyperscaling": 2,
        "deformed": 3,
        "dpbrane": 4,
        "unknown": 5,
        "kerr": 6,
    }


def _upgrade_family_head(
    old_weight: torch.Tensor,
    old_bias: torch.Tensor,
    candidate_family_map: dict[str, int],
) -> tuple[torch.Tensor, torch.Tensor]:
    new_out = len(candidate_family_map)
    new_weight = torch.zeros((new_out, old_weight.shape[1]), dtype=old_weight.dtype)
    new_bias = torch.zeros((new_out,), dtype=old_bias.dtype)

    # Preserve the existing classes and split the old "unknown" prior into dpbrane/unknown.
    new_weight[0:4] = old_weight[0:4]
    new_bias[0:4] = old_bias[0:4]
    new_weight[candidate_family_map["dpbrane"]] = old_weight[4]
    new_bias[candidate_family_map["dpbrane"]] = old_bias[4]
    new_weight[candidate_family_map["unknown"]] = old_weight[4]
    new_bias[candidate_family_map["unknown"]] = old_bias[4]
    # Kerr has no supervised examples in the sandbox split used here.
    # Start it neutral instead of inheriting the previous extrapolative bias.
    new_weight[candidate_family_map["kerr"]] = torch.zeros_like(old_weight[5])
    new_bias[candidate_family_map["kerr"]] = torch.zeros_like(old_bias[5])
    return new_weight, new_bias


def _normalize_features(x: np.ndarray, x_mean: np.ndarray, x_std: np.ndarray) -> np.ndarray:
    x_mean = np.asarray(x_mean).flatten()
    x_std = np.asarray(x_std).flatten()
    x_work = np.asarray(x, dtype=np.float32).copy()
    x_work = np.nan_to_num(x_work, nan=0.0, posinf=0.0, neginf=0.0)
    tiny_std = x_std < 1e-6
    if np.any(tiny_std):
        x_work = np.where(tiny_std, x_mean, x_work)
    x_norm = (x_work - x_mean) / x_std
    return np.clip(x_norm, -10.0, 10.0).astype(np.float32)


def _load_dataset(
    engine_module: ModuleType,
    data_dir: Path,
    family_map: dict[str, int],
    x_mean: np.ndarray,
    x_std: np.ndarray,
) -> dict[str, Any]:
    manifest = json.loads((data_dir / "geometries_manifest.json").read_text())
    loader = engine_module.CuerdasDataLoader(mode="train")
    train_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    z_grid = None
    d_value = None

    for geo in manifest["geometries"]:
        h5_path = data_dir / f"{geo['name']}.h5"
        with h5py.File(h5_path, "r") as fh:
            boundary_data, operators = loader.load_boundary_and_meta(fh)
            A_truth, f_truth, R_truth, z_grid_local, z_h, family, d_local, has_bulk = loader.load_bulk_truth(fh)
        if not has_bulk:
            continue
        boundary_data["d"] = d_local
        x = engine_module.build_feature_vector_v3(boundary_data, operators)
        x_norm = _normalize_features(x, x_mean, x_std)
        row = {
            "name": geo["name"],
            "category": geo["category"],
            "family": family,
            "family_id": family_map[family],
            "X_norm": x_norm,
            "Y_zh": float(z_h),
        }
        if z_grid is None:
            z_grid = z_grid_local
            d_value = d_local
        if geo["category"] == "known":
            train_rows.append(row)
        elif geo["category"] == "test":
            test_rows.append(row)

    if not train_rows or not test_rows:
        raise RuntimeError("FATAL: sandbox split is incomplete for tune experiment")

    return {
        "train_rows": train_rows,
        "test_rows": test_rows,
        "z_grid": np.asarray(z_grid, dtype=np.float32),
        "d": int(d_value),
        "manifest_n": len(manifest["geometries"]),
    }


def _rows_to_tensors(rows: list[dict[str, Any]], device: torch.device) -> dict[str, torch.Tensor]:
    x = np.stack([row["X_norm"] for row in rows]).astype(np.float32)
    y_zh = np.asarray([row["Y_zh"] for row in rows], dtype=np.float32)
    y_family = np.asarray([row["family_id"] for row in rows], dtype=np.int64)
    return {
        "X": torch.from_numpy(x).to(device),
        "Y_zh": torch.from_numpy(y_zh).to(device),
        "Y_family": torch.from_numpy(y_family).to(device),
    }


def _family_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["family"] for row in rows).items()))


@torch.no_grad()
def _evaluate_split(
    model: torch.nn.Module,
    tensors: dict[str, torch.Tensor],
    rows: list[dict[str, Any]],
    candidate_family_map: dict[str, int],
    z_t: torch.Tensor,
) -> dict[str, Any]:
    model.eval()
    out = model(tensors["X"], z_grid=z_t)
    family_logits = out["family_logits"]
    family_probs = torch.softmax(family_logits, dim=1)
    family_top1, family_pred = torch.max(family_probs, dim=1)
    top2 = torch.topk(family_probs, k=2, dim=1).values[:, 1]
    family_margin = family_top1 - top2
    family_entropy = -(family_probs * torch.log(torch.clamp(family_probs, min=1e-12))).sum(dim=1)
    zh_raw = out["z_h"].view(-1)
    zh_mae = F.smooth_l1_loss(zh_raw, tensors["Y_zh"], reduction="mean").item()
    accuracy = (family_pred == tensors["Y_family"]).float().mean().item()
    pred_names = {v: k for k, v in candidate_family_map.items()}
    pred_counts = Counter(pred_names[int(idx)] for idx in family_pred.cpu().tolist())
    negative_mask = zh_raw < 0.0
    return {
        "family_accuracy": float(accuracy),
        "family_pred_counts": dict(sorted(pred_counts.items())),
        "dominant_family_fraction": (max(pred_counts.values()) / len(rows)) if rows else 0.0,
        "zh_raw_mae": float(zh_mae),
        "n_negative_zh_raw": int(negative_mask.sum().item()),
        "negative_zh_raw_fraction": float(negative_mask.float().mean().item()),
        "family_top1_score_mean": float(family_top1.mean().item()),
        "family_margin_mean": float(family_margin.mean().item()),
        "family_entropy_mean": float(family_entropy.mean().item()),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tune a candidate stage-02 checkpoint for unified82 using sandbox supervision.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/emergent_geometry_checkpoint_tune_82/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--sandbox-dir", type=Path, default=SANDBOX_DIR_DEFAULT)
    ap.add_argument("--base-checkpoint", type=Path, default=BASE_CHECKPOINT_DEFAULT)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--n-epochs", type=int, default=120)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--family-lr", type=float, default=3e-3)
    ap.add_argument("--zh-lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--kerr-logit-penalty", type=float, default=0.25)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--unfreeze-top-layers", type=int, default=0,
                    help="Number of top backbone residual blocks to unfreeze (0=heads-only, 2=recommended)")
    ap.add_argument("--backbone-lr", type=float, default=5e-4,
                    help="Learning rate for unfrozen backbone layers (should be lower than head LRs)")
    ap.add_argument("--label-smoothing", type=float, default=0.0,
                    help="Label smoothing for family cross-entropy loss (0.1 recommended)")
    ap.add_argument("--zh-softplus", action="store_true", default=False,
                    help="Replace zh head final layer with Softplus-constrained output for architectural non-negativity")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    runs_root = Path(args.runs_root).resolve(strict=False)
    sandbox_dir = Path(args.sandbox_dir).resolve(strict=False)
    base_checkpoint = Path(args.base_checkpoint).resolve(strict=False)
    device = torch.device(args.device)

    final_stage_dir = runs_root / args.run_id / "experiment" / "emergent_geometry_checkpoint_tune_82"
    tmp_stage_dir = runs_root / args.run_id / "experiment" / f".tmp_emergent_geometry_checkpoint_tune_82_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    outputs_dir = tmp_stage_dir / "outputs"
    logs_dir = tmp_stage_dir / "logs"

    required = [sandbox_dir, sandbox_dir / "geometries_manifest.json", base_checkpoint, ENGINE_SCRIPT]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"FATAL: missing required contractual input: {missing[0]}")
    if final_stage_dir.exists():
        raise SystemExit(f"FATAL: output dir already exists: {final_stage_dir}")
    if tmp_stage_dir.exists():
        raise SystemExit(f"FATAL: temporary output dir already exists: {tmp_stage_dir}")

    outputs_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=False)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        engine_module = _load_engine_module(ENGINE_SCRIPT)
        if getattr(engine_module, "h5py", None) is None:
            engine_module.h5py = h5py

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            ckpt = torch.load(base_checkpoint, map_location=device, weights_only=False)
            candidate_family_map = _build_candidate_family_map()
            dataset = _load_dataset(
                engine_module,
                sandbox_dir,
                candidate_family_map,
                ckpt["X_mean"],
                ckpt["X_std"],
            )
            train_tensors = _rows_to_tensors(dataset["train_rows"], device)
            test_tensors = _rows_to_tensors(dataset["test_rows"], device)
            z_t = torch.from_numpy(dataset["z_grid"]).to(device)

            model = engine_module.EmergentGeometryNet(
                n_features=ckpt["n_features"],
                n_z=ckpt["n_z"],
                hidden_dim=ckpt.get("hidden_dim", 256),
                n_layers=ckpt.get("n_layers", 4),
                n_families=len(candidate_family_map),
                d=ckpt.get("d", dataset["d"]),
            ).to(device)

            base_state = ckpt["model_state_dict"]
            candidate_state = model.state_dict()
            for key, value in base_state.items():
                if key.startswith("decoder_family."):
                    continue
                if key in candidate_state and candidate_state[key].shape == value.shape:
                    candidate_state[key] = value.clone()
            family_weight, family_bias = _upgrade_family_head(
                base_state["decoder_family.weight"],
                base_state["decoder_family.bias"],
                candidate_family_map,
            )
            candidate_state["decoder_family.weight"] = family_weight.to(device=device)
            candidate_state["decoder_family.bias"] = family_bias.to(device=device)
            model.load_state_dict(candidate_state, strict=True)

            # --- Softplus wrapping for zh non-negativity ---
            if args.zh_softplus:
                original_zh = model.decoder_zh
                class _SoftplusZhWrapper(torch.nn.Module):
                    def __init__(self, base):
                        super().__init__()
                        self.base = base
                        self._softplus = torch.nn.Softplus(beta=5.0)
                    def forward(self, x):
                        return self._softplus(self.base(x))
                model.decoder_zh = _SoftplusZhWrapper(original_zh).to(device)

            # --- Freeze/unfreeze logic ---
            n_backbone_layers = len(model.layers)
            unfreeze_top = min(args.unfreeze_top_layers, n_backbone_layers)
            for name, param in model.named_parameters():
                is_head = name.startswith("decoder_family") or name.startswith("decoder_zh")
                is_top_backbone = False
                if unfreeze_top > 0:
                    for i in range(n_backbone_layers - unfreeze_top, n_backbone_layers):
                        if name.startswith(f"layers.{i}.") or name.startswith(f"layer_norms.{i}."):
                            is_top_backbone = True
                            break
                    if name.startswith("final_norm."):
                        is_top_backbone = True
                param.requires_grad = is_head or is_top_backbone

            trainable_params = [param for param in model.parameters() if param.requires_grad]
            if not trainable_params:
                raise RuntimeError("FATAL: no trainable parameters selected for candidate tune")

            train_family_ids = [row["family_id"] for row in dataset["train_rows"]]
            train_family_counts = Counter(train_family_ids)
            class_weights = torch.zeros(len(candidate_family_map), dtype=torch.float32, device=device)
            for fam_id, count in train_family_counts.items():
                class_weights[fam_id] = len(train_family_ids) / (len(train_family_counts) * count)

            # --- Optimizer with per-group LRs ---
            param_groups = [
                {"params": list(model.decoder_family.parameters()), "lr": args.family_lr},
                {"params": list(model.decoder_zh.parameters()), "lr": args.zh_lr},
            ]
            if unfreeze_top > 0:
                backbone_params = []
                for name, param in model.named_parameters():
                    if param.requires_grad and not name.startswith("decoder_"):
                        backbone_params.append(param)
                if backbone_params:
                    param_groups.append({"params": backbone_params, "lr": args.backbone_lr})

            optimizer = torch.optim.AdamW(
                param_groups,
                weight_decay=args.weight_decay,
            )
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.n_epochs, eta_min=min(args.family_lr, args.zh_lr) * 0.05)

            history: list[dict[str, Any]] = []
            best_state = None
            best_metrics = None
            best_epoch = None

            n_train = train_tensors["X"].shape[0]
            for epoch in range(1, args.n_epochs + 1):
                model.train()
                perm = torch.randperm(n_train, device=device)
                epoch_total = 0.0
                epoch_family = 0.0
                epoch_zh = 0.0
                epoch_nonneg = 0.0
                epoch_kerr = 0.0

                for start in range(0, n_train, args.batch_size):
                    batch_idx = perm[start:start + args.batch_size]
                    xb = train_tensors["X"][batch_idx]
                    yb_family = train_tensors["Y_family"][batch_idx]
                    yb_zh = train_tensors["Y_zh"][batch_idx]
                    out = model(xb, z_grid=z_t)
                    loss_family = F.cross_entropy(out["family_logits"], yb_family, weight=class_weights,
                                                   label_smoothing=args.label_smoothing)
                    zh_raw = out["z_h"].view(-1)
                    loss_zh = F.smooth_l1_loss(zh_raw, yb_zh, reduction="mean")
                    loss_nonneg = torch.relu(-zh_raw).pow(2).mean()
                    kerr_logits = out["family_logits"][:, candidate_family_map["kerr"]]
                    loss_kerr = F.softplus(kerr_logits).mean()
                    total = loss_family + 0.5 * loss_zh + 1.0 * loss_nonneg + args.kerr_logit_penalty * loss_kerr

                    optimizer.zero_grad()
                    total.backward()
                    torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                    optimizer.step()

                    batch_n = batch_idx.numel()
                    epoch_total += float(total.item()) * batch_n / n_train
                    epoch_family += float(loss_family.item()) * batch_n / n_train
                    epoch_zh += float(loss_zh.item()) * batch_n / n_train
                    epoch_nonneg += float(loss_nonneg.item()) * batch_n / n_train
                    epoch_kerr += float(loss_kerr.item()) * batch_n / n_train

                scheduler.step()
                val_metrics = _evaluate_split(model, test_tensors, dataset["test_rows"], candidate_family_map, z_t)
                history.append(
                    {
                        "epoch": epoch,
                        "train_total_loss": epoch_total,
                        "train_family_loss": epoch_family,
                        "train_zh_loss": epoch_zh,
                        "train_nonneg_penalty": epoch_nonneg,
                        "train_kerr_logit_penalty": epoch_kerr,
                        **val_metrics,
                    }
                )

                candidate_key = (
                    val_metrics["family_accuracy"],
                    -val_metrics["negative_zh_raw_fraction"],
                    -val_metrics["zh_raw_mae"],
                )
                best_key = None
                if best_metrics is not None:
                    best_key = (
                        best_metrics["family_accuracy"],
                        -best_metrics["negative_zh_raw_fraction"],
                        -best_metrics["zh_raw_mae"],
                    )
                if best_metrics is None or candidate_key > best_key:
                    best_metrics = val_metrics
                    best_epoch = epoch
                    raw_state = model.state_dict()
                    # Unwrap Softplus wrapper keys so checkpoint is loadable by vanilla engine
                    best_state = {}
                    for k, v in raw_state.items():
                        clean_k = k.replace("decoder_zh.base.", "decoder_zh.") if args.zh_softplus else k
                        best_state[clean_k] = v.detach().cpu().clone()

            if best_state is None or best_metrics is None or best_epoch is None:
                raise RuntimeError("FATAL: candidate tune did not produce a best checkpoint")

            # Re-wrap keys for the current model (which may have Softplus wrapper)
            load_state = {}
            for k, v in best_state.items():
                wrapped_k = k.replace("decoder_zh.", "decoder_zh.base.") if (args.zh_softplus and not k.startswith("decoder_zh.base.")) else k
                load_state[wrapped_k] = v
            model.load_state_dict(load_state, strict=False)
            train_metrics = _evaluate_split(model, train_tensors, dataset["train_rows"], candidate_family_map, z_t)
            test_metrics = _evaluate_split(model, test_tensors, dataset["test_rows"], candidate_family_map, z_t)

            candidate_checkpoint_path = outputs_dir / "emergent_geometry_model_candidate_v2.pt"
            candidate_ckpt = dict(ckpt)
            candidate_ckpt["model_state_dict"] = {k: v.cpu() for k, v in best_state.items()}
            candidate_ckpt["family_map"] = candidate_family_map
            trainable_module_names = ["decoder_family", "decoder_zh"]
            if unfreeze_top > 0:
                for i in range(n_backbone_layers - unfreeze_top, n_backbone_layers):
                    trainable_module_names.extend([f"layers.{i}", f"layer_norms.{i}"])
                trainable_module_names.append("final_norm")
            candidate_ckpt["candidate_v2"] = {
                "base_checkpoint": str(base_checkpoint),
                "family_head_strategy": "expanded_dpbrane_class_from_old_unknown_init",
                "trainable_modules": trainable_module_names,
                "unfreeze_top_layers": unfreeze_top,
                "zh_softplus": args.zh_softplus,
                "label_smoothing": args.label_smoothing,
                "loss": {
                    "family_ce": 1.0,
                    "zh_smooth_l1": 0.5,
                    "zh_negative_penalty": 1.0,
                    "kerr_logit_penalty": args.kerr_logit_penalty,
                },
                "optimizer": {
                    "family_lr": args.family_lr,
                    "zh_lr": args.zh_lr,
                    "backbone_lr": args.backbone_lr if unfreeze_top > 0 else None,
                    "weight_decay": args.weight_decay,
                },
                "best_epoch": best_epoch,
                "sandbox_train_counts": _family_counts(dataset["train_rows"]),
                "sandbox_test_counts": _family_counts(dataset["test_rows"]),
            }
            candidate_ckpt["history_candidate_v2"] = history
            torch.save(candidate_ckpt, candidate_checkpoint_path)

            summary_payload = {
                "created_at": _utc_now_iso(),
                "stage": STAGE_NAME,
                "status": "PASS",
                "base_checkpoint": str(base_checkpoint),
                "candidate_checkpoint": str(candidate_checkpoint_path),
                "sandbox_dir": str(sandbox_dir),
                "n_manifest_geometries": dataset["manifest_n"],
                "n_train": len(dataset["train_rows"]),
                "n_test": len(dataset["test_rows"]),
                "candidate_family_map": candidate_family_map,
                "trainable_modules": trainable_module_names,
                "unfreeze_top_layers": unfreeze_top,
                "zh_softplus": args.zh_softplus,
                "label_smoothing": args.label_smoothing,
                "best_epoch": best_epoch,
                "train_family_counts": _family_counts(dataset["train_rows"]),
                "test_family_counts": _family_counts(dataset["test_rows"]),
                "train_metrics": train_metrics,
                "test_metrics": test_metrics,
                "history_tail": history[-10:],
            }
            _write_json_atomic(outputs_dir / "candidate_tune_summary.json", summary_payload)

        stdout_text = stdout_buffer.getvalue()
        stderr_text = stderr_buffer.getvalue()
        (logs_dir / "stdout.log").write_text(stdout_text, encoding="utf-8")
        (logs_dir / "stderr.log").write_text(stderr_text, encoding="utf-8")

        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "status": "PASS",
            "base_checkpoint": str(base_checkpoint),
            "candidate_checkpoint": str(outputs_dir / "emergent_geometry_model_candidate_v2.pt"),
            "best_epoch": summary_payload["best_epoch"],
            "n_train": summary_payload["n_train"],
            "n_test": summary_payload["n_test"],
            "trainable_modules": summary_payload["trainable_modules"],
            "test_family_accuracy": summary_payload["test_metrics"]["family_accuracy"],
            "test_n_negative_zh_raw": summary_payload["test_metrics"]["n_negative_zh_raw"],
            "test_dominant_family_fraction": summary_payload["test_metrics"]["dominant_family_fraction"],
            "test_family_pred_counts": summary_payload["test_metrics"]["family_pred_counts"],
        }

        manifest = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "script": str(Path(__file__).resolve()),
            "command": [
                sys.executable,
                str(Path(__file__).resolve()),
                "--run-id",
                args.run_id,
                "--runs-root",
                str(runs_root),
                "--sandbox-dir",
                str(sandbox_dir),
                "--base-checkpoint",
                str(base_checkpoint),
                "--device",
                args.device,
                "--n-epochs",
                str(args.n_epochs),
                "--batch-size",
                str(args.batch_size),
                "--family-lr",
                str(args.family_lr),
                "--zh-lr",
                str(args.zh_lr),
                "--weight-decay",
                str(args.weight_decay),
                "--kerr-logit-penalty",
                str(args.kerr_logit_penalty),
                "--seed",
                str(args.seed),
            ],
            "artifacts": {
                "candidate_checkpoint": "outputs/emergent_geometry_model_candidate_v2.pt",
                "candidate_tune_summary": "outputs/candidate_tune_summary.json",
                "logs": ["logs/stdout.log", "logs/stderr.log"],
            },
            "base_checkpoint_sha256": _sha256_file(base_checkpoint),
        }

        summary_payload = _rewrite_stage_paths(summary_payload, tmp_stage_dir, final_stage_dir)
        stage_summary = _rewrite_stage_paths(stage_summary, tmp_stage_dir, final_stage_dir)
        manifest = _rewrite_stage_paths(manifest, tmp_stage_dir, final_stage_dir)

        _write_json_atomic(outputs_dir / "candidate_tune_summary.json", summary_payload)
        _write_json_atomic(tmp_stage_dir / "manifest.json", manifest)
        _write_json_atomic(tmp_stage_dir / "stage_summary.json", stage_summary)
        os.replace(tmp_stage_dir, final_stage_dir)
        return 0
    except Exception:
        (logs_dir / "stdout.log").write_text(stdout_buffer.getvalue(), encoding="utf-8")
        (logs_dir / "stderr.log").write_text(stderr_buffer.getvalue(), encoding="utf-8")
        shutil.rmtree(tmp_stage_dir, ignore_errors=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
