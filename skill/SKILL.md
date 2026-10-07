---
name: shotsmith
description: Compose App Store screenshots with `shotsmith` — gradient backgrounds, captions, multi-locale, framed-PNG-aware. Use this skill when the user asks to render captioned marketing screenshots, set up a multi-locale screenshot pipeline, validate a screenshot directory contract, or migrate from `appshot-cli`. Pillow-based; wraps `frames-cli` for device bezels.
---

# shotsmith

`shotsmith` 0.2.0 composes App Store Connect-ready screenshots from already-framed PNGs (typically produced by `frames-cli`). It adds gradient backgrounds, captions, optional subtitles, and handles multi-locale rendering. Stable per-device directory contract: `raw/` → `framed/` → the device's configured output path for iPhone/iPad; passthrough devices (Apple Watch) go `raw/` → output with no framing or composition.

## What Agents Should Know

- The CLI is `shotsmith`. Six subcommands: `stage`, `frame`, `passthrough`, `compose`, `verify`, `pipeline`. All take `--config`/`-c <path>`, `--locale <code>` (repeatable), `--device <iphone|ipad|watch>` (repeatable). With no filter flags, every (device × locale) combination runs — except that `frame` and `compose` skip passthrough devices and `passthrough` only touches them.
- **Don't bypass the directory contract.** PNGs belong in `<input>/<locale>/raw/` (capture output) or `<input>/<locale>/framed/` (frames-cli output). Loose PNGs at the locale root are an anti-pattern that `verify` flags. Composed PNGs (and passthrough copies) go to each device's resolved `output` template, which normally contains `{locale}`.
- Apple Watch screenshots are screen-only on the ASC submission path — shotsmith **never** frames or composes them. `watch` is a **passthrough device**: declare it in `input`/`output` like iPhone/iPad, and the `passthrough` step copies `raw/` → output unmodified (honoring `input_mapping`). `verify` checks watch raws against the 422×514 Ultra 3 screen size. The watch hardware corner-radius would clip any framing or caption art at viewing time.
- iPhone 6.9" (1320×2868) + iPad 13" (2064×2752) are Apple's required ASC submission sizes. Apple auto-scales them down to smaller iPhone/iPad slots — uploading those two covers every iPhone and iPad size class.
- Pillow is the only Python package dependency, and `pipx install` handles it. `frame` also needs `frames-cli` on PATH, and so does `pipeline` when it frames iPhone or iPad inputs.

## Install

```bash
pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
shotsmith --version
```

The `passthrough` subcommand, the `watch` device, and `verify --strict` landed on `main` after the v0.2.0 tag. Until the next release, install from `main` to get them:

```bash
pipx install --force git+https://github.com/xoloUno/shotsmith.git@main
```

## Quick Reference

```bash
# Re-render composed PNGs after a caption tweak (no re-capture, no re-frame)
shotsmith compose --config fastlane/shotsmith/config.json

# Frame raw inputs via frames-cli (writes to framed/, never overwrites raw/)
shotsmith frame --config fastlane/shotsmith/config.json
shotsmith frame --config <path> --force          # re-frame existing PNGs

# Copy passthrough-device raws (watch) straight to output/ — no frame, no compose
shotsmith passthrough --config fastlane/shotsmith/config.json
shotsmith passthrough --config <path> --locale en-US --force   # re-copy existing

# Stage manual-gesture inputs (declared in manual_inputs config block) into raw/
shotsmith stage --config fastlane/shotsmith/config.json

# Validate the directory contract end-to-end
shotsmith verify --config fastlane/shotsmith/config.json
shotsmith verify --config <path> --strict        # warnings → errors (CI use)

# Run everything (verify → stage → frame → passthrough → compose)
shotsmith pipeline --config fastlane/shotsmith/config.json
shotsmith pipeline --config <path> --steps compose       # just re-render
shotsmith pipeline --config <path> --steps capture,stage,frame,passthrough,compose
```

`pipeline --steps` defaults to `stage,frame,passthrough,compose`. Add `capture` if your config defines a `pipeline.capture_hook`. `stage` is a no-op without a `manual_inputs` block; `passthrough` is a no-op without a passthrough device (today: `watch`) in the config.

## Config Schema (shorthand)

```json
{
  "version": 2,
  "input":  { "iphone": "../screenshots/{locale}/iPhone 6.9\" Display",
              "watch":  "../screenshots/{locale}/Apple Watch Ultra 3 (49mm)" },
  "output": { "iphone": "composed/{locale}/iPhone 6.9\" Display",
              "watch":  "composed/{locale}/Apple Watch Ultra 3 (49mm)" },
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

Path templates use `{locale}`; `manual_inputs.source` also accepts `{device}`. All paths are config-relative. Device keys are `iphone`, `ipad`, and `watch` (a passthrough device: no caption sizes, but `manual_inputs` and `input_mapping` still apply). `subtitle`, `manual_inputs`, `input_mapping`, and `pipeline` are optional.

## Captions File

Per-image, per-locale. String form is shorthand for caption-only; dict form supports subtitles and per-device overrides.

```json
{
  "01_HomeScreen.png": {
    "en":    { "caption": "Your headline", "subtitle": "with an optional subtitle" },
    "en-US": { "caption_iphone": "Your headline\non two lines" },
    "es":    "Tu titular aquí"
  }
}
```

shotsmith resolves locale → language fallback (`es-MX` → `es` → skip with warning). Use `\n` for forced line breaks.

## Common Tasks

### Re-render after a caption tweak
```bash
shotsmith compose --config fastlane/shotsmith/config.json
```
Just `compose` — no re-capture, no re-frame. Reads from `framed/`, writes to each device's output path.

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

shotsmith never frames or composes Apple Watch screenshots for ASC submissions. Capture straight into the watch lane's `raw/` dir:

```bash
xcrun simctl io "$WATCH_SIM" screenshot "<watch input>/<locale>/raw/01_Home.png"
```

With `watch` declared in `input`/`output`, `shotsmith pipeline` (or `shotsmith passthrough` alone) copies `raw/` → output unmodified, next to the composed iPhone/iPad PNGs, so a single `upload_screenshots` ships everything. Don't hand-copy watch PNGs into the output dir — that skips `input_mapping` renames. `verify` warns when a watch raw isn't 422×514; `shotsmith pipeline` runs it first, but `passthrough` alone doesn't. Use `verify --strict` or `pipeline.verify_strict_dimensions: true` to make that warning an error. See the upstream playbook's `.claude/rules/screenshot-pipeline.md` for the seven-gotcha checklist (ASC dimensions per device class, alpha rejection rules, sheet auto-presentation timing, ScrollViewReader race conditions, etc.).

## Tips

- `frame`, `compose` and `passthrough` never write to `raw/`. Captures land there from your capture hook (the pipeline's `capture` step) or from `stage`, which copies `manual_inputs` sources in; re-running either replaces files there. `frame` only rewrites a `framed/` PNG when its `raw/` source is newer (or with `--force`); `passthrough` applies the same rule to watch output. Re-running `compose` with new gradient stops or caption text re-renders in seconds without touching captures or framed intermediates.
- `verify` is fast and information-dense. Run it before `compose` after any config edit.
- `--dry-run` works on `stage`, `frame`, `passthrough`, `compose`, and `pipeline`. Plans without writing PNGs.
- Bundled gradient presets at `templates/presets/`: `mauve`, `royal-purple`, `apple-music`. Copy any one as a starting point.
- shotsmith deliberately doesn't replace `frames-cli`. They compose: `frames-cli` does device bezels (which it does well), shotsmith adds the gradient + caption layer.

## Repo

[github.com/xoloUno/shotsmith](https://github.com/xoloUno/shotsmith) — issues, full schema docs, CHANGELOG.
