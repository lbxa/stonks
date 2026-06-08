---
name: image-pipeline-visual-smoke
description: Use when asked to visually test, smoke test, compare, inspect, or generate concrete outputs from the VALUE_ALPHA image pipeline. Covers image-lib/native transforms, watermarking, PhotoRoom background removal, Gemini image analysis, recovered R2/source images, timestamped output folders, run-summary.jsonl files, and manual visual review batches.
---

# Image Pipeline Visual Smoke

Use this when the user needs concrete image outputs they can inspect, not just unit-test results. Keep runs timestamped, reproducible, and explicit about which external services were reachable.

## Workflow

1. Confirm the exact image set and input root. Common roots:
   - `libs/image-lib/native/image-transformer/tests/assets`
   - `libs/image-lib/data/...`
   - recovered R2/source image folders
2. Check required environment before running:
   - `PHOTOROOM_API_KEY` when background removal can call PhotoRoom
   - R2 credentials only when downloading, uploading, or verifying bucket objects
3. Create a timestamped output root under `libs/image-lib/data`, for example:
   - `ad-hoc-analysis-native-tests-YYYYMMDD-HHMMSS`
   - `ad-hoc-analysis-native-normals-YYYYMMDD-HHMMSS`
4. Run from the VALUE_ALPHA repo root so relative paths match package scripts.
5. For each image, run the narrowest existing command, usually:

```sh
bun run --cwd libs/image-lib run:native-transform -- \
  --input "./native/image-transformer/tests/assets/<file>" \
  --watermark "./assets/watermark.png" \
  --output-dir "./data/<run>/<stem>"
```

6. Write `run-summary.jsonl` with one row per input. Include:
   - `image`
   - `ok`
   - compact `scene_analysis.json` when present
   - failure text when the command fails
7. After the run, list the output root, summary path, succeeded images, failed images, and the first actionable failure cause.

## Failure Handling

- If PhotoRoom calls fail because network is sandboxed, rerun only the affected set with the smallest approval scope.
- If an env var is missing, state that before running and do not imply the pipeline failed.
- If a batch is quiet for a long time, prefer a progress-printing rerun for the next attempt.
- Do not delete old analysis folders unless the user explicitly asks; stale visual artifacts can still be useful.

## Reporting

Return:

```text
Output root: libs/image-lib/data/<run>
Summary: libs/image-lib/data/<run>/run-summary.jsonl
Succeeded: <n> (<names or range>)
Failed: <n> (<name>: <reason>)
Next check: <exact file or command to inspect>
```

Mention whether the run used real external APIs or only local deterministic analysis.
