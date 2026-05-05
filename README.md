# shotsmith

App Store screenshot composer: gradients, captions, multi-locale. Takes
already-framed PNGs (from [`frames-cli`](https://github.com/viticci/frames-cli)) and produces
ASC-ready submission images. Pure Python, single dependency (Pillow), wraps
`frames-cli` for device bezels.

**v0.2.0** — iPhone 6.9" + iPad 13", multi-locale, manual-input staging.
Apple Watch is intentionally out of scope (see [Watch screenshots](#watch-screenshots)).

## TL;DR

A typical run takes raw screenshots from your simulator and emits
ASC-ready PNGs you can `fastlane deliver` upload directly. One command:

```bash
shotsmith pipeline --config fastlane/shotsmith/config.json
```

What it does, in order:

1. **verify** — checks the directory contract: confirms `raw/` is
   populated, flags orphan PNGs at the locale root, names any missing
   `manual_inputs` source files end-to-end.
2. **stage** — copies any declared manual-gesture captures (Live
   Activity, Home Screen widget, Control Center) from your tracked
   `manual-captures/` source into `raw/`. No-op if your config has
   no `manual_inputs` block.
3. **frame** — wraps `frames-cli` to draw Apple device bezels around
   each raw PNG. Reads from `raw/`, writes to `framed/`.
4. **compose** — overlays each framed PNG onto a gradient background,
   draws the caption (and optional subtitle) per locale, and writes
   the final ASC-ready PNG at exactly `1320×2868` (iPhone 6.9") or
   `2064×2752` (iPad 13") — Apple's required submission sizes.

Output flows like this:

```
raw simctl/UITest PNGs (in <input>/<locale>/<device>/raw/)
        ↓ shotsmith stage         (copies manual_inputs → raw/)
        ↓ shotsmith frame         (wraps frames-cli → framed/)
framed PNGs
        ↓ shotsmith compose       (gradient + caption per locale)
ASC-ready PNGs (in <output>/<locale>/<device>/)
        ↓ fastlane deliver
App Store Connect
```

Re-running `compose` alone (`--steps compose`) re-renders captioned PNGs
in seconds without re-capturing or re-framing — useful when you're
iterating on caption copy or gradient stops.

## Install

Requires [pipx](https://pipx.pypa.io/). On macOS: `brew install pipx` if
you don't have it.

```bash
pipx install git+https://github.com/xoloUno/shotsmith.git@v0.2.0
shotsmith --version
```

Or install from a clone (no pipx required):

```bash
git clone https://github.com/xoloUno/shotsmith.git
cd shotsmith
pip install -r requirements.txt
mkdir -p ~/.local/bin
ln -s "$(pwd)/bin/shotsmith" ~/.local/bin/shotsmith
shotsmith --version
```

## Requirements

- **Python ≥ 3.9** — any `python3` on PATH
- **Pillow** — pinned in `requirements.txt`; pulled in automatically by
  `pipx install`
- **[frames-cli](https://github.com/viticci/frames-cli)** on PATH — required
  for the `frame` and `pipeline` subcommands (shotsmith shells out to it
  for the device-bezel layer). One-time install:
  ```bash
  git clone https://github.com/viticci/frames-cli.git
  cd frames-cli && pip3 install Pillow
  mkdir -p ~/.local/bin
  ln -s "$(pwd)/frames" ~/.local/bin/frames
  frames setup   # downloads the Apple Frames asset pack (~40 MB)
  ```
  The `compose` and `verify` subcommands work without frames-cli — they
  read pre-framed PNGs from `framed/` directly. So if you're framing
  upstream of shotsmith, you can skip the frames-cli install.

> **Stock macOS note.** `/usr/bin/python3` (3.9) doesn't ship with Pillow.
> Running `./bin/shotsmith` from a clone without Pillow installed prints
> the exact `pip install` command for your active Python and exits.
> `pipx install` handles this for you. To use a specific interpreter:
> `/usr/local/bin/python3 ./bin/shotsmith --version`.

## Usage

Five subcommands. All take `--config`, `--locale` (repeatable), `--device`
(repeatable). With no filter flags, every (device × locale) combination runs.

```bash
# Stage manual_inputs sources into raw/ (no-op without manual_inputs config)
shotsmith stage    --config path/to/config.json

# Frame — wraps frames-cli, reads raw/, writes framed/
shotsmith frame    --config path/to/config.json
shotsmith frame    --config path/to/config.json --force   # re-frame existing

# Compose — reads framed/, writes ASC-ready PNGs
shotsmith compose  --config path/to/config.json
shotsmith compose  --config path/to/config.json --locale en-US --device iphone --dry-run

# Verify the directory contract
shotsmith verify   --config path/to/config.json

# Pipeline — verify, then stage + frame + compose end-to-end
shotsmith pipeline --config path/to/config.json
shotsmith pipeline --config path/to/config.json --steps capture,stage,frame,compose
shotsmith pipeline --config path/to/config.json --steps compose   # just re-render
```

`pipeline --steps` defaults to `stage,frame,compose`. Add `capture` if your
config defines a `pipeline.capture_hook`. The `stage` step is a no-op
without a `manual_inputs` block.

## Directory contract

Stable per-device layout. Two siblings under each device's configured input
path hold the intermediate and final-input PNGs:

```
<input.{device}>/<locale>/
├── raw/        ← capture output (XCUITest, simctl). NEVER overwritten.
└── framed/     ← frames-cli output. NEVER overwritten. shotsmith reads from here.

<output.{device}>/<locale>/   ← shotsmith composed output (per preset)
```

- Loose PNGs at the locale root are flagged by `shotsmith verify`.
- Re-rendering after a caption tweak is cheap (seconds; no re-capture or re-frame).
- Intermediates are never silently lost.

## Config

A `config.json` describes inputs, outputs, the gradient, the caption style,
and which locales to render. See `templates/config.example.json`:

```json
{
  "version": 2,
  "input":  { "iphone": "fastlane/screenshots/{locale}/iPhone 6.9\" Display" },
  "output": { "iphone": "fastlane/shotsmith/final/iphone/{locale}" },
  "pipeline": {
    "capture_hook": "scripts/capture-screenshots.sh",
    "frames_cli":   "frames",
    "verify_strict": true
  },
  "background": {
    "type": "linear-gradient",
    "stops": ["#FF5F6D", "#FFC371"],
    "angle": 180,
    "dither": 6
  },
  "caption": {
    "font": "New York Small Bold",
    "color": "#1B1B1B",
    "size_iphone": 115,
    "size_ipad": 130,
    "position": "footer",
    "padding_pct": 3.0,
    "max_lines": 2,
    "line_height": 1.15
  },
  "captions_file": "captions.json",
  "locales": ["en-US", "es-ES", "es-MX"]
}
```

Path templates use `{locale}` and resolve relative to the config file's
directory. `input.{device}` names the per-device root; `raw/` and `framed/`
subdirs underneath `<input>/<locale>/` are managed by shotsmith.

### Input mapping (optional)

Capture tools rarely write filenames matching what you want to ship —
XCUITest captures in implementation order, ASC displays alphabetically,
consumer order (which screen is the marketing hero?) is independent of
both. Mixing capture sources (XCUITest, simctl, manual gestures) means
each source has its own naming conventions.

`input_mapping` is a per-device dict translating **canonical filename**
(captions.json key) → **source filename** (whatever the capture tool wrote
into `raw/`). The frame step uses this lookup, so `framed/` always ends
up with canonical names matching captions.json.

```json
"input_mapping": {
  "iphone": {
    "01_LiveActivities.png":   "from_simctl_NotificationCenter.png",
    "02_HomeScreen.png":        "01_HomeScreen.png",
    "03_SymptomPicker.png":     "02_SymptomPicker.png",
    "04_SymptomDetail.png":     "03_SymptomDetail.png",
    "05_StopConfirmation.png":  "04_StopConfirmation.png",
    "06_ControlCenter.png":     "from_simctl_ControlCenter.png",
    "07_HomeScreenWidgets.png": "from_simctl_HomeScreen.png",
    "08_HomeScreenDark.png":    "05_HomeScreenDark.png"
  }
}
```

Without `input_mapping`, shotsmith uses identity — every PNG in `raw/`
becomes the same filename in `framed/`. Simple pipelines need no mapping.

### Manual inputs (optional)

Some screenshot surfaces — Live Activity stack, Home Screen widget,
Control Center pulled down — can't reliably be captured by XCUITest or
simctl scripts. They need a human gesture in the simulator. Any tool
that produces tracked PNGs in a per-locale directory works (the
[xoloUno iOS project playbook](https://github.com/xoloUno/claude-code-ios-playbook)
ships a `/capture-manual-surfaces` slash command for this); filenames
just need to match what `manual_inputs.{device}.files` declares.
Recapture once per release when the underlying UI changes.

The `manual_inputs` config block declares those sources. The `stage`
pipeline step copies them into `<raw_dir>/` before frame, and `verify`
reports a hard error when a declared source file is missing:

```json
"manual_inputs": {
  "iphone": {
    "source": "../manual-captures/{locale}",
    "files": [
      "90_LockScreen_LiveActivity.png",
      "91_HomeScreen_Widget.png",
      "92_ControlCenter.png"
    ]
  }
}
```

Per device. `source` is config-relative and supports `{locale}`. Files
typically use the conventional `90/91/92_` prefix; pair with
`input_mapping` to rename them to canonical caption keys at frame time.

**Why declare them in config rather than handle staging in your Fastfile/script?**

- **Single source of truth** — the contract for "what manual surfaces this
  project ships" lives next to the gradient and captions, not in glue code
  that drifts across projects.
- **End-to-end verify** — without `manual_inputs`, a missing manual capture
  surfaces only via `input_mapping` indirection ("source X.png not found in
  raw/"). With `manual_inputs`, `shotsmith verify` names the missing source
  file directly: `manual_inputs source(s) missing in /…/manual-captures/es-MX:
  91_HomeScreen_Widget.png`.
- **Composability** — re-stage without re-framing or re-composing when you
  recapture a single surface (`shotsmith stage --device iphone --locale es-MX`).

A config without `manual_inputs` makes both the `stage` step and the
subcommand a no-op.

### Pipeline block (optional)

Adds the `frame`, `verify`, and `pipeline` subcommands. Without it, only
`compose` works.

| Field | Default | Purpose |
|---|---|---|
| `capture_hook` | none | Path to your project's capture script. Called per (device, locale) with env vars `SHOTSMITH_DEVICE`, `SHOTSMITH_LOCALE`, `SHOTSMITH_RAW_DIR`. Hook writes raw PNGs into `$SHOTSMITH_RAW_DIR`. |
| `frames_cli` | `"frames"` | Command name for frames-cli on PATH. |
| `frames_args` | `[]` | Extra args appended to every frames-cli invocation. |
| `verify_strict` | `true` | Pipeline aborts on verify errors. Set `false` to downgrade errors to warnings. |

`background.dither` is an optional Gaussian-noise sigma applied to the
gradient — a subtle film-grain overlay that breaks up gradient banding on
8-bit displays. `0` (default) disables. Subtle range is `4..12`; higher
values produce visible grain. Inspired by Arc browser's gradient treatment.

### Captions file

A separate JSON keyed by input PNG filename, each entry keyed by language
code. Each value is either a **string** (caption only) or a **dict** with
`caption` and optional `subtitle` keys:

```json
{
  "01_HomeScreen.png": {
    "en":    { "caption": "Track everything", "subtitle": "in one place" },
    "es":    { "caption": "Todo en un solo lugar", "subtitle": "en tiempo real" },
    "es-MX": { "caption": "Todo en un solo lugar", "subtitle": "en tiempo real" }
  },
  "02_Detail.png": {
    "en":    "Drill down with one tap",
    "es":    "Profundiza con un solo toque"
  }
}
```

The string form is shorthand for `{"caption": "...", "subtitle": null}`.

shotsmith resolves locale → language fallback (`es-MX` → `es` → skip with
warning).

### Per-device caption + subtitle overrides

Each per-locale dict-form value can carry device-specific override keys
alongside the defaults. shotsmith tries `caption_X` first, falls back to
`caption`. Same for `subtitle_X` / `subtitle`. The two resolve
independently — override the caption for iPhone without touching subtitles.

```json
{
  "01_HomeScreen.png": {
    "en": {
      "caption":        "Track everything in one place",
      "caption_iphone": "Track everything\nin one place",
      "subtitle":       "in real time"
    }
  }
}
```

Common case: iPhone wants a forced line break for visual punch; iPad's
wider canvas reads better as a single line.

### Per-device padding (`padding_pct_iphone`, `padding_pct_ipad`)

`caption.padding_pct` is the default; optional `padding_pct_iphone` and
`padding_pct_ipad` overrides tighten or loosen the caption_area on a
specific device. Useful when one device's canvas proportions make the
default feel wrong — e.g. iPad's wider canvas can take less padding to
recover image_area height for the framed PNG.

```json
"caption": {
  "padding_pct":      3.5,
  "padding_pct_ipad": 2.0
}
```

### Forced line breaks

Use `\n` (literal newline in JSON) to force a break inside any caption
or subtitle. Each forced segment is independently word-wrapped to fit
the available width, sharing the `max_lines` budget across all segments.

```json
{
  "01.png": {
    "en": {
      "caption": "Track everything\nin one place",
      "subtitle": "in real time"
    }
  }
}
```

If total wrapped lines exceed `max_lines`, the last visible line is
truncated with an ellipsis. Empty segments (`\n\n`) are collapsed — to
add vertical gap, increase `subtitle.spacing_pct`.

### Subtitle (optional)

Add a `subtitle` block alongside `caption` to enable a smaller secondary
line beneath each caption. Has its own font, color, sizes, and max
lines. `spacing_pct` controls the gap between caption and subtitle (as
a percent of canvas height).

```json
"subtitle": {
  "font": "New York Small Regular",
  "color": "#FFFFFF",
  "size_iphone": 60,
  "size_ipad": 70,
  "max_lines": 1,
  "line_height": 1.15,
  "spacing_pct": 1.5
}
```

If the `subtitle` block is omitted, no subtitle is rendered. If present,
it activates per image based on the caption-file value: dict-form
entries with a non-empty `subtitle` get one; string-form or
dict-form-without-subtitle entries get caption-only layout.

### Font resolution

Two ways to specify the font in `caption.font`:

1. **Family + style name** — e.g. `"New York Small Bold"`. shotsmith
   searches `/System/Library/Fonts`, `/Library/Fonts`, and
   `~/Library/Fonts` using Apple's optical-size + weight naming
   convention (`NewYorkSmall-Bold.otf`).
2. **Direct path** — anything containing `/` or ending in
   `.ttf`/`.otf`/`.ttc` is used verbatim.

If the family-name lookup fails, shotsmith prints the directories
searched and patterns tried.

## Devices

| Key | ASC slot | Default caption size |
|---|---|---|
| `iphone` | iPhone 6.9" Display (1320 × 2868) | 115 |
| `ipad`   | iPad 13" Display (2064 × 2752) | 130 |

These are Apple's required ASC submission sizes. Apple auto-scales them
down to smaller iPhone/iPad slots — uploading 6.9" + 13" covers every
device class. See [Apple's screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/)
for the full ASC matrix.

## Layout model

For the App Store convention (`position: "footer"`):

```
+---------------------------------+ y=0
|                                 |
|   [framed PNG, fitted into      |
|    image area, centered]        |
|                                 |
+---------------------------------+ y=image_area_height
|                                 |
|   <Caption, wrapped, centered>  |
|   <Subtitle, optional>          |
|                                 |
+---------------------------------+ y=canvas_height
```

```
caption_area_height
  = (caption_font × line_height × caption_max_lines)
  + (subtitle_font × subtitle_line_height × subtitle_max_lines)  [if subtitle]
  + (canvas_height × subtitle_spacing_pct / 100)                 [if subtitle]
  + (2 × canvas_height × caption_padding_pct / 100)
image_area_height = canvas_height − caption_area_height
```

The framed PNG is scaled to fit `image_area_height` while preserving
aspect ratio. The text block (caption + spacing + subtitle) is
vertically centered within `caption_area_height`.

## Watch screenshots

shotsmith never composes Apple Watch screenshots. ASC submissions go
straight from `simctl io screenshot` (raw 422×514 native for Ultra 3)
to the upload payload — no framing, no gradient, no caption. The watch
hardware's display corner-radius would clip added art at viewing time.

For non-ASC marketing needs (web pages, press kits), run `frames-cli`
on the raw capture rather than maintaining a separate composition
pipeline.

## Bundled gradient presets

Three palettes selected during shotsmith's early development, saved at
[templates/presets/](templates/presets/):

- **mauve** — `#A56FB4` → `#FF6B5C` (soft dusty purple → coral)
- **royal-purple** — `#6B4FBB` → `#FF6B5C` (cool deep violet → coral)
- **apple-music** — `#FA2D48` → `#FF6B5C` (deep red → coral, no purple)

All share `dither: 30`, white captions, `New York Small Bold`. See
[templates/presets/README.md](templates/presets/README.md).

## Tests

```bash
pip install -r requirements.txt pytest
pytest tests/
```

The end-to-end test synthesizes a fake framed PNG, runs the full compose
pipeline, and asserts output dimensions. Output quality is validated by
visual inspection during real ASC submission rounds; golden-image diffs
are not used.

## Claude Code skill

Standalone skill at `skill/SKILL.md` gives any Claude Code session in
any project native awareness of shotsmith's schema, subcommands, and
directory contract. Install once:

```bash
mkdir -p ~/.claude/skills/shotsmith
ln -s "$(pwd)/skill/SKILL.md" ~/.claude/skills/shotsmith/SKILL.md
```

## Roadmap

- **PyPI publication** — install command currently uses
  `pipx install git+https://...`; PyPI release once the schema settles
  via a second project consumer or external interest surfaces.
- **Schema v3** — TBD; no breaking changes planned for v0.2.x. Likely
  drivers: a non-Latin script that exposes shaping gaps in Pillow vs.
  CoreText, or a project layout that doesn't fit the per-device
  input/output template model.

## Why not appshot?

shotsmith's predecessor pipeline used `appshot-cli` for caption +
gradient composition, but the install required a 22-line monkey-patch
(`patch-appshot.sh`) to override the built-in iPhone/iPad font-size
strategy — captions rendered illegibly small at ASC sizes otherwise.
The patch had to be re-applied after every `npm install -g
appshot-cli`. shotsmith eliminates the patch by exposing font size
directly in the config.

## Why keep frames-cli?

[`frames-cli`](https://github.com/viticci/frames-cli) (viticci's port
of MacStories' Apple Frames) handles the device bezel layer well and
is independently maintained. shotsmith takes its output as input and
adds the gradient + caption — separation of concerns.
