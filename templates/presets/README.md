# Gradient presets

Three palettes carried forward from shotsmith's early-development gradient
batch comparison. Each is a complete config that runs against the bundled
test fixtures so the rendered samples can be re-inspected.

| Preset | Top | Bottom | Notes |
|---|---|---|---|
| [mauve.json](mauve.json) | `#A56FB4` | `#FF6B5C` | Soft dusty purple → coral. Most editorial. |
| [royal-purple.json](royal-purple.json) | `#6B4FBB` | `#FF6B5C` | Cool deep violet → coral. Most contrast. |
| [apple-music.json](apple-music.json) | `#FA2D48` | `#FF6B5C` | Deep red → coral, no purple. Most cohesive. |

All three share:
- `dither: 30` — Arc-style film grain
- `caption.color: #FFFFFF` — white reads against all three top stops
- `font: "New York Small Bold"` at 115px iPhone / 130px iPad
- `angle: 180` (top → bottom)

## Re-rendering

```bash
shotsmith compose --config templates/presets/mauve.json --device iphone
open tests/fixtures/sample-output/presets/mauve/iphone/en-US/01_HomeScreen.png
```

## Adopting a preset in your project

Copy the chosen preset's `background` and `caption` blocks into your
project's `fastlane/shotsmith/config.json`, then point `input` and
`output` at your project's actual paths. The preset's gradient stops,
font, and dither value give you a tested starting point — tune from
there.
