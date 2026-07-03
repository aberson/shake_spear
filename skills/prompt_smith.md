# Prompt Smith

## Purpose

Turn a vague AI request into a well-formed prompt. "Make this scene better" is
a wish; a good prompt states context, task, constraints, output format, tone,
and what NOT to do. This skill builds those prompts — for use in this workshop
or any AI assistant — and helps the writer grow a personal prompt library.

## Use when

- The writer is about to ask an AI for help and the request is fuzzy.
- An AI response missed the mark and the writer suspects the prompt, not the
  model.
- A prompt that worked well is worth saving and generalizing (store it in the
  story's `prompts/` folder).
- Building a reusable prompt for a recurring task (e.g., "clue-audit my
  chapter" for a mystery).

## Inputs to read first

- The writer's rough request, as stated.
- Whatever the prompt will operate on (the draft passage, scene card, or file
  it targets).
- `story_bible.md` and any voice/taste profile — prompts should carry the
  story's tone and the writer's constraints with them.
- The story's `prompts/` folder, if it exists — a similar prompt may already
  be there to adapt.

## Process

1. Ask what a great response would look like. One question, concrete answer —
   this becomes the desired output format.
2. Draft the prompt with these seven parts (skip a part only when it truly
   adds nothing):
   - **Context** — what the AI needs to know: the story, the situation, which
     files to read first. Reference real files (`story_bible.md`,
     `active_state.md`, a scene card) rather than re-explaining them.
   - **Task** — one clearly named job. Two jobs = two prompts.
   - **Constraints** — length, scope, rules ("do not rewrite my sentences,"
     "feedback only," "keep my POV").
   - **Desired output format** — the exact shape of the answer: a labeled
     block, a table, three options, a diff of small edits.
   - **Tone** — how the response should sound (direct, warm, playful,
     clinical) and any taste-profile rules that apply.
   - **What not to do** — the failure modes to preempt: no generic praise,
     no imitating living authors, no spoiling the ending, no new characters.
   - **Examples when useful** — a short sample of the desired output, or one
     good/bad pair. One example beats three paragraphs of description.
3. Read the draft prompt as if you were the AI receiving it cold. Anything
   ambiguous, tighten. Anything the AI could not know, add to context.
4. Offer the finished prompt in a copy-ready block, plus one line on how to
   adapt it next time.
5. If it is likely to recur, suggest saving it to the story's `prompts/`
   folder with a descriptive filename.

## Output format

```text
What you asked for (restated in one line):
The prompt:
  Context:
  Task:
  Constraints:
  Desired output format:
  Tone:
  What not to do:
  Example (if useful):
Why this will work better (one or two sentences):
Save as (suggested prompts/ filename, if reusable):
```

## Things to avoid

- Prompt maximalism. Longer is not better; every line must earn its place, or
  the important constraints drown.
- Stacking several tasks into one prompt. Split them.
- Vague quality words as instructions ("make it better," "more engaging").
  Translate them into observable qualities ("shorter sentences in the chase,"
  "one concrete image per paragraph").
- Prompts that ask the AI to imitate living authors — encode taste as craft
  traits instead (see the voice and taste skill).
- Rebuilding from scratch what a shared skill already does. If the request
  matches an existing skill file, the best prompt is "read that skill and
  apply it."
