# Mystery Mode

## Purpose

Help write mystery stories that play fair: a puzzle the reader could solve,
clues planted in plain sight, red herrings that mislead honestly, and a reveal
that feels inevitable in hindsight. This mode adds bookkeeping — a mystery is
a machine, and every gear must be tracked.

## Use when

- The story is a mystery (check `story_bible.md`), or the session type is
  `mystery`.
- Planning the crime, the suspect web, or the clue schedule.
- Drafting or revising an investigation, interrogation, or reveal scene.
- Auditing a draft for fair-play holes ("could an attentive reader have
  gotten there?").

## Inputs to read first

- `story_bible.md` — the central question and ending direction.
- `continuity.md` — the running record of established facts; in a mystery
  this doubles as the clue ledger.
- `characters/` profiles — suspects' wants, secrets, and established alibis.
- `scenes/` cards and `drafts/` for what the reader has actually seen so far
  (not what the writer merely knows).

## Process

1. Establish or restate the spine: what is the **crime or central question**
   this story turns on? Everything else hangs off it.
2. Maintain the eleven tracked elements. For each, know the current state and
   where it is recorded (usually `continuity.md`):
   - **Crime or central question** — what happened, and what the story asks.
   - **Suspects** — everyone who plausibly could have done it.
   - **Motives** — why each suspect might have.
   - **Means** — how each suspect could have.
   - **Opportunity** — when and where each suspect could have.
   - **Clues** — every real clue: what it proves, and the scene where it is
     planted.
   - **Red herrings** — every false trail: what it falsely suggests, and how
     it is honestly explained by the end.
   - **Reveals** — the schedule of what the reader learns, in order.
   - **Fair-play clue placement** — each clue the solution depends on appears
     on the page before the reveal, visible to an attentive reader.
   - **Timeline** — the true sequence of events (what actually happened) vs
     the order the reader discovers it.
   - **Detective knowledge vs reader knowledge** — at any point, what the
     detective knows, what the reader knows, and the deliberate gap between
     them. Track it per scene; this gap IS the suspense.
3. When planning a scene, state what it adds to the machine: which clue is
   planted, which suspect gains or loses standing, what gap opens or closes.
4. When auditing, walk the solution backward: for each fact the reveal needs,
   find the scene that planted it. Anything unplanted is a fair-play hole —
   list it with a suggested planting spot.
5. Propose `continuity.md` updates for anything new the draft established.
   Keep motive/means/opportunity per suspect current as scenes land.

## Output format

```text
Central question:
Suspect table (suspect / motive / means / opportunity / current standing):
Clues planted so far (clue -> what it proves -> scene):
Red herrings active (herring -> what it falsely suggests -> eventual honest explanation):
Reveal schedule (what the reader learns, in order):
Fair-play holes (solution facts not yet planted, with suggested scenes):
Timeline check (true order vs discovery order — contradictions, if any):
Knowledge gap right now (detective knows / reader knows / the gap):
Continuity updates to record:
```

## Things to avoid

- Withholding a solution-critical clue from the reader and calling it
  suspense. That is cheating, and readers know.
- Red herrings that are never honestly resolved — a false trail must get a
  true explanation by the end.
- A culprit whose motive, means, or opportunity was never established on the
  page before the reveal.
- Detectives who solve by unshared intuition or an unmentioned lab result.
- Letting the bookkeeping smother the prose. Track the machine in
  `continuity.md`, then write scenes about people; the reader should feel the
  gears, not see the spreadsheet.
