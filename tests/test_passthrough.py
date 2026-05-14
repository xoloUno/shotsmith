"""Tests for shotsmith passthrough step.

Passthrough copies raw/ → output/ unmodified for devices that bypass
frame + compose (today: Apple Watch). See `shotsmith/passthrough.py`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shotsmith import config as config_mod  # noqa: E402
from shotsmith import passthrough as passthrough_mod  # noqa: E402


def _write_config(tmp_path: Path) -> Path:
    cfg = {
        "version": 2,
        "input": {
            "iphone": "input/iphone/{locale}",
            "watch": "input/watch/{locale}",
        },
        "output": {
            "iphone": "output/iphone/{locale}",
            "watch": "output/watch/{locale}",
        },
        "background": {"type": "linear-gradient", "stops": ["#000", "#FFF"], "angle": 180},
        "caption": {
            "font": "New York Small Bold", "color": "#1B1B1B",
            "size_iphone": 60, "size_ipad": 60, "position": "footer",
            "padding_pct": 3.0, "max_lines": 2, "line_height": 1.15,
        },
        "captions_file": "captions.json",
        "locales": ["en-US"],
        "pipeline": {"frames_cli": "frames", "verify_strict": False},
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    (tmp_path / "captions.json").write_text("{}")
    return cfg_path


def _make_png(path: Path, size: tuple[int, int] = (422, 514)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (10, 10, 10)).save(path)


def test_passthrough_copies_raw_to_output(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    raw_dir = cfg.raw_dir("watch", "en-US")
    _make_png(raw_dir / "01.png")
    _make_png(raw_dir / "02.png")

    result = passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")
    assert len(result.written) == 2
    out_dir = cfg.resolve("output/watch/en-US")
    assert (out_dir / "01.png").is_file()
    assert (out_dir / "02.png").is_file()


def test_passthrough_refuses_composed_device(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    with pytest.raises(passthrough_mod.PassthroughError, match="not a passthrough"):
        passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="iphone")


def test_passthrough_errors_on_missing_raw(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    with pytest.raises(passthrough_mod.PassthroughError, match="raw/ directory not found"):
        passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")


def test_passthrough_errors_on_empty_raw(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    cfg.raw_dir("watch", "en-US").mkdir(parents=True)
    with pytest.raises(passthrough_mod.PassthroughError, match="no source PNGs"):
        passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")


def test_passthrough_dry_run_does_not_write(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    raw_dir = cfg.raw_dir("watch", "en-US")
    _make_png(raw_dir / "01.png")

    result = passthrough_mod.passthrough_locale(
        cfg, locale="en-US", device_key="watch", dry_run=True,
    )
    assert len(result.written) == 1
    out_dir = cfg.resolve("output/watch/en-US")
    assert not (out_dir / "01.png").exists()


def test_passthrough_honors_input_mapping(tmp_path):
    """Renames raw → canonical on copy, same contract as frame."""
    raw = json.loads(_write_config(tmp_path).read_text())
    raw["input_mapping"] = {
        "watch": {
            "01_Activity.png": "from_simctl_Activity.png",
            "02_Workouts.png": "from_simctl_Workouts.png",
        }
    }
    (tmp_path / "config.json").write_text(json.dumps(raw))
    cfg = config_mod.load(tmp_path / "config.json")

    raw_dir = cfg.raw_dir("watch", "en-US")
    _make_png(raw_dir / "from_simctl_Activity.png")
    _make_png(raw_dir / "from_simctl_Workouts.png")

    result = passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")
    assert len(result.written) == 2
    out_dir = cfg.resolve("output/watch/en-US")
    assert (out_dir / "01_Activity.png").is_file()
    assert (out_dir / "02_Workouts.png").is_file()
    # Source-named files must NOT appear in output.
    assert not (out_dir / "from_simctl_Activity.png").exists()


def test_passthrough_skips_when_output_newer(tmp_path):
    """mtime-aware skip: parity with frame's stale-output fix."""
    cfg = config_mod.load(_write_config(tmp_path))
    raw_dir = cfg.raw_dir("watch", "en-US")
    out_dir = cfg.resolve("output/watch/en-US")
    out_dir.mkdir(parents=True)

    raw_path = raw_dir / "01.png"
    out_path = out_dir / "01.png"
    _make_png(raw_path)
    _make_png(out_path)
    # Output newer than raw.
    t = raw_path.stat().st_mtime
    os.utime(raw_path, (t, t))
    os.utime(out_path, (t + 10, t + 10))

    result = passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")
    assert result.written == []
    assert len(result.skipped) == 1
    assert "raw not newer" in result.skipped[0][1]


def test_passthrough_reframes_when_raw_newer(tmp_path):
    cfg = config_mod.load(_write_config(tmp_path))
    raw_dir = cfg.raw_dir("watch", "en-US")
    out_dir = cfg.resolve("output/watch/en-US")
    out_dir.mkdir(parents=True)

    raw_path = raw_dir / "01.png"
    out_path = out_dir / "01.png"
    _make_png(out_path)
    _make_png(raw_path)
    # Raw newer than output.
    t = out_path.stat().st_mtime
    os.utime(out_path, (t, t))
    os.utime(raw_path, (t + 10, t + 10))

    result = passthrough_mod.passthrough_locale(cfg, locale="en-US", device_key="watch")
    assert len(result.written) == 1
    assert result.skipped == []
