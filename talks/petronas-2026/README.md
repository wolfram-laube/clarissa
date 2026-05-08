# SPE Workshop Kuala Lumpur 2026 — CLARISSA Talk

**Talk venue:** SPE Workshop, Kuala Lumpur 2026
**Discussion Leader:** Ian Matejka
**Speaker:** Wolfram Laube (CLARISSA / Blauweiss EDV)
**Date generated:** 2026-05-07 afternoon (~14:00–16:30 CEST)
**Submission ID:** TBD

This directory holds the **inputs** to the dual-track talk bundle that was
produced for the SPE Workshop. The bundle itself (PPTX deck, self-contained
narrated HTML player, speaker notes in DOCX/MD, MP3 audio per slide) is **not**
checked into git — it lives as a Drive deliverable.

## Architecture

```
inputs (here)                 engine                      outputs (Drive)
─────────────                 ──────                      ───────────────
clarissa_tagged.md   ──┐                                  ┌─→ deck.pptx
image_prompts/        ─┤                                  ├─→ player.html (26 MB)
diagrams/*.mmd        ─┼──→  tooling/claudeck   ────→     ├─→ speaker_notes.docx
voice_config.yaml     ─┤      (BW-ADR-016)                ├─→ speaker_notes.md
                       ─┘                                  └─→ slide_NN.mp3
```

The engine lives in
[`tooling/claudeck`](https://gitlab.com/wolfram_laube/blauweiss_llc/tooling/claudeck).
This directory is purely the use-case artifact — the talk-specific inputs
that drove this specific talk's generation.

## Reproduce

Once `tooling/claudeck` reaches Phase 1 (engine import + first release):

```bash
# from the claudeck repo, with this directory checked out alongside:
claudeck render \
    --template spe-workshop \
    --tagged-md projects/clarissa/talks/petronas-2026/clarissa_tagged.md \
    --voice-config projects/clarissa/talks/petronas-2026/voice_config.yaml \
    --output-dir /tmp/petronas-2026-bundle/
```

Until Phase 1 lands, the original sprint scripts in
`claudeck_sources_2026-05-07.zip` (Drive `BLAUWEISS-EDV-LLC/handovers/`) are
the reproduction recipe.

## Voice ID

ElevenLabs voice `Qn726hJmMrKY6uVQql7V` — Wolframs voice clone. Pronunciation
hints (phonetic-fix table) are part of the engine's prep stage. See
`tooling/claudeck/src/claudeck/stages/prep.py` (after Phase 0).

## Inputs in this directory (snapshot from sprint)

What is currently committed (rescued from the truncated Drive snapshot, see
the carve-out story in
[BW-ADR-016](https://gitlab.com/wolfram_laube/blauweiss_llc/ops/adr/-/blob/main/BW-ADR-016-claudeck-engine-repo.md)):

- `speaker_notes_snapshot/` — per-slide speaker text after phonetic
  substitutions (output of stage 3 prep, used as TTS input). 4 of 10 slides:
  04, 06, 08, 09.
- `image_prompts/` — DALL-E revised-prompts as returned by the API. 2 of 10
  slides: 01 (title), 06 (SPE benchmarks).

What is **missing** and gets committed once the user re-uploads the full
Mac-local sprint state to Drive:

- `clarissa_tagged.md` — the master tagged-MD source-of-truth
- `diagrams/architecture.mmd` and `diagrams/workflow.mmd`
- `image_prompts/` for slides 02, 03, 04, 05, 07, 08, 09, 10
- `speaker_notes_snapshot/` for slides 01, 02, 03, 05, 07, 10
- `voice_config.yaml` (formalized voice + phonetic-fix overrides for this
  talk specifically)

## Sprint-time issues (from the claudeck_sources HANDOVER, fix during reuse)

- Slide 4 of the HTML player: avatar PiP bottom-right slightly overlaps the
  architecture diagram bottom. Layout-tuning, ~10 min fix.
- DALL-E ignored "no human figures" constraint on slide 1 — produced a
  schematic silhouette. Cosmetically OK in context but the prompt needs
  strengthening (negative-prompt techniques, or move to GPT-Image-1 if it
  respects negative constraints better).
- DALL-E inserted small numeric decorations ("0.1", "8.30") on slide 6
  despite "no text" constraint. Reads as scale-tick decoration in the
  rendered output but technically a constraint violation.

## Bundle deliverables (Drive)

When the bundles are regenerated, they go to:
`Drive: BLAUWEISS-EDV-LLC/talks/petronas-2026/` (folder TBD).

Filename convention:
- `petronas-2026_<YYYY-MM-DD>_track-a.pptx` — conservative deck
- `petronas-2026_<YYYY-MM-DD>_player.html` — self-contained narrated replay
- `petronas-2026_<YYYY-MM-DD>_speaker_notes.docx`
- `petronas-2026_<YYYY-MM-DD>_speaker_notes.md`

## Cross-references

- Carve-out ADR: [`ops/adr` / BW-ADR-016](https://gitlab.com/wolfram_laube/blauweiss_llc/ops/adr/-/blob/main/BW-ADR-016-claudeck-engine-repo.md)
- Engine repo: [`tooling/claudeck`](https://gitlab.com/wolfram_laube/blauweiss_llc/tooling/claudeck)
- Phase 0 import: [`tooling/claudeck#2`](https://gitlab.com/wolfram_laube/blauweiss_llc/tooling/claudeck/-/work_items/2)
- This artifact-home issue: clarissa#147
- Sprint HANDOVER snapshot: Drive `BLAUWEISS-EDV-LLC/handovers/claudeck_sources_2026-05-07.zip`
  (fileId `1MZ7GXyUSh3R-7b71ANACTxsiV1Qi0mX7`)
