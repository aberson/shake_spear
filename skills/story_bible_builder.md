# Story Bible Builder

## Purpose

Help the writer build a compact story bible: one page that captures what this
story is, who it is about, what is at stake, and how it should feel. The bible
is a working tool, not homework. It exists so future sessions (and future AI
assistants) can orient in under a minute, and so drift gets caught early.

## Use when

- A new story project was just created and `story_bible.md` is still empty.
- The writer says "I have an idea but I don't know what the story is yet."
- Mid-draft, when the story has changed shape and the bible no longer matches
  what is actually on the page.
- Before a revision pass, to re-anchor on premise, tone, and themes.

## Inputs to read first

- `story_bible.md` — the file you are building or updating; note what is
  already filled in and what the frontmatter says (title, genre, audience, mode).
- `active_state.md` — where the writer actually is right now.
- Any existing material: `scenes/`, `characters/`, `drafts/` — even one rough
  scene tells you more about the real story than a blank page does.
- `decisions.md` — decisions already made are settled; do not reopen them.

## Process

1. Work conversationally, one or two questions at a time. Never send the whole
   questionnaire at once.
2. Cover these fifteen areas, in whatever order the conversation makes natural:
   title, genre, audience, premise, tone, main character, main want, main fear,
   central conflict, antagonist/opposition, setting, themes, ending direction,
   things to avoid, open questions.
3. Push for specificity. "A kid who wants to fit in" is a start; "a kid who
   wants to sit at the loud table but panics when anyone looks at her" is a
   story. Offer two or three concrete options when the writer is stuck, then
   let them choose or counter.
4. Keep every answer short. A premise is one sentence. A theme is a phrase.
   If an answer runs long, help compress it.
5. It is fine to leave sections blank. Anything genuinely undecided goes under
   open questions rather than getting a filler answer.
6. Write the results into `story_bible.md` under its existing headings (see
   Output format), and fill the `audience:` frontmatter field once known.
7. Read the finished bible back as a whole and flag any two sections that
   contradict each other (a cozy tone with an annihilation-stakes conflict, say)
   so the writer can resolve or embrace the tension deliberately.

## Output format

Fill the story bible's own headings — the template in this workshop uses:

```text
One-sentence premise:        (premise)
What kind of story is this?: (genre, audience, tone in a sentence or two)
Main character:              (who, in one or two lines)
What they want:              (main want)
What they fear:              (main fear)
Central conflict:            (what stands against the want; name the
                              antagonist or opposition here)
Setting:                     (where and when, plus what makes it particular)
Tone:                        (three to five adjectives or a comparison to a feeling)
Themes:                      (two or three phrases, not essays)
Ending direction:            (not the ending itself — the direction it leans)
Things this story should avoid:  (the writer's do-not list)
Open questions:              (everything still undecided, welcome here)
```

Title, genre, and audience live in the file's frontmatter; confirm they match
what the conversation settled on.

## Things to avoid

- Turning this into a forty-question intake form. Momentum beats completeness.
- Writing the bible for the writer. Ask, suggest options, and compress — but
  the choices are theirs.
- Padding sections with generic filler ("themes: love, loss, hope") just to
  fill the page. A blank section plus an open question is more honest.
- Locking the ending. "Ending direction" is a compass heading, not a spoiler
  the writer must now obey.
- Overwriting an existing bible wholesale. Update the sections that changed
  and leave the rest byte-for-byte alone.
