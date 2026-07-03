# Continuity Auditor

## Purpose

Detect contradictions before readers do, and keep `continuity.md` current. Every
scene quietly establishes facts — names, dates, injuries, promises, who knows what.
This skill harvests those facts from new writing and checks them against what the
story has already established.

## Use when

- The shutdown phase of a session, after new words exist.
- A draft or scene is finished and its facts should be recorded.
- The writer asks "did I contradict something?" or "when did that happen?"
- Before a revision pass that might move events or change established facts.

## Inputs to read first

- `continuity.md` — the established record; treat it as the source of truth.
- The new or changed writing being audited, in `drafts/` or `scenes/`.
- `story_bible.md` — premise-level facts and the ending direction.
- The "Established facts" sections of relevant `characters/` and `world/` files.
- `active_state.md` — open loops already known.

## Process

1. Read the new material and extract every checkable fact, small or large.
2. Track these ten categories:
   - timeline events
   - character facts
   - relationships
   - location facts
   - world rules
   - promises made to the reader
   - unresolved questions
   - mysteries/clues
   - recurring objects
   - contradictions
3. Check each extracted fact against `continuity.md` and the story files.
4. Distinguish hard contradictions from soft drift — a detail that now reads
   differently but could still be reconciled.
5. Note reader promises: anything a reasonable reader now expects the story to
   pay off (a gun on the wall, a named fear, a mystery raised).
6. Propose updates: additions to `continuity.md`, plus "Established facts" additions
   in `characters/` and `world/` files. Propose first; let the writer confirm
   before any file changes.

## Output format

```text
Continuity updates to add:
Possible contradictions:
Open questions:
Reader promises:
Suggested updates to files:
```

Keep each entry to one line, with a pointer to where the fact appears (file and
scene). Empty sections say "none found" rather than disappearing.

## Things to avoid

- Rewriting prose to fix a contradiction — report it; the fix is a revision decision.
- Recording interpretation as fact. Log what the text establishes, not your reading.
- Drowning the writer in trivia. A fact matters if a future scene could break it.
- Silent updates to story files. Always show what you want to add and why.
- Treating ambiguity the writer intends — an unreliable narrator, an open mystery —
  as an error to correct.
