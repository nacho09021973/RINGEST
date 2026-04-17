#!/usr/bin/env python3
"""
make_canary_h5.py — generate synthetic boundary HDF5 files for canary audit.

Physics baseline (whitened strain, post-merger window):
  Signal = A1*exp(sigma1*t)*cos(omega1*t + phi1)
         + A2*exp(sigma2*t)*cos(omega2*t + phi2)
         + noise (unit Gaussian, representing whitened detector)

Parameters match Kerr QNM table (Berti et al. 2009, l=m=2):
  GW150914: M=63.1 Msun, chi=0.69
    n=0: f=254 Hz, tau=4.5 ms (dominant)
    n=1: f=235 Hz, tau=1.45 ms (weaker overtone)

  GW170104: M=48.9 Msun, chi=0.66
    n=0: f=310 Hz, tau=3.25 ms
    n=1: f=284 Hz, tau=1.08 ms

SNR: dominant mode at SNR~8 in the ringdown window (realistic for these events).
"""
import json
import numpy as np
import h5py
from pathlib import Path

G_OVER_C3_PER_MSUN = 4.925491025543576e-6  # s / M_sun

# Kerr QNM table entries (n=0 and n=1 at interpolated chi)
EVENTS = {
    "GW150914": {
        "M": 63.1, "chi": 0.69, "gps": 1126259462.4,
        # n=0: chi=0.69 from table
        "modes": [
            {"n": 0, "omega_re_norm": 0.49766, "omega_im_norm": -0.06893, "A": 1.0},
            {"n": 1, "omega_re_norm": 0.46169, "omega_im_norm": -0.22940, "A": 0.25},
        ],
        "noise_level": 0.12,  # relative to dominant mode amplitude
    },
    "GW170104": {
        "M": 48.9, "chi": 0.66, "gps": 1167559936.6,
        # n=0: interpolate chi=0.66 ≈ chi=0.60 entry shifted
        # using chi=0.60: omega_re=0.47004, omega_im=-0.07449
        "modes": [
            {"n": 0, "omega_re_norm": 0.47004, "omega_im_norm": -0.07449, "A": 1.0},
            {"n": 1, "omega_re_norm": 0.43329, "omega_im_norm": -0.24084, "A": 0.22},
        ],
        "noise_level": 0.15,
    },
}

FS = 4096.0
DURATION_TOTAL = 32.0   # seconds total (like GWOSC event window)
T_MERGER = 16.0         # merger at t_rel=0, placed at midpoint of window
SEED = 42


def make_boundary_h5(event_name: str, params: dict, out_path: Path) -> None:
    rng = np.random.default_rng(SEED)
    N = int(DURATION_TOTAL * FS)
    dt = 1.0 / FS

    M = params["M"]
    gps = params["gps"]
    scale = M * G_OVER_C3_PER_MSUN  # seconds per dimensionless unit

    t_rel = np.arange(N, dtype=np.float64) * dt - T_MERGER  # centered at merger

    # Build whitened strain: signal + noise
    # Signal is only present for t > 0 (post-merger ringdown)
    signal = np.zeros(N, dtype=np.float64)
    peak_amp = 1.0  # reference amplitude for SNR calculation

    for mode in params["modes"]:
        omega_re = mode["omega_re_norm"] / scale   # rad/s
        omega_im = mode["omega_im_norm"] / scale   # rad/s (negative)
        A = mode["A"] * peak_amp
        phase = rng.uniform(0, 2 * np.pi)

        # ringdown envelope: active only for t_rel > 0
        post_mask = t_rel > 0.0
        t_post = np.where(post_mask, t_rel, 0.0)
        envelope = A * np.exp(omega_im * t_post) * post_mask.astype(float)
        signal += envelope * np.cos(omega_re * t_post + phase)

    noise_amp = params["noise_level"] * peak_amp
    noise_h1 = rng.normal(0, noise_amp, N)
    noise_l1 = rng.normal(0, noise_amp, N)

    h1_whitened = signal + noise_h1
    l1_whitened = signal + noise_l1  # same signal, independent noise

    # Write HDF5 in the format expected by 01_extract_ringdown_poles.py
    with h5py.File(out_path, "w") as f:
        # Root attrs
        f.attrs["event"] = event_name
        f.attrs["gps"] = float(gps)
        f.attrs["fs_hz"] = float(FS)
        f.attrs["dt"] = float(dt)
        f.attrs["M_final_Msun"] = float(M)
        f.attrs["chi_final"] = float(params["chi"])

        # time group
        tg = f.create_group("time")
        tg.create_dataset("t_rel", data=t_rel)
        tg.attrs["fs_hz"] = float(FS)
        tg.attrs["dt"] = float(dt)

        # strain group
        sg = f.create_group("strain")
        sg.create_dataset("H1", data=h1_whitened)
        sg.create_dataset("L1", data=l1_whitened)
        sg.create_dataset("H1_whitened", data=h1_whitened)
        sg.create_dataset("L1_whitened", data=l1_whitened)

    print(f"  Wrote: {out_path}")
    print(f"    M={M} Msun, chi={params['chi']}, GPS={gps}")
    for mode in params["modes"]:
        omega_re = mode["omega_re_norm"] / (M * G_OVER_C3_PER_MSUN)
        omega_im = mode["omega_im_norm"] / (M * G_OVER_C3_PER_MSUN)
        tau_ms = -1000.0 / omega_im
        f_hz = omega_re / (2 * np.pi)
        print(f"    n={mode['n']}: f={f_hz:.1f} Hz, tau={tau_ms:.2f} ms, A={mode['A']}")


def write_manifest(run_dir: Path, event: str, boundary_rel: str) -> None:
    manifest = {
        "manifest_version": "2.0",
        "created_at": "2026-04-17T00:00:00+00:00",
        "run_dir": str(run_dir),
        "artifacts": {"ligo_boundary_h5": boundary_rel},
        "metadata": {"event": event, "synthetic_canary": True},
    }
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    base = Path("/home/user/RINGEST/runs/canary_audit")
    for event_name, params in EVENTS.items():
        run_dir = base / event_name
        boundary_dir = run_dir / "data_boundary"
        boundary_dir.mkdir(parents=True, exist_ok=True)
        boundary_path = boundary_dir / f"{event_name}_boundary.h5"
        make_boundary_h5(event_name, params, boundary_path)
        write_manifest(run_dir, event_name, f"data_boundary/{event_name}_boundary.h5")

    print("\nDone. Canary HDF5 files written.")
