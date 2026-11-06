# Huoshen asset validation

## Current revision: v25

Checked: 2026-11-07. The v25 package supplies `pet.json`, `preview.webp`, and `spritesheet.webp`; its pet ID remains `huoshen`. The original reference and character brief are retained. The map's `sourceCommit` is the earlier original-atlas audit baseline, not a claim that v25 was present there. The current atlas is identified by its SHA-256 below.

| File | SHA-256 |
| --- | --- |
| pet.json | `1a5b00c99776d90ec202e931c4b65ca5351680b38b9146a182ed16a464f564b5` |
| preview.webp | `39b3927c321444f9da7f530b6195bb0a35e0dee3a04ea18c81a253e9311aabbb` |
| spritesheet.webp | `3ccac75872cfee5db23801449a53ac4dbc1060afb5d9f5ba26fb891ffefd5578` |

The v25 atlas decodes as single-frame RGBA WebP at 1536×2288. The current [validation.json](validation.json) records 74 nonempty and 14 empty cells and one failure: row 0, column 6 is nonempty although the inspected host uses idle columns 0–5. Five validator tests pass. The prior artwork findings below describe the original atlas and have not been revalidated against v25. This update does not establish a v25 visual acceptance or live host-event test.

## Historical audit: original atlas

The following records the original baseline and its prior inspection, not the current v25 asset status.

Checked: 2026-11-07. Baseline: `c8adb487a0d7df37b491e33dfde8528a663d9755`. This report separates static checks, preview, artwork and host behavior. No asset was modified.

## Baseline files and SHA-256

| File at baseline | SHA-256 |
| --- | --- |
| README.md | `7436b29d058a80e9cf8d77f3f040b8fc81891447057c5b60e74b2088793f25a5` |
| pet-brief.md | `75a2994cb0189557e051911eaff54e20ab42e61cb6e1ed19c9f7418d64b14ecc` |
| pet.json | `b287f9352eb9962641d2a19cc997473dbbb6be99526da7dc968edcec4451cc87` |
| main-reference.png | `418389eb8de97269dcdfe153a05771ba6c3edcd81a7e07fb76fef4d996d8a101` |
| preview.webp | `f3343e9731c66272b38f4b2a1fe5ba8cee3a69b2684c4dd97d1676be78c8c093` |
| spritesheet.webp | `a090ea73945449387c6cfaaa26c5defc956365cc4cdda7e086d6dc0c92224a32` |

At that audit, README had been extended and the other five original files remained unchanged. The v25 update has since replaced the manifest, preview and atlas. The baseline atlas is single-frame WebP, 1536×2288, RGBA, divided into 8×11 cells of 192×208 pixels.

## Protocol evidence and scope

The inspected local application is `/Applications/ChatGPT.app`, bundle identifier `com.openai.codex`, version 26.1029.61003, build 24614. Its bundled `Contents/Resources/skills/skills/.curated/hatch-pet/references/animation-rows.md` (SHA-256 `d27b08d599e73cf6a65a03d2b8ad49e9ad408e18292636164e7b2d2f1815615f`) specifies the v2 dimensions, row and column counts and direction layout. Its `Contents/Resources/app.asar` (SHA-256 `0c951258b7ab381ec601045ffb02159e53f424548dda18e6a4dcfd126557383b`), module `DRpS` in `webview/assets/async/24191.589dcc9878.js`, contains the corresponding playback logic. This is evidence for that build, not proof for other builds or a live event test.

Rows 0–8 use idle 6, running-right 8, running-left 8, waving 4, jumping 5, failed 8, waiting 6, running 6 and review 6 frames. The local implementation multiplies the documented idle base durations by six for normal idle playback; the map records those resulting durations. Reduced motion uses the first frame. Non-idle states loop when the caller requests looping; otherwise the implementation plays three repetitions and returns to idle. The map leaves `loop` null because the caller's choice depends on context. Rows 9–10 are 16 clockwise pointer directions starting at up; they are kept outside the task-state map. Their individual artwork semantics have not been validated.

The source specification's alpha-based idle candidate had seven nonempty cells. The local implementation uses only columns 0–5; column 6 is not played. The bundled v2 guidance requires unused cells to be transparent. No change was made to the atlas. The `verified` status in the map refers only to row, frame range and timing in the inspected implementation, not artwork acceptance, event routing or compatibility with other versions.

## Static validation

Run `python tools/validate_assets.py` in a Python 3.9+ environment with Pillow. The original-atlas result was **failed**, exit 1, 74 nonempty and 14 empty cells. The only reported error is `unexpected non-empty cell 0,6` (zero-based row, column). No alpha bounding box touches a cell boundary. This is not a pixel-by-pixel determination of detached fragments, shadows, lighting or visual correctness.

Five automated tests pass, including out-of-range, empty assigned cell, unexpected nonempty cell, boundary contact, overlap, hash and duration mismatch failures. Their fixtures do not replace validation of the real atlas.

## Preview and artwork

The local browser preview loaded both canvas sizes and switched all nine states and both direction rows. Pause, single-step, background and target-size controls were exercised. Preview speed defaults to an adjustable 8 FPS and is not the host timing. Previewing does not prove host integration. The current map intentionally excludes idle column 6 to match the inspected implementation; the static result records that cell separately.

Static contact sheets of rows 0–8 were inspected at original size on checker, black and white backgrounds, including the unused idle cell. The large striped horns, small horns, orange body, black wings, collar and smoky tail are broadly recognizable; this is not a precise identity-lock pass for every frame. In `running-left`, row 2 column 2 has a flame detached from the body, and column 5 has another detached flame fragment. Row 2 columns 0 and 7 show straight cut-off shapes inside the cell, and green pixels are visible around the wing root in column 5 and hand in column 7. These locations require artwork review and correction; the atlas was not edited. A 96px white-background browser view was checked for row 2 column 2, not all states and backgrounds.

Artwork acceptance is **not complete**: the nine states have not been watched for three full loops or a full one-shot action, nor assessed against all ten identity locks at target size. Jump anticipation/return, failed expression and flame dimming, continuity, flicker, shadow, color and direction-pose correctness remain to be reviewed. Do not treat alpha or browser loading as a visual pass.

## Host event testing

The implementation and accompanying row reference were inspected, but the actual host has not been exercised through task execution → waiting for input → resume → review → idle, failure, left/right movement, greeting, or hover entry/exit. Installation/selection and live event subscriptions or timer cleanup were not tested in this run. No host integration was added or claimed. Event triggering and behavior must be checked in the actual target desktop build before declaring runtime acceptance.
