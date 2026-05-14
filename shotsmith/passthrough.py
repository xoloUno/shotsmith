"""Passthrough step: copy raw PNGs straight into composed/ output unmodified.

For devices that shotsmith can't (or shouldn't) frame and compose. Today
this means Apple Watch: the hardware corner-radius would clip composed
bezel art at viewing time, so ASC accepts raw screen PNGs as the final
submission. See `devices.DEVICES["watch"]`.

Reads from `<input>/<locale>/raw/` and writes to the per-locale resolved
`output_paths[device_key]`. Honors `config.input_mapping` for filename
canonicalization (same contract as `frame` and `compose`): if a raw
filename maps to a canonical one, the output PNG carries the canonical
name. Without a mapping, output names equal input names.

Mtime-aware skip: if the output PNG exists and is at least as new as the
raw source, the copy is skipped. Matches the `frame` step's behavior
(see `frame.py` for the rationale — same "fresh refresh, stale output"
failure mode otherwise).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from . import devices
from .config import Config


class PassthroughError(RuntimeError):
    pass


@dataclass
class PassthroughResult:
    locale: str
    device: str
    written: list[Path]
    skipped: list[tuple[str, str]]  # (filename, reason)


def passthrough_locale(
    config: Config,
    locale: str,
    device_key: str,
    force: bool = False,
    dry_run: bool = False,
) -> PassthroughResult:
    """Copy all raw PNGs for one (locale, device) into the output dir.

    Pre-conditions:
    - `device_key` must reference a registered passthrough device
      (e.g. `DEVICES["watch"]` with `passthrough=True`).
    - `config.output_paths[device_key]` must be declared.
    """
    profile = devices.get(device_key)
    if not profile.passthrough:
        raise PassthroughError(
            f"Device '{device_key}' is not a passthrough device. "
            f"Did you mean `shotsmith frame`/`compose`?"
        )

    output_template = config.output_paths.get(device_key)
    if not output_template:
        raise PassthroughError(
            f"No output path configured for device '{device_key}'. "
            f"Add `output.{device_key}` to your config."
        )

    raw_dir = config.raw_dir(device_key, locale)
    output_dir = config.resolve(output_template.format(locale=locale))

    if not raw_dir.is_dir():
        raise PassthroughError(
            f"{device_key}/{locale}: raw/ directory not found at {raw_dir}. "
            f"Capture watch screenshots into raw/ first."
        )

    targets = _resolve_targets(config, device_key, raw_dir)
    if not targets:
        raise PassthroughError(
            f"{device_key}/{locale}: no source PNGs to passthrough in {raw_dir}. "
            f"Either capture first, or check your input_mapping if configured."
        )

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    skipped: list[tuple[str, str]] = []
    for source_name, canonical_name in targets:
        source_path = raw_dir / source_name
        if not source_path.is_file():
            skipped.append((
                canonical_name,
                f"source {source_name} not found in raw/ "
                f"(check input_mapping or capture step)",
            ))
            continue

        target_path = output_dir / canonical_name
        if target_path.exists() and not force:
            # Same mtime-aware invalidation as the frame step: skip only if
            # raw isn't newer than the existing output.
            if source_path.stat().st_mtime <= target_path.stat().st_mtime:
                skipped.append((
                    canonical_name,
                    "already passed through (raw not newer; pass --force to rebuild)",
                ))
                continue

        if dry_run:
            written.append(target_path)
            continue

        shutil.copy2(source_path, target_path)
        written.append(target_path)

    return PassthroughResult(
        locale=locale, device=device_key, written=written, skipped=skipped
    )


def _resolve_targets(
    config: Config, device_key: str, raw_dir: Path
) -> list[tuple[str, str]]:
    """Return list of (source_filename, canonical_filename) pairs to copy.

    Mirrors `frame._resolve_targets`: with `input_mapping`, iterate the
    mapping (source files come from mapping values); without, iterate every
    PNG in raw_dir with identity mapping.
    """
    if config.input_mapping and device_key in config.input_mapping:
        device_map = config.input_mapping[device_key]
        return [(source, canonical) for canonical, source in device_map.items()]
    return [(p.name, p.name) for p in sorted(raw_dir.glob("*.png"))]
