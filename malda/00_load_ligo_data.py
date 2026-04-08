#!/usr/bin/env python3
"""00_load_ligo_data.py — CUERDAS-MALDACENA

Adapter that converts locally downloaded GWOSC/GWpy ringdown windows (NPZ)
into a CUERDAS-style boundary data artifact inside a deterministic run_dir.

v4 change (whitening):
  - Optional PSD-based whitening via --whiten flag.
  - PSD estimated with Welch's method from an offband segment (t_rel before event).
  - Whitened strain stored as strain/H1_whitened (+ L1) alongside raw strain.
  - All whitening parameters logged in attrs, meta, and manifest for reproducibility.
  - 01_extract_ringdown_poles.py uses H1_whitened/L1_whitened when present.

v3 change (robust --set-latest semantics):
  - If --set-latest points to an existing *directory* (not a symlink), interpret
    it as a container directory and place the symlink as <dir>/latest.
  - If --set-latest resolves to the run_dir itself, place the symlink as
    <run_dir.parent>/latest.
  - Refuse to replace a real directory at the final link path.

v2 change (ergonomics):
  - Duplicate key timing attributes (fs_hz, dt, gps) onto the HDF5 group
    `/time` in addition to the file root attrs.

Design goals:
  - Runnable from any CWD (paths resolved relative to PROJECT_ROOT).
  - Deterministic, auditable outputs (run_manifest.json + summary.json).
  - No physics injection: only data formatting + optional signal hygiene
    (detrend, window, FFT, whitening).

Inputs (expected NPZ schema; see descarga_GW150914_v7.py outputs):
  - t_gps: 1D float array
  - strain: 1D float array
  - fs: scalar (Hz)
  - ifo/event/gps/start/end/source_url: scalars/strings

Outputs (inside RUN_DIR):
  - run_manifest.json (IO_LAYOUT_V2 spirit: run_dir absolute, artifacts relative)
  - adapter_spec.json (parameters actually used)
  - summary.json
  - data_boundary/<event>_boundary.h5
  - data_boundary/<event>_boundary_meta.json

Whitening method (when --whiten is set):
  1. Extract offband segment: t_rel in [--whiten-psd-trel-start, --whiten-psd-trel-end].
  2. Estimate one-sided PSD via Welch's method (scipy.signal.welch).
  3. Interpolate PSD onto the full strain's rfft frequency grid.
  4. Hard-zero bins below fmin_hz and above fmax_hz; apply 10-bin cosine roll-off at edges.
  5. Divide strain rfft by ASD = sqrt(PSD); apply floor to avoid division by zero.
  6. Inverse rfft to produce whitened time series (real, same length as input).
  The whitened strain has approximately unit noise variance per frequency bin in [fmin, fmax].

This script is intentionally self-contained; it does NOT assume any other
repo modules exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np


SCRIPT_VERSION = "00_load_ligo_data.py/v4"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_canonical_dumps(obj: Any) -> str:
    """Stable JSON encoding for hashing (sorted keys, compact separators)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _safe_relpath_no_up(path_str: str) -> None:
    parts = Path(path_str).parts
    if ".." in parts:
        raise ValueError(f"Relative path must not contain '..': {path_str}")


def _resolve_root_relative(project_root: Path, p: str) -> Path:
    """Resolve an input path p.

    - If absolute: use as-is.
    - If relative: interpret as PROJECT_ROOT / p.
    - Reject relative paths containing '..'.
    """
    if os.path.isabs(p):
        return Path(p)
    _safe_relpath_no_up(p)
    return (project_root / p).resolve()


def _mkdirp(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _atomic_symlink(target_abs: Path, link_path: Path) -> None:
    """Atomically update a symlink to point to an absolute target.

    Safety rule: refuse to replace a real directory at link_path.
    """
    if not target_abs.is_absolute():
        raise ValueError("target_abs must be absolute")

    # If the final destination is a real directory (not a symlink), do not clobber it.
    if link_path.exists() and link_path.is_dir() and not link_path.is_symlink():
        raise IsADirectoryError(
            f"Refusing to replace directory with symlink: {link_path}. "
            "Pass --set-latest to a symlink path (e.g. outputs/latest) or a directory "
            "container (e.g. outputs) and the script will use <dir>/latest."
        )

    _mkdirp(link_path.parent)
    tmp = link_path.with_name(link_path.name + ".tmp")
    try:
        if tmp.exists() or tmp.is_symlink():
            tmp.unlink()
        tmp.symlink_to(str(target_abs))
        os.replace(tmp, link_path)
    finally:
        if tmp.exists() or tmp.is_symlink():
            try:
                tmp.unlink()
            except OSError:
                pass


def _normalize_set_latest_path(project_root: Path, run_dir: Path, raw: str) -> Path:
    """Normalize --set-latest.

    Accepted user intents:
      1) A symlink path (e.g. outputs/latest) -> use as-is.
      2) A directory container (e.g. outputs) -> use outputs/latest.
      3) Mistakenly passing the run_dir itself -> use run_dir.parent/latest.
    """
    link = _resolve_root_relative(project_root, raw)

    # If the user accidentally points to the run_dir itself, interpret as wanting a stable alias.
    try:
        if link.resolve() == run_dir.resolve():
            return run_dir.parent / "latest"
    except OSError:
        # If resolve fails (broken symlink, etc.), ignore.
        pass

    # If link is an existing real directory, interpret as container dir.
    if link.exists() and link.is_dir() and not link.is_symlink():
        return link / "latest"

    return link


def _detrend_linear(y: np.ndarray) -> np.ndarray:
    """Remove mean + best-fit line (least squares) from y."""
    x = np.arange(y.size, dtype=np.float64)
    A = np.vstack([x, np.ones_like(x)]).T
    m, b = np.linalg.lstsq(A, y.astype(np.float64), rcond=None)[0]
    return y.astype(np.float64) - (m * x + b)


def _hann_window(n: int) -> np.ndarray:
    if n <= 1:
        return np.ones((n,), dtype=np.float64)
    k = np.arange(n, dtype=np.float64)
    return 0.5 - 0.5 * np.cos(2.0 * np.pi * k / (n - 1))


def _rfft_with_freq(y: np.ndarray, fs: float) -> Tuple[np.ndarray, np.ndarray]:
    """One-sided FFT using rfft."""
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(y.size, d=1.0 / fs)
    return f.astype(np.float64), Y.astype(np.complex128)


def _estimate_psd_welch(y: np.ndarray, fs: float, nperseg: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate one-sided PSD using Welch's method.

    Returns (freqs_hz, psd) where psd has units strain^2/Hz.
    nperseg defaults to min(len(y), max(256, len(y)//8)) for good frequency resolution.
    """
    try:
        from scipy.signal import welch  # type: ignore
    except ImportError as e:
        raise RuntimeError("scipy is required for whitening. Install with: pip install scipy") from e

    n = len(y)
    if nperseg is None:
        nperseg = int(min(n, max(256, n // 8)))
    freqs, psd = welch(y, fs=fs, nperseg=nperseg, window="hann", average="median")
    return freqs.astype(np.float64), psd.astype(np.float64)


def _whiten_strain(
    y: np.ndarray,
    fs: float,
    psd_freqs: np.ndarray,
    psd_vals: np.ndarray,
    fmin_hz: float = 20.0,
    fmax_hz: float = 1800.0,
    asd_floor_factor: float = 1e-6,
    roll_off_bins: int = 12,
) -> np.ndarray:
    """Whiten a strain time series using a pre-estimated PSD.

    Steps:
      1. FFT the full strain.
      2. Interpolate PSD onto the strain's rfft frequency grid.
      3. Apply a bandpass mask [fmin_hz, fmax_hz] with cosine roll-off at edges.
      4. Divide by ASD (sqrt of masked PSD); apply floor to avoid blow-up in quiet bins.
      5. Inverse FFT → real whitened time series, same length as y.

    The roll-off avoids Gibbs ringing at the band edges. roll_off_bins controls the
    width of the cosine taper (in frequency bins) applied at each edge.
    """
    n = len(y)
    Y = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    # Interpolate PSD onto rfft grid (log-linear interpolation avoids negative values)
    log_psd_interp = np.interp(
        freqs,
        psd_freqs,
        np.log(psd_vals + 1e-300),
        left=np.log(psd_vals[0] + 1e-300),
        right=np.log(psd_vals[-1] + 1e-300),
    )
    psd_interp = np.exp(log_psd_interp)

    # Build bandpass mask with cosine roll-off
    mask = np.zeros(len(freqs), dtype=np.float64)
    in_band = (freqs >= fmin_hz) & (freqs <= fmax_hz)
    mask[in_band] = 1.0

    # Cosine roll-on at fmin
    i_fmin = int(np.searchsorted(freqs, fmin_hz))
    i_start = max(0, i_fmin - roll_off_bins)
    if i_start < i_fmin:
        ramp = np.linspace(0.0, np.pi, i_fmin - i_start)
        mask[i_start:i_fmin] = 0.5 * (1.0 - np.cos(ramp))

    # Cosine roll-off at fmax
    i_fmax = int(np.searchsorted(freqs, fmax_hz))
    i_end = min(len(freqs), i_fmax + roll_off_bins)
    if i_fmax < i_end:
        ramp = np.linspace(0.0, np.pi, i_end - i_fmax)
        mask[i_fmax:i_end] = 0.5 * (1.0 + np.cos(ramp))

    # ASD with floor to prevent blow-up in notch/quiet bins
    asd = np.sqrt(psd_interp)
    asd_floor = asd_floor_factor * float(np.median(asd[in_band]) if np.any(in_band) else asd.max())
    asd = np.maximum(asd, asd_floor)

    # Normalize: divide by ASD and apply mask; scale by sqrt(2/fs) for unit variance
    Y_white = Y * mask / asd * np.sqrt(2.0 / fs)

    # Inverse FFT; irfft guarantees real output of length n
    y_white = np.fft.irfft(Y_white, n=n)
    return y_white.astype(np.float64)


@dataclass
class LigoSeries:
    ifo: str
    event: str
    gps: float
    start: float
    end: float
    fs: float
    t_gps: np.ndarray
    strain: np.ndarray
    source_url: str


def _load_npz(npz_path: Path) -> LigoSeries:
    z = np.load(npz_path, allow_pickle=False)
    required = ["t_gps", "strain", "fs", "ifo", "event", "gps", "start", "end", "source_url"]
    missing = [k for k in required if k not in z]
    if missing:
        raise ValueError(f"NPZ missing keys {missing}: {npz_path}")

    def _scalar(k: str):
        v = z[k]
        if isinstance(v, np.ndarray) and v.shape == ():
            return v.item()
        return v

    t_gps = np.asarray(z["t_gps"], dtype=np.float64)
    strain = np.asarray(z["strain"], dtype=np.float64)
    if t_gps.ndim != 1 or strain.ndim != 1 or t_gps.size != strain.size:
        raise ValueError(f"t_gps/strain must be 1D and same length in {npz_path}")

    fs_value = float(_scalar("fs"))
    if fs_value <= 0:
        raise ValueError(
            f"fs must be > 0 in {npz_path}; got fs={fs_value}"
        )

    return LigoSeries(
        ifo=str(_scalar("ifo")),
        event=str(_scalar("event")),
        gps=float(_scalar("gps")),
        start=float(_scalar("start")),
        end=float(_scalar("end")),
        fs=fs_value,
        t_gps=t_gps,
        strain=strain,
        source_url=str(_scalar("source_url")),
    )


def _load_meta_optional(meta_path: Optional[Path]) -> Dict[str, Any]:
    if not meta_path:
        return {}
    if not meta_path.exists():
        raise FileNotFoundError(meta_path)
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _check_compat(a: LigoSeries, b: LigoSeries) -> None:
    if a.event != b.event:
        raise ValueError(f"event mismatch: {a.event} vs {b.event}")
    if abs(a.gps - b.gps) > 1e-6:
        raise ValueError(f"gps mismatch: {a.gps} vs {b.gps}")
    if abs(a.fs - b.fs) > 1e-9:
        raise ValueError(f"fs mismatch: {a.fs} vs {b.fs}")
    if a.t_gps.size != b.t_gps.size:
        raise ValueError(f"length mismatch: {a.t_gps.size} vs {b.t_gps.size}")
    if not np.allclose(a.t_gps, b.t_gps, rtol=0.0, atol=1e-12):
        raise ValueError("t_gps grids differ between IFOs")


def _build_run_id(event: str, inputs_sha: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}__00_load_ligo__{event}__{inputs_sha[:12]}"


def _write_h5(out_path: Path, payload: Dict[str, Any]) -> None:
    try:
        import h5py  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("h5py is required. Install with: pip install h5py") from e

    def ensure_groups(h, dpaths):
        for dpath in dpaths:
            if "/" in dpath:
                g = dpath.rsplit("/", 1)[0]
                if g:
                    h.require_group(g)

    with h5py.File(out_path, "w") as h:
        ensure_groups(h, payload.get("datasets", {}).keys())
        ensure_groups(h, payload.get("complex_datasets", {}).keys())

        for k, v in payload.get("attrs", {}).items():
            h.attrs[k] = v

        for gpath, gattrs in payload.get("group_attrs", {}).items():
            grp = h.require_group(gpath)
            for k, v in gattrs.items():
                grp.attrs[k] = v

        for dpath, arr in payload.get("datasets", {}).items():
            h.create_dataset(dpath, data=arr)

        for dpath, carr in payload.get("complex_datasets", {}).items():
            c = np.asarray(carr, dtype=np.complex128)
            stacked = np.stack([c.real, c.imag], axis=-1).astype(np.float64)
            h.create_dataset(dpath, data=stacked)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert downloaded GW150914 NPZ windows into CUERDAS boundary artifact.")
    parser.add_argument("--h1-npz", required=True, help="Path to H1 NPZ (root-relative or absolute)")
    parser.add_argument("--l1-npz", required=False, help="Path to L1 NPZ (root-relative or absolute)")
    parser.add_argument("--h1-meta", required=False, help="Optional H1 meta.json")
    parser.add_argument("--l1-meta", required=False, help="Optional L1 meta.json")
    parser.add_argument("--runs-root", default="runs", help="Runs root directory (root-relative unless absolute). Default: runs")
    parser.add_argument("--run-dir", default=None, help="Explicit run dir. If omitted, creates under --runs-root with deterministic id.")
    parser.add_argument(
        "--set-latest",
        default=None,
        help=(
            "Optional symlink path to update to this run. "
            "If you pass a directory (e.g. outputs), the symlink will be outputs/latest. "
            "If you pass the run_dir by mistake, the symlink will be <run_dir.parent>/latest."
        ),
    )
    parser.add_argument("--data-dir-name", default="data_boundary", help="Name of data directory inside run_dir. Default: data_boundary")
    parser.add_argument("--fft", action="store_true", help="Compute and store one-sided FFT (rfft) for each IFO.")
    parser.add_argument("--detrend", choices=["none", "mean", "linear"], default="mean", help="Detrend option. Default: mean")
    parser.add_argument("--window", choices=["none", "hann"], default="hann", help="Window function before FFT. Default: hann")

    # Whitening options
    parser.add_argument("--whiten", action="store_true",
                        help="Whiten strain using PSD estimated from an offband segment. "
                             "Stores strain/H1_whitened (+ L1) alongside raw strain. "
                             "Requires scipy.")
    parser.add_argument("--whiten-psd-trel-start", type=float, default=-28.0,
                        help="Start of PSD estimation window (t_rel in seconds, relative to event GPS). "
                             "Must be before the merger. Default: -28.0")
    parser.add_argument("--whiten-psd-trel-end", type=float, default=-4.0,
                        help="End of PSD estimation window (t_rel in seconds). "
                             "Leave >=4s gap before merger to avoid contamination. Default: -4.0")
    parser.add_argument("--whiten-fmin-hz", type=float, default=20.0,
                        help="Low-frequency cutoff for whitening bandpass (Hz). Default: 20.0")
    parser.add_argument("--whiten-fmax-hz", type=float, default=1800.0,
                        help="High-frequency cutoff for whitening bandpass (Hz). Default: 1800.0")
    parser.add_argument("--whiten-nperseg", type=int, default=0,
                        help="Welch nperseg for PSD estimation. 0 = auto (min(N, max(256, N//8))). Default: 0")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent  # repo root (basurin/)

    h1_npz = _resolve_root_relative(project_root, args.h1_npz)
    l1_npz = _resolve_root_relative(project_root, args.l1_npz) if args.l1_npz else None
    h1_meta = _resolve_root_relative(project_root, args.h1_meta) if args.h1_meta else None
    l1_meta = _resolve_root_relative(project_root, args.l1_meta) if args.l1_meta else None

    s_h1 = _load_npz(h1_npz)
    s_l1 = _load_npz(l1_npz) if l1_npz else None
    if s_l1 is not None:
        _check_compat(s_h1, s_l1)

    meta_h1 = _load_meta_optional(h1_meta)
    meta_l1 = _load_meta_optional(l1_meta)

    inputs_fingerprints = {
        "h1_npz_sha256": _sha256_file(h1_npz),
        "h1_npz_path": str(args.h1_npz),
        "l1_npz_sha256": _sha256_file(l1_npz) if l1_npz else None,
        "l1_npz_path": str(args.l1_npz) if args.l1_npz else None,
        "h1_meta_sha256": _sha256_file(h1_meta) if h1_meta else None,
        "h1_meta_path": str(args.h1_meta) if args.h1_meta else None,
        "l1_meta_sha256": _sha256_file(l1_meta) if l1_meta else None,
        "l1_meta_path": str(args.l1_meta) if args.l1_meta else None,
    }
    inputs_sha = _sha256_bytes(_json_canonical_dumps(inputs_fingerprints).encode("utf-8"))

    if args.run_dir:
        run_dir = _resolve_root_relative(project_root, args.run_dir)
    else:
        runs_root = _resolve_root_relative(project_root, args.runs_root)
        run_dir = (runs_root / _build_run_id(s_h1.event, inputs_sha)).resolve()

    data_dir = run_dir / args.data_dir_name
    _mkdirp(data_dir)

    t_gps = s_h1.t_gps
    t_rel = (t_gps - s_h1.gps).astype(np.float64)

    def apply_detrend(x: np.ndarray) -> np.ndarray:
        if args.detrend == "none":
            return x.astype(np.float64)
        if args.detrend == "mean":
            return x.astype(np.float64) - float(np.mean(x))
        return _detrend_linear(x)

    strain_h1 = apply_detrend(s_h1.strain)
    strain_l1 = apply_detrend(s_l1.strain) if s_l1 is not None else None

    # --- Whitening -----------------------------------------------------------
    whiten_params: Dict[str, Any] = {"enabled": False}
    strain_h1_white: Optional[np.ndarray] = None
    strain_l1_white: Optional[np.ndarray] = None

    if args.whiten:
        psd_t_start = float(args.whiten_psd_trel_start)
        psd_t_end = float(args.whiten_psd_trel_end)
        fmin_hz = float(args.whiten_fmin_hz)
        fmax_hz = float(args.whiten_fmax_hz)
        nperseg_arg = int(args.whiten_nperseg) if args.whiten_nperseg > 0 else None

        # Validate offband window
        if psd_t_start >= psd_t_end:
            raise ValueError(f"--whiten-psd-trel-start ({psd_t_start}) must be < --whiten-psd-trel-end ({psd_t_end})")
        if psd_t_end > -1.0:
            raise ValueError(f"--whiten-psd-trel-end ({psd_t_end}) must be <= -1.0 s to avoid merger contamination")

        mask_offband = (t_rel >= psd_t_start) & (t_rel <= psd_t_end)
        n_offband = int(np.sum(mask_offband))
        if n_offband < 256:
            raise ValueError(
                f"Offband PSD segment too short: {n_offband} samples "
                f"(t_rel=[{psd_t_start},{psd_t_end}]). Need >=256."
            )

        nperseg_used = nperseg_arg if nperseg_arg is not None else int(min(n_offband, max(256, n_offband // 8)))

        # H1 whitening
        psd_freqs_h1, psd_vals_h1 = _estimate_psd_welch(
            strain_h1[mask_offband], float(s_h1.fs), nperseg=nperseg_used
        )
        strain_h1_white = _whiten_strain(
            strain_h1, float(s_h1.fs), psd_freqs_h1, psd_vals_h1,
            fmin_hz=fmin_hz, fmax_hz=fmax_hz
        )

        # L1 whitening (reuse H1 PSD grid structure but estimate from L1 offband)
        if strain_l1 is not None:
            psd_freqs_l1, psd_vals_l1 = _estimate_psd_welch(
                strain_l1[mask_offband], float(s_h1.fs), nperseg=nperseg_used
            )
            strain_l1_white = _whiten_strain(
                strain_l1, float(s_h1.fs), psd_freqs_l1, psd_vals_l1,
                fmin_hz=fmin_hz, fmax_hz=fmax_hz
            )

        whiten_params = {
            "enabled": True,
            "psd_trel_start": psd_t_start,
            "psd_trel_end": psd_t_end,
            "n_offband_samples": n_offband,
            "nperseg": nperseg_used,
            "fmin_hz": fmin_hz,
            "fmax_hz": fmax_hz,
            "method": "welch_median_asd_divide",
        }
        print(f"Whitening: offband [{psd_t_start:.1f}, {psd_t_end:.1f}]s, "
              f"n={n_offband}, nperseg={nperseg_used}, band=[{fmin_hz:.0f},{fmax_hz:.0f}] Hz")
    # -------------------------------------------------------------------------

    win = _hann_window(strain_h1.size) if args.window == "hann" else None

    fft_payload: Dict[str, Any] = {}
    if args.fft:
        x_h1 = strain_h1 * win if win is not None else strain_h1
        f, Y_h1 = _rfft_with_freq(x_h1, s_h1.fs)
        fft_payload["freq_hz"] = f
        fft_payload["H1"] = Y_h1
        if strain_l1 is not None:
            x_l1 = strain_l1 * win if win is not None else strain_l1
            _, Y_l1 = _rfft_with_freq(x_l1, s_h1.fs)
            fft_payload["L1"] = Y_l1

    event = s_h1.event
    out_h5 = data_dir / f"{event}_boundary.h5"
    out_meta = data_dir / f"{event}_boundary_meta.json"

    created_at = _utc_now_iso()
    dt = float(1.0 / s_h1.fs)

    attrs = {
        "event": event,
        "gps": float(s_h1.gps),
        "fs_hz": float(s_h1.fs),
        "dt": dt,
        "start_gps": float(t_gps[0]),
        "end_gps": float(t_gps[-1]),
        "created_at": created_at,
        "script_version": SCRIPT_VERSION,
        "source_url_H1": s_h1.source_url,
        "source_url_L1": s_l1.source_url if s_l1 is not None else "",
        "ifo_count": 2 if s_l1 is not None else 1,
        "detrend": args.detrend,
        "window": args.window,
        "fft": bool(args.fft),
        "whitened": bool(args.whiten),
    }

    group_attrs = {"time": {"gps": float(s_h1.gps), "fs_hz": float(s_h1.fs), "dt": dt}}

    datasets = {"time/t_gps": t_gps, "time/t_rel": t_rel, "strain/H1": strain_h1}
    if strain_l1 is not None:
        datasets["strain/L1"] = strain_l1
    if win is not None:
        datasets["preprocess/window"] = win
    if strain_h1_white is not None:
        datasets["strain/H1_whitened"] = strain_h1_white
    if strain_l1_white is not None:
        datasets["strain/L1_whitened"] = strain_l1_white

    complex_datasets: Dict[str, Any] = {}
    if args.fft:
        datasets["fft/freq_hz"] = fft_payload["freq_hz"]
        complex_datasets["fft/H1"] = fft_payload["H1"]
        if "L1" in fft_payload:
            complex_datasets["fft/L1"] = fft_payload["L1"]

    _write_h5(out_h5, {"attrs": attrs, "group_attrs": group_attrs, "datasets": datasets, "complex_datasets": complex_datasets})

    meta_payload: Dict[str, Any] = {
        "event": event,
        "gps": float(s_h1.gps),
        "fs_hz": float(s_h1.fs),
        "time": {"t_gps_start": float(t_gps[0]), "t_gps_end": float(t_gps[-1]), "n_samples": int(t_gps.size), "dt": dt},
        "inputs": inputs_fingerprints,
        "inputs_meta_h1": meta_h1,
        "inputs_meta_l1": meta_l1,
        "preprocess": {"detrend": args.detrend, "window": args.window, "fft": bool(args.fft),
                       "whitening": whiten_params},
        "artifacts": {"boundary_h5_rel": out_h5.relative_to(run_dir).as_posix(), "boundary_meta_rel": out_meta.relative_to(run_dir).as_posix()},
        "created_at": created_at,
        "script_version": SCRIPT_VERSION,
    }
    out_meta.write_text(json.dumps(meta_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    adapter_spec = {
        "script": "00_load_ligo_data.py",
        "script_version": SCRIPT_VERSION,
        "created_at": created_at,
        "params": {
            "h1_npz": str(args.h1_npz),
            "l1_npz": str(args.l1_npz) if args.l1_npz else None,
            "h1_meta": str(args.h1_meta) if args.h1_meta else None,
            "l1_meta": str(args.l1_meta) if args.l1_meta else None,
            "runs_root": str(args.runs_root),
            "run_dir": str(args.run_dir) if args.run_dir else None,
            "set_latest": str(args.set_latest) if args.set_latest else None,
            "data_dir_name": args.data_dir_name,
            "fft": bool(args.fft),
            "detrend": args.detrend,
            "window": args.window,
            "whiten": bool(args.whiten),
            "whiten_psd_trel_start": float(args.whiten_psd_trel_start) if args.whiten else None,
            "whiten_psd_trel_end": float(args.whiten_psd_trel_end) if args.whiten else None,
            "whiten_fmin_hz": float(args.whiten_fmin_hz) if args.whiten else None,
            "whiten_fmax_hz": float(args.whiten_fmax_hz) if args.whiten else None,
            "whiten_nperseg": int(args.whiten_nperseg) if args.whiten else None,
        },
        "whitening_applied": whiten_params,
        "inputs": inputs_fingerprints,
        "outputs": {"boundary_h5": out_h5.relative_to(run_dir).as_posix(), "boundary_meta_json": out_meta.relative_to(run_dir).as_posix()},
    }
    spec_canonical = _json_canonical_dumps(adapter_spec)
    spec_sha_canonical = _sha256_bytes(spec_canonical.encode("utf-8"))
    spec_path = run_dir / "adapter_spec.json"
    spec_path.write_text(json.dumps(adapter_spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    spec_sha_file = _sha256_file(spec_path)

    manifest = {
        "manifest_version": "2.0",
        "created_at": created_at,
        "run_dir": str(run_dir),
        "artifacts": {
            "data_dir": data_dir.relative_to(run_dir).as_posix(),
            "ligo_boundary_h5": out_h5.relative_to(run_dir).as_posix(),
            "ligo_boundary_meta_json": out_meta.relative_to(run_dir).as_posix(),
            "adapter_spec": "adapter_spec.json",
        },
        "metadata": {
            "script": "00_load_ligo_data.py",
            "script_version": SCRIPT_VERSION,
            "event": event,
            "gps": float(s_h1.gps),
            "ifo_count": 2 if s_l1 is not None else 1,
            "whitened": bool(args.whiten),
            "whitening": whiten_params,
            "spec_sha256_canonical": spec_sha_canonical,
            "spec_sha256_file": spec_sha_file,
            "inputs_sha256": inputs_sha,
        },
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "created_at": created_at,
        "script": "00_load_ligo_data.py",
        "script_version": SCRIPT_VERSION,
        "event": event,
        "gps": float(s_h1.gps),
        "closure_criterion": "adapter_completed",
        "boundary_h5_rel": out_h5.relative_to(run_dir).as_posix(),
        "boundary_h5": str(out_h5),
        "spec_sha256_canonical": spec_sha_canonical,
        "spec_sha256_file": spec_sha_file,
        "inputs_sha256": inputs_sha,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.set_latest:
        link = _normalize_set_latest_path(project_root, run_dir, args.set_latest)
        _atomic_symlink(run_dir, link)
        print(f"Updated latest symlink: {link} -> {run_dir}")

    print(f"RUN_DIR: {run_dir}")
    print(f"Wrote: {out_h5.relative_to(run_dir).as_posix()}")
    print(f"Wrote: {out_meta.relative_to(run_dir).as_posix()}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
