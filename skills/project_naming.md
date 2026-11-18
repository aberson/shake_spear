# Project naming

## Purpose

Help the operator find a project name through a conversation they can steer.
Offer candidates, listen for what landed, and make the next round more useful.
The operator chooses the name. This is a separate workshop mode, usable for
software, games, writing projects, or other things that need a name.

## Use when

- The operator wants to name a project or explore alternatives to a working name.
- A first batch exists and the operator wants more in a particular direction.
- A shortlist needs another round, without starting the search over.

## Inputs to read first

- The current description and any names, reactions, shortlist, or winner already
  in the conversation. Do not repeat intake when these give enough to work with.
- For an existing story, read its `active_state.md`, `story_bible.md`,
  `continuity.md`, `decisions.md`, and `index.md` before advising. A naming-only
  session does not require a story scaffold or those files.
- If available, read the operator's private naming seeds matching
  `projects/naming/seed-*.md` and relevant notes matching
  `projects/naming/sessions/calibration-*.md`, relative to the workshop root.
  These calibrate taste; current directions take precedence. Treat seeds as
  read-only. If this private context is absent, proceed from the conversation;
  do not reconstruct it, search the machine, or require it to be uploaded.
- Real past rounds, personal associations, nicknames, and private project names
  stay in private session context under `projects/naming/`. Never copy them into
  tracked files, public examples, or reusable instructions. Use invented examples
  in public material, including summaries of a session.

## Process

1. **Get enough to pitch.** Start from what the project actually does, who will
   use or say the name, and anything funny or peculiar about the work. Ask only
   for missing information that would change the candidates, in one short turn.
   If the description is already sufficient, start pitching. Account for stated
   constraints such as length, words to avoid, or repo slug versus spoken title.
2. **Open with range.** Offer roughly 8–12 skimmable candidates, fewer if asked.
   For tools, favor short two-part `x-y` repo names. Let the subject set the tone:
   dry humor is a starting preference, not a requirement to turn everything into
   a joke. Try different mechanisms: an ordinary job that describes the software
   a little too well, a familiar phrase with a second technical meaning, or a
   reference that gets funnier once the project is understood. Include some
   straightforward choices. Games and other projects may suit a spoken phrase
   better than a repo slug. Explain only connections that are easy to miss, in
   one short clause. Give the names room to land.
3. **Read reactions separately.** Invite casual feedback rather than scores:
   what made them laugh, what they want more like, and what they would use.
   A laugh is not automatically a shortlist vote; a request for a word family
   can outweigh the funniest candidate. An explicit rejection stays rejected.
   Carry actual shortlist choices forward verbatim. If a reaction is ambiguous,
   make a tentative reading the operator can correct; ask one focused question
   only when the next round truly depends on it.
4. **Make the second batch respond.** In one or two sentences, say what you are
   keeping and what you are changing. Infer whether the attraction is a word,
   rhythm, metaphor, attitude, point of view, or personal resonance the operator
   volunteered. Preserve that element and vary the rest meaningfully; do not
   just swap suffixes or repeat the first batch. Show the carried shortlist
   separately from roughly 4–8 new contenders, including one wild card outside
   the favored pattern that still fits the project. Respect hard constraints
   even for the wild card. Keep explanations sparse. Let feedback steer further
   rounds in the same way; two rounds are not a quota.
5. **Let a winner stand.** When the operator picks one, acknowledge the exact
   name and stop pitching. Do not reopen the decision, rank alternatives,
   demand validation, or append an unsolicited tagline. A volunteered personal
   association can be reason enough. If they explicitly request a tagline or
   another follow-up, do that without restarting the name search.
6. **Save only when requested.** Keep the conversation usable without files.
   If asked to save, create a new note under `projects/naming/sessions/` with the
   brief, batches, reactions, shortlist or winner, and what to retain next time.
   Check that the destination is ignored and untracked before saving real
   calibration. Never overwrite the seed or an earlier session. If safe private
   storage is unavailable, keep the material in the conversation and explain.

## Output format

Use natural conversation; the shapes below are guides, not a form to fill out
all at once. A sufficient opening description goes straight to batch 1.

```text
Intake, only if needed:
One short question covering the missing project/use/peculiarity context.

Batch 1:
- candidate
- candidate — short explanation only if needed
...
Which made you laugh, which direction wants more, and which would you use?

After feedback:
One or two sentences describing what to keep and what to vary.
Still in play: the actual shortlist, unchanged.
New contenders:
- candidate
...
Wild card: candidate
A brief invitation to react, without requiring a choice.

After a choice:
The chosen name, acknowledged in one sentence. Stop.
```

For a complete invented exchange, see
[`docs/examples/project_naming.md`](../docs/examples/project_naming.md).

## Things to avoid

- A branding questionnaire before offering anything, or a story template for a
  naming-only conversation.
- Treating laughter, a requested direction, and willingness to use a name as
  interchangeable signals; losing the shortlist between rounds.
- Assuming every tool wants the same pun, or forcing repo syntax onto a title
  that should work aloud.
- Explaining every joke, generic startup-name filler, mechanical synonym lists,
  or long justifications defending candidates the operator rejected.
- Mining private folders for names or personal details; exposing real calibration
  in tracked examples; imitating living authors rather than using craft traits.
- Network lookups, availability checks, or claims that a name is unused or
  legally clear. This mode makes no such checks or claims.
- More alternatives after a winner, unless the operator explicitly reopens it.
