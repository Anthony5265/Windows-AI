# Windows AI — MEGA PROMPT (NO-REMOTE MODE)

Read `codex/manifest.json` → open `"entry"`. Load `codex/STATE.json`.

Operate WITHOUT Git push/PR. For every TODO task:
  1) Implement per spec (code + tests + docs).
  2) Update `codex/STATE.json` with `"status":"done","commit":"local-<timestamp>"`.
  3) Stage ALL new/changed files under `PATCH_OUT/` preserving paths.
  4) Append a bullet to `PATCH_OUT/PATCHPLAN.md` describing the change.

After final task:
  • Write `codex/HISTORY/<timestamp>.md` and include it in `PATCH_OUT/`.
  • Create `PATCH_OUT/APPLY.md` with upload instructions.
  • Zip `PATCH_OUT/` → `windowsai_full_patch.zip`.
  • Print Base64 between markers:
      -----BEGIN WINDOWS AI PATCH ZIP-----
      <base64>
      -----END WINDOWS AI PATCH ZIP-----
Stop after printing the ZIP.
