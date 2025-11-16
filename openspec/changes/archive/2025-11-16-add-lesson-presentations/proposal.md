## Why
Teachers routinely ask for ready-to-show materials after PocketMusec drafts a standards-aligned lesson. Right now they must manually turn the Markdown lesson into slides and speaker notes, which takes extra time and breaks the "ready-to-use" promise.

## What Changes
- Add a structured presentation document schema (slides + teacher scripts) that links to each generated lesson revision.
- Build a backend presentation generator that converts LessonDocument m2.0 outputs into slide decks, optionally enhancing copy through the existing Chutes LLM, and stores results in a dedicated `presentations` table (status + exports per lesson revision).
- Add asynchronous generation + stale tracking so lessons can auto-trigger deck creation, retry on failure, and indicate when slides are out-of-date.
- Expose APIs and UI affordances so teachers can request, preview, and download presentations, with automatic regeneration when lessons change.
- Lay groundwork for exporting decks (JSON/Markdown now, PPTX/PDF later) and surfacing teacher scripts alongside slide bullets.

## Impact
- Affected specs: new `lesson-presentations` capability (linked to `lesson-generation`).
- Affected code: PocketFlow lesson agent, lesson repository + new presentation repository/service, FastAPI lesson routes, React Drafts/Editor UI, future export utilities.
