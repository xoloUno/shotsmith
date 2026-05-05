---
name: shotsmith
description: Compose App Store screenshots with `shotsmith` — gradient backgrounds, captions, multi-locale, framed-PNG-aware. Use this skill when the user asks to render captioned marketing screenshots, set up a multi-locale screenshot pipeline, validate a screenshot directory contract, or migrate from `appshot-cli`. Pillow-based; wraps `frames-cli` for device bezels.
---

# shotsmith

`shotsmith` 0.2.0 composes App Store Connect-ready screenshots from already-framed PNGs (typically produced by `frames-cli`). It adds gradient backgrounds, captions, optional subtitles, and handles multi-locale rendering. Stable per-device directory contract: `raw/` → `framed/` → `composed/`.

## What Agents Should Know

- The CLI is `shotsmith`. Five subcommands: `stage`, `frame`, `compose`, `verify`, `pipeline`. All take `--config`/`-c <path>`, `--locale <code>` (repeatable), `--device <iphone|ipad>` (repeatable). With no filter flags, every (device × locale) combination runs.
- **Don't bypass the directory contract.** PNGs belong in `<input>/<locale>/raw/` (capture output) or `<input>/<locale>/framed/` (frames-cli output). Loose PNGs at the locale root are an anti-pattern that `verify` flags. The composed output goes to `<output>/<locale>/<device>/`.
- Apple Watch screenshots are screen-only on the ASC submission path — shotsmith **never** composes them. Stage raw `simctl io screenshot` output (422×514 native for Ultra 3) directly into the composed-output dir alongside iPhone/iPad. The watch hardware corner-radius would clip any framing or caption art at viewing time.
- iPhone 6.9" (1320×2868) + iPad 13" (2064×2752) are Apple's required ASC submission sizes. Apple auto-scales them down to smaller iPhone/iPad slots — uploading those two covers every device class.
- Pillow is the only runtime dependency. `pipx install` handles it.

## Install

```bash
pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
shotsmith --version
```

## Quick Reference

```bash
# Re-render composed PNGs after a caption tweak (no re-capture, no re-frame)
shotsmith compose --config fastlane/shotsmith/config.json

# Frame raw inputs via frames-cli (writes to framed/, never overwrites raw/)
shotsmith frame --config fastlane/shotsmith/config.json
shotsmith frame --config <path> --force          # re-frame existing PNGs

# Stage manual-gesture inputs (declared in manual_inputs config block) into raw/
shotsmith stage --config fastlane/shotsmith/config.json

# Validate the directory contract end-to-end
shotsmith verify --config fastlane/shotsmith/config.json

# Run everything (verify → stage → frame → compose)
shotsmith pipeline --config fastlane/shotsmith/config.json
shotsmith pipeline --config <path> --steps compose       # just re-render
shotsmith pipeline --config <path> --steps capture,stage,frame,compose
```

`pipeline --steps` defaults to `stage,frame,compose`. Add `capture` if your config defines a `pipeline.capture_hook`.

## Config Schema (shorthand)

```json
{
  "version": 2,
  "input":  { "iphone": "../screenshots/{locale}/iPhone 6.9\" Display" },
  "output": { "iphone": "composed/{locale}/iPhone 6.9\" Display" },
  "pipeline": { "frames_cli": "frames", "verify_strict": true },
  "background": {
    "type": "linear-gradient",
    "stops": ["#6B4FBB", "#FF6B5C"],
    "angle": 180,
    "dither": 30
  },
  "caption": {
    "font": "New York Small Bold", "color": "#FFFFFF",
    "size_iphone": 115, "size_ipad": 130,
    "position": "footer", "padding_pct": 3.5,
    "max_lines": 2, "line_height": 1.15
  },
  "subtitle": { "font": "...", "size_iphone": 60, "spacing_pct": 1.5, ... },
  "captions_file": "captions.json",
  "locales": ["en-US", "es-ES", "es-MX"],
  "manual_inputs": {
    "iphone": {
      "source": "../manual-captures/{locale}",
      "files": ["90_LockScreen.png", "91_HomeScreen.png", "92_ControlCenter.png"]
    }
  },
  "input_mapping": {
    "iphone": { "01_Hero.png": "from_xcuitest_HomeScreen.png" }
  }
}
```

Path templates use `{locale}`. All paths are config-relative. `subtitle`, `manual_inputs`, `input_mapping`, and `pipeline` are optional.

## Captions File

Per-image, per-locale. String form is shorthand for caption-only; dict form supports subtitles and per-device overrides.

```json
{
  "01_HomeScreen.png": {
    "en":    { "caption": "Track everything", "subtitle": "in one place" },
    "en-US": { "caption_iphone": "Track everything\nin one place" },
    "es":    "Todo en un solo lugar"
  }
}
```

shotsmith resolves locale → language fallback (`es-MX` → `es` → skip with warning). Use `\n` for forced line breaks.

## Common Tasks

### Re-render after a caption tweak
```bash
shotsmith compose --config fastlane/shotsmith/config.json
```
Just `compose` — no re-capture, no re-frame. Reads from `framed/`, writes to `composed/`.

### Add a new locale
1. Add the locale to `locales` in `config.json`
2. Add the language entry (or full locale) to `captions.json`
3. (If using `manual_inputs`) capture the manual-gesture surfaces for the new locale
4. `shotsmith pipeline --config <path>` to render the new locale

### Debug a missing manual capture
`shotsmith verify --config <path>` names the missing source file directly:
```
❌ iphone/es-MX: manual_inputs source(s) missing in /…/manual-captures/es-MX:
   91_HomeScreen_Widget.png
```
Recapture via your project's manual-capture flow (the upstream xoloUno iOS playbook ships `/capture-manual-surfaces` for this).

### Fix "matches ASC composed size" verify error
Means a PNG in `framed/` has dimensions like 1320×2868 — those are the *output* size, not frames-cli's input size. The PNG is a prior composition leaked back into `framed/`. Move it out and re-run `shotsmith frame`.

## Watch screenshots

shotsmith never composes Apple Watch screenshots for ASC submissions. The capture path is:

```bash
xcrun simctl io "$WATCH_SIM" screenshot path/to/output.png
```

Stage the raw PNG into the composed-output dir so a single `upload_screenshots` ships everything. See the upstream playbook's `.claude/rules/screenshot-pipeline.md` for the seven-gotcha checklist (ASC dimensions per device class, alpha rejection rules, sheet auto-presentation timing, ScrollViewReader race conditions, etc.).

## Tips

- The `raw/` and `framed/` dirs are **never** overwritten by shotsmith. Re-running `compose` with new gradient stops or caption text re-renders in seconds without touching captures or framed intermediates.
- `verify` is fast and information-dense. Run it before `compose` after any config edit.
- `--dry-run` works on `stage`, `frame`, `compose`, and `pipeline`. Plans without writing PNGs.
- Bundled gradient presets at `templates/presets/`: `mauve`, `royal-purple`, `apple-music`. Copy any one as a starting point.
- shotsmith deliberately doesn't replace `frames-cli`. They compose: `frames-cli` does device bezels (which it does well), shotsmith adds the gradient + caption layer.

## Repo

[github.com/xoloUno/shotsmith](https://github.com/xoloUno/shotsmith) — issues, full schema docs, CHANGELOG.
