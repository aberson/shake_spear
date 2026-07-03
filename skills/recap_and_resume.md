# Recap and Resume

## Purpose

Make stopping cheap and resuming instant. This is the stop/resume ritual: at
the end of a session, capture the story's live state in a fixed short block;
at the start of the next one, read that block and be writing again within a
few minutes — even if "next" turns out to be three weeks away.

## Use when

- The last five minutes of any writing session (the shutdown step).
- The writer says "I need to stop," "save my place," or "where was I?"
- Returning to a story after any gap and needing to re-enter fast.
- Before switching between story projects, so each one is left resumable.

## Inputs to read first

When stopping:

- What was just written or changed this session (the writer can tell you, or
  check the newest file in `sessions/` and recent changes in `drafts/`).
- `active_state.md` — the current recorded state you are about to update.

When resuming:

- `active_state.md` — the recap block is the entry point; read it first.
- `continuity.md` and the latest session log in `sessions/`, if more context
  is needed.
- Only then, if necessary, the current scene card or draft.

## Process

Stopping (about five minutes):

1. Ask the writer at most two questions: "what did you write or change?" and
   "what still feels alive?" Fill the rest from the files yourself.
2. Produce the recap block in the exact Output format below. Keep every line
   to one or two sentences — this is a bookmark, not a summary of the work.
3. Be concrete in "One tiny next action": "write the first two lines of the
   kitchen argument" resumes a session; "continue chapter 3" does not.
4. Save it into `active_state.md` (the `ss recap` command maintains a marker
   block there for exactly this). Never destructively summarize or alter the
   drafts themselves.
5. Note any continuity facts the session established and suggest adding them
   to `continuity.md`.

Resuming (about three minutes):

1. Read the recap block aloud back to the writer, briefly.
2. Confirm or refresh "One tiny next action" — if it no longer appeals,
   propose one equally tiny alternative, not a plan.
3. Start the session there. Do not re-litigate the whole story before any new
   words happen.

## Output format

Produce exactly this block:

```text
Current state:
What I wrote last:
What is emotionally alive:
Open loops:
Files changed:
Best next scene:
One tiny next action:
```

Line guide: "Current state" is where the story stands in one sentence;
"Open loops" are unresolved threads (bulleted, short); "Files changed" lists
paths touched this session; "Best next scene" is the scene most worth writing
next and why in a phrase; "One tiny next action" is doable in under ten
minutes.

## Things to avoid

- Long recaps. Past ten lines it stops being a bookmark and becomes work to
  read; momentum dies in the summary.
- Vague next actions ("keep going," "work on the middle"). Tiny and concrete
  or it will not restart the writer.
- Rewriting `active_state.md` outside the recap block, or summarizing drafts
  destructively. The writer's own notes are theirs.
- Guilt framing ("it's been 3 weeks..."). Gaps are normal; the ritual exists
  so gaps do not cost anything.
- Turning resume into review. Read the block, confirm the action, write.
