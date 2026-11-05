# Victoria 3 Mod project

## Scope and baseline
- Target Victoria 3 1.15.x. The installed baseline was verified as 1.15.0 on 2026-11-05.
- This project currently contains an empty mod framework. Do not add gameplay scripts, placeholder events, on_actions, decisions, localization or vanilla overrides unless the user requests a feature.
- `mod/` is the complete game-loadable and publishable root. Keep documentation, scripts, source art and developer configuration outside it.
- Preserve the stable mod ID `com.github.YangtzeMa.Vic-mod` across updates.
- Use `vicmod_` for future identifiers and unique filenames. Verify every API and scope against the installed version before using it.
- Read `docs/validation.md` for observed results and `docs/testing.md` for the required verification steps.

## Game and achievements
- Installed vanilla files are read-only references. Never edit installed game files, other mods, or existing user saves.
- Preserve achievement eligibility. Do not override achievement definitions, achievement rules, eligibility flags or cheat/achievement mechanisms.
- Do not claim that multiplayer synchronization or an unchanged checksum alone proves achievement compatibility.
- Use normal launch and achievement-allowed game rules for achievement acceptance. Keep debug sessions separate from that evidence.
- Avoid full-file overrides. On supported databases use explicit entry modes and verify injection/stacking semantics.
- When features are authorized, check the actual vanilla directory spelling, scope, localization format and 1.15 schema. Journal entries must use the current outcome system.
- Match vanilla encoding for future scripts; localization uses UTF-8 with BOM. Use ASCII paths and identifiers.

## Verification
- Run `python scripts/validate_mod.py` and `python scripts/package_mod.py` for framework changes.
- Run `git diff --check` before committing. Inspect both staged and unstaged changes.
- A new preview image must be visually inspected. Regeneration uses `scripts/make_thumbnail.py` and Pillow; other scripts use only the Python standard library.
- Changes to game-loaded metadata, art or content need relevant in-game checks before being called tested. Pure documentation changes need document/link review.
- Record exact game build, test scope and observed results in `docs/validation.md`. Do not manufacture evidence or turn a pending check into a pass.
- Do not add tests that merely repeat a low-impact implementation; keep the existing package-boundary checks meaningful.

## GitHub synchronization (already authorized by the user)
- The user requests timely GitHub synchronization after successful checks and any necessary game tests.
- After reviewing the diff and passing those checks, commit the scoped work and push to the configured upstream without asking again for routine permission.
- Preserve user edits. Do not reset, force-push, rewrite published history or silently include unrelated changes.
- Confirm the remote branch contains the exact local commit. Inspect the corresponding GitHub Actions result and fix failures.
- If a required check or authentication step is blocked, report the concrete blocker and keep unfinished work visible; do not describe the goal as completed.
- Do not publish to Steam Workshop without a user request to publish. Preparing an upload-ready package is authorized; creating a Workshop listing is a separate action.
- Never commit credentials, full original game files, local databases, user logs or saves. `.local/` and `dist/` are ignored.

## Local setup
- `scripts/link_local_mod.py` creates an idempotent directory junction using the actual Windows Documents path. It must never replace another directory or change system execution policies.
- Register/enable local mods using the Launcher UI. Do not patch the Launcher SQLite database.
- Launch options or playset changes made for tests must be recorded and restored where appropriate. Never overwrite an existing save during testing.
