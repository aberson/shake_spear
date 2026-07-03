# Seed Prompt for Claude: AI-Assisted Creative Writing Workshop

Use this prompt in Claude from an empty folder in VS Code. The goal is to create a practical, markdown-first creative writing workspace that supports immersive writing sessions, quick feedback, story continuity, character/world organization, and multiple separate story subprojects that share the same tools.

---

## 1. Project goal

Create a VS Code-friendly project called `shake_spear`.

This project should help me practice creative writing with AI assistance. I am not trying to generate a bestseller or outsource the whole book. I want a reliable workspace for:

- immersive writing sessions
- quick feedback loops
- scene planning
- revision passes
- character organization
- worldbuilding organization
- continuity tracking
- reusable AI prompt “skills”
- separate story subprojects such as `story_001`, `kids_space_bakery`, or `no_one_dies_here_usually`

The important design idea is:

> There should be one overarching writing workshop with shared tools and skills, but each story should be its own folder that I can open directly with `code .` and still have enough local context to work comfortably.

For example:

```text
shake_spear/
  skills/
  templates/
  scripts/
  projects/
    kids_space_bakery/
    no_one_dies_here_usually/
    robots_are_people_too/
```

If I open `shake_spear/projects/kids_space_bakery` directly in VS Code, Claude should be able to understand that this is a story workspace and should know where to find the shared skills and templates.

---

## 2. Core philosophy

Build this as a writing practice system, not a content mill.

The AI should usually act as:

- writing coach
- scene partner
- continuity assistant
- developmental editor
- revision partner
- prompt librarian
- story organizer

The AI should not default to writing everything for me. It may draft sample prose when explicitly asked, but the default mode should be to help me think, write, revise, and improve.

Important principles:

1. Preserve my taste and judgment.
2. Prefer specific feedback over generic praise.
3. Prefer small exercises over giant book-generation prompts.
4. Keep each story project clean and separate.
5. Keep shared skills reusable across all stories.
6. Use markdown files as the primary interface.
7. Avoid hard dependencies on paid APIs in the first version.
8. Make the system pleasant to use inside VS Code.
9. Avoid asking the AI to imitate living authors. Use craft traits instead.
10. Make it easy to stop and resume a writing session.

---

## 3. Implementation preferences

Please implement an MVP with simple, durable technology.

Use:

- Python 3.11+ if code is needed
- standard library wherever possible
- `pathlib` for filesystem paths
- markdown files for all writing assets
- optional `pytest` for tests
- no database for the first version
- no required OpenAI/Anthropic API integration for the first version
- no web app for the first version
- no GUI for the first version

The first version should be mostly:

- folder structure
- markdown templates
- prompt skills
- a lightweight CLI for creating and managing story projects
- generated indexes and session logs

Make it cross-platform. I may use this on Windows, WSL, or another machine. Avoid symlinks by default because they can be annoying on Windows. Use relative paths and copied local guide files instead.

---

## 4. Desired repository structure

Create this structure:

```text
shake_spear/
  README.md
  AGENTS.md
  Claude.md
  pyproject.toml
  .gitignore

  src/
    shake_spear/
      __init__.py
      cli.py
      scaffold.py
      indexer.py
      session.py
      utils.py

  skills/
    README.md
    immersive_session.md
    scene_planner.md
    quick_feedback.md
    revision_passes.md
    continuity_auditor.md
    character_keeper.md
    world_keeper.md
    story_bible_builder.md
    dialogue_doctor.md
    voice_and_taste.md
    kids_story_mode.md
    mystery_mode.md
    recap_and_resume.md
    prompt_smith.md

  templates/
    story_project_README.md
    local_AGENTS.md
    local_Claude.md
    story_bible.md
    active_state.md
    session_log.md
    scene_card.md
    character_profile.md
    world_element.md
    chapter_draft.md
    feedback_note.md
    revision_plan.md
    continuity_log.md
    decision_log.md

  projects/
    _template/
      README.md
      AGENTS.md
      Claude.md
      story_bible.md
      active_state.md
      continuity.md
      decisions.md
      index.md
      characters/
      world/
      scenes/
      drafts/
      sessions/
      feedback/
      revisions/
      exports/

  tests/
    test_scaffold.py
    test_indexer.py
```

The exact package layout can be adjusted if needed, but keep the spirit: one root project, shared skills/templates, many story folders.

---

## 5. CLI behavior

Create a small CLI. The CLI can be invoked as either:

```bash
python -m shake_spear ...
```

or, if simple to configure in `pyproject.toml`:

```bash
ww ...
```

Implement these commands:

### `ww new-story`

Create a new story project.

Example:

```bash
ww new-story "Kids Space Bakery" --slug kids_space_bakery --genre kids --mode playful
```

Behavior:

- Creates `projects/kids_space_bakery/`
- Copies local story templates into that folder
- Creates standard subfolders: `characters`, `world`, `scenes`, `drafts`, `sessions`, `feedback`, `revisions`, `exports`
- Creates local `AGENTS.md` and `Claude.md`
- Local guide files should point back to shared skills using relative paths such as `../../skills/immersive_session.md`
- Initializes `story_bible.md`, `active_state.md`, `continuity.md`, `decisions.md`, and `index.md`
- Does not overwrite an existing story unless `--force` is passed

### `ww session`

Start a dated writing session log inside a story project.

Example:

```bash
ww session projects/kids_space_bakery --type scene --minutes 45
```

Behavior:

- Creates a new file under `sessions/` named like `2026-07-02_scene_45min.md`
- Uses `templates/session_log.md`
- Pulls a short summary from `active_state.md`
- Includes a checklist for the session
- Includes links to useful shared skills
- Includes sections for warm-up, goal, constraints, writing block, quick feedback, continuity updates, and next step

### `ww scene`

Create a new scene card.

Example:

```bash
ww scene projects/kids_space_bakery "Rocket finds the moon oven"
```

Behavior:

- Creates a new markdown file in `scenes/`
- Uses `templates/scene_card.md`
- Adds frontmatter with title, status, POV, location, characters, emotional turn, and tags
- Leaves prompts for scene goal, conflict, sensory details, and ending image

### `ww character`

Create a character profile.

Example:

```bash
ww character projects/no_one_dies_here_usually "Detective Frank Ash"
```

Behavior:

- Creates a file in `characters/`
- Uses `templates/character_profile.md`
- Includes wants, fears, contradictions, secrets, voice notes, relationships, and continuity facts

### `ww world`

Create a world element file.

Example:

```bash
ww world projects/kids_space_bakery "Moon Oven"
```

Behavior:

- Creates a file in `world/`
- Uses `templates/world_element.md`
- Supports locations, objects, institutions, rules, magic/science concepts, recurring images, and cultural details

### `ww index`

Regenerate a project index.

Example:

```bash
ww index projects/kids_space_bakery
```

Behavior:

- Scans story files
- Updates `index.md`
- Lists characters, world elements, scenes, drafts, feedback notes, sessions, and revision plans
- Extracts simple metadata from markdown frontmatter when present
- Does not need a full YAML dependency; simple frontmatter parsing is enough

### `ww recap`

Create a resume-friendly recap file.

Example:

```bash
ww recap projects/kids_space_bakery
```

Behavior:

- Reads `active_state.md`, `continuity.md`, latest sessions, and index data
- Creates or updates `active_state.md`
- Produces a “start here next time” section
- Does not summarize full drafts in a destructive way

---

## 6. Root `AGENTS.md` and `Claude.md`

Create root-level agent guide files.

They should tell Claude:

- This is a creative writing workshop project.
- Do not treat all prose as code.
- Preserve drafts and never overwrite creative writing unless asked.
- Prefer creating new revision files over destructive edits.
- Shared prompt skills live in `skills/`.
- Story projects live in `projects/`.
- Each story project has local context in `story_bible.md`, `active_state.md`, `continuity.md`, `decisions.md`, and `index.md`.
- When assisting with a story, first read the local story files before giving advice.
- For feedback, use the quick feedback format unless the user asks for deep critique.
- For drafting, ask whether the user wants a plan, sample prose, or coaching.
- Avoid imitating living authors. Use craft traits and genre traits instead.

---

## 7. Local story `AGENTS.md` and `Claude.md`

Every story subproject should have its own local guide files so I can open that folder directly with `code .`.

Local guide files should say:

```text
This folder is one story project inside the larger writing workshop.

Before helping, read:
- story_bible.md
- active_state.md
- continuity.md
- decisions.md
- index.md

Shared skills are available at:
- ../../skills/immersive_session.md
- ../../skills/scene_planner.md
- ../../skills/quick_feedback.md
- ../../skills/revision_passes.md
- ../../skills/continuity_auditor.md
- ../../skills/character_keeper.md
- ../../skills/world_keeper.md
- ../../skills/recap_and_resume.md

Default behavior:
- Help me have an immersive writing session.
- Ask one focused question if needed, not a long questionnaire.
- Prefer concrete next actions.
- Preserve my existing draft voice.
- Put new generated files in the appropriate folder.
```

---

## 8. Shared skills to create

Create markdown files under `skills/`. Each skill should be written as a reusable instruction file that I can reference in Claude, ChatGPT, Claude, or another AI assistant.

Each skill file should include:

```text
# Skill Name

## Purpose

## Use when

## Inputs to read first

## Process

## Output format

## Things to avoid
```

Create the following skills.

### `immersive_session.md`

Purpose: guide a focused writing session.

Include a default 45-minute session flow:

1. 3-minute warm start: what are we writing and why?
2. 5-minute orientation: read active state, scene card, and relevant character/world files.
3. 5-minute scene shaping: define scene goal, conflict, emotional turn, and ending image.
4. 20-minute writing block: help me write or hold me accountable.
5. 7-minute quick feedback: identify what works and what to revise.
6. 5-minute shutdown: update continuity, active state, and next action.

The skill should support modes:

- drafting
- revision
- character exploration
- worldbuilding
- dialogue practice
- kids story
- mystery
- freewrite

### `scene_planner.md`

Purpose: turn a vague idea into a concrete scene plan.

Output format:

```text
Scene title:
POV:
Location:
Characters present:
External goal:
Internal/emotional goal:
Conflict:
Complication:
Emotional turn:
Sensory anchors:
Key object:
Ending image or line:
Five scene beats:
```

### `quick_feedback.md`

Purpose: give fast, useful feedback without derailing the writing session.

Output format:

```text
What is working:
Most important issue:
Where I got confused:
Most vivid detail:
Most generic detail:
One craft suggestion:
Three concrete edits:
Continuity notes:
Next writing move:
```

The tone should be direct, kind, and practical.

### `revision_passes.md`

Purpose: revise one dimension at a time.

Include passes for:

- story logic
- character motivation
- emotional tension
- dialogue
- sensory detail
- pacing
- sentence polish
- line-level compression
- humor
- scarier/more suspenseful version
- quieter/more literary version
- kid-friendly clarity

Important: the skill should not rewrite everything at once unless asked. It should identify the target pass and stay focused.

### `continuity_auditor.md`

Purpose: detect contradictions and update continuity notes.

Track:

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

Output should include:

```text
Continuity updates to add:
Possible contradictions:
Open questions:
Reader promises:
Suggested updates to files:
```

### `character_keeper.md`

Purpose: create and maintain character profiles.

Track:

- name
- role in story
- want
- fear
- wound or pressure point
- contradiction
- secret
- voice notes
- physical anchors
- relationships
- recurring behaviors
- what changes over the story
- facts established in scenes

### `world_keeper.md`

Purpose: organize worldbuilding without overbuilding.

Track:

- locations
- objects
- institutions
- rules
- sensory motifs
- social norms
- magic/science rules if relevant
- what the reader needs to know now
- what can remain implied

Include instruction: keep worldbuilding tied to scenes and character choices.

### `story_bible_builder.md`

Purpose: help create a compact story bible.

Sections:

- title
- genre
- audience
- premise
- tone
- main character
- main want
- main fear
- central conflict
- antagonist/opposition
- setting
- themes
- ending direction
- things to avoid
- open questions

### `dialogue_doctor.md`

Purpose: improve dialogue.

Focus on:

- subtext
- character-specific voice
- conflict
- rhythm
- cutting exposition
- awkward human behavior
- what is not being said

### `voice_and_taste.md`

Purpose: preserve my writing taste.

Include a section where I can define:

- prose I like
- prose I dislike
- preferred sentence feel
- humor level
- darkness level
- sincerity level
- weirdness level
- banned phrases
- recurring images I like
- style traits without naming living authors to imitate

### `kids_story_mode.md`

Purpose: help write children’s stories.

Focus on:

- clarity
- warmth
- concrete images
- playful repetition
- emotionally safe conflict
- read-aloud rhythm
- wonder
- gentle humor
- age-appropriate stakes

Avoid:

- condescension
- too many abstract lessons
- scary details unless requested
- overly complicated plots

### `mystery_mode.md`

Purpose: help write mystery stories.

Track:

- crime or central question
- suspects
- motives
- means
- opportunity
- clues
- red herrings
- reveals
- fair-play clue placement
- timeline
- detective knowledge vs reader knowledge

### `recap_and_resume.md`

Purpose: help me stop and resume projects.

Output:

```text
Current state:
What I wrote last:
What is emotionally alive:
Open loops:
Files changed:
Best next scene:
One tiny next action:
```

### `prompt_smith.md`

Purpose: help improve prompts for AI writing assistance.

It should turn vague requests into better prompts with:

- context
- task
- constraints
- desired output format
- tone
- what not to do
- examples when useful

---

## 9. Template details

Create templates with useful headings and lightweight frontmatter.

### `story_bible.md`

Include:

```markdown
---
type: story_bible
title:
genre:
audience:
status: seed
---

# Story Bible

## One-sentence premise

## What kind of story is this?

## Main character

## What they want

## What they fear

## Central conflict

## Setting

## Tone

## Themes

## Ending direction

## Things this story should avoid

## Open questions
```

### `active_state.md`

This should be the “start here” file for each story.

Include:

```markdown
# Active State

## Current status

## Last session summary

## What feels alive right now

## Current scene or chapter

## Open loops

## Next tiny action

## Files to read before continuing

## Notes for AI assistants
```

### `session_log.md`

Include:

```markdown
---
type: session_log
date:
session_type:
minutes:
status: open
---

# Writing Session

## Warm start

What am I writing today?

Why does it interest me right now?

## Read first

- [ ] active_state.md
- [ ] story_bible.md
- [ ] continuity.md
- [ ] relevant scene/character/world files

## Session goal

## Constraints

## Scene or exercise setup

## Writing block

## Quick feedback

## Continuity updates

## Decisions made

## Next tiny action
```

### `scene_card.md`

Include:

```markdown
---
type: scene
title:
status: planned
pov:
location:
characters: []
tags: []
---

# Scene

## Purpose in story

## External goal

## Internal/emotional goal

## Conflict

## Complication

## Emotional turn

## Sensory anchors

## Key object or image

## Five beats

1.
2.
3.
4.
5.

## Draft links

## Feedback links

## Continuity notes
```

### `character_profile.md`

Include:

```markdown
---
type: character
name:
role:
status: active
tags: []
---

# Character

## Short description

## Want

## Fear

## Contradiction

## Secret

## Voice notes

## Physical anchors

## Relationships

## Recurring behaviors

## Arc

## Established facts

## Open questions
```

### `world_element.md`

Include:

```markdown
---
type: world_element
name:
category:
status: active
tags: []
---

# World Element

## What it is

## Why it matters

## Sensory details

## Rules or constraints

## Connected characters

## Connected scenes

## Established facts

## Open questions
```

---

## 10. Immersive writing session behavior

Make the project especially good at helping me enter and exit focused creative writing sessions.

A session should help answer:

- What am I writing right now?
- What do I need to read before starting?
- What is the smallest useful creative target?
- What emotional turn am I trying to create?
- What can I write in 20–45 minutes?
- What feedback do I need immediately?
- What should be updated before I stop?
- What is the next tiny action?

Do not optimize for maximum output. Optimize for momentum, creative safety, and repeatability.

---

## 11. Indexing and metadata

Implement a simple indexer that scans markdown files and updates `index.md` in each story project.

The index should include sections like:

```markdown
# Project Index

## Story files

## Characters

## World elements

## Scenes

## Drafts

## Sessions

## Feedback

## Revisions

## Recently modified files
```

For each file, include:

- title or filename
- type if available
- status if available
- relative path
- short first-line summary if easy

Do not attempt semantic embeddings in the MVP.

---

## 12. Git and safety behavior

Add `.gitignore` that ignores common junk:

```text
__pycache__/
.pytest_cache/
.venv/
dist/
build/
.DS_Store
```

Do not ignore story drafts by default. I may want them in git.

When scripts generate or update files:

- avoid destructive overwrites
- create backups or require `--force` for overwrite
- preserve existing drafts
- never delete creative writing automatically

---

## 13. README instructions

Create a friendly `README.md` with:

1. What this project is
2. How to install/run locally
3. How to create a new story
4. How to start a writing session
5. How to create a scene, character, or world element
6. How to regenerate an index
7. How to open a subproject directly with `code .`
8. How to use the shared skills
9. Suggested first writing exercise

Include example commands:

```bash
python -m venv .venv
# activate the environment depending on OS
pip install -e .
ww new-story "Kids Space Bakery" --slug kids_space_bakery --genre kids
ww session projects/kids_space_bakery --type scene --minutes 45
ww scene projects/kids_space_bakery "The bakery runs out of moon sugar"
ww character projects/kids_space_bakery "Nova the baker"
ww world projects/kids_space_bakery "Moon sugar"
ww index projects/kids_space_bakery
ww recap projects/kids_space_bakery
```

Also include:

```bash
cd projects/kids_space_bakery
code .
```

Explain that the local `AGENTS.md` and `Claude.md` files help AI tools find the shared workshop skills.

---

## 14. Acceptance criteria

The MVP is complete when:

- The repository structure exists.
- `pip install -e .` works.
- `ww new-story` creates a complete story project.
- The story project includes local `AGENTS.md` and `Claude.md`.
- The local guide files link back to the shared skills.
- `ww session` creates a useful session log.
- `ww scene` creates a scene card.
- `ww character` creates a character profile.
- `ww world` creates a world element.
- `ww index` updates the story index.
- `ww recap` updates or generates resume-friendly active state notes.
- Tests cover basic scaffold and index behavior.
- The README explains how to use the system.

---

## 15. Nice-to-have extras if quick

Only add these after the MVP works:

- VS Code tasks for common commands
- a `ww list-projects` command
- a `ww status` command that prints the current active state
- a `ww daily` command that starts a daily freewrite session
- a `ww export` command that gathers drafts into `exports/manuscript.md`
- a `prompts/` folder inside each story for story-specific prompts
- simple `tags.md` conventions
- sample story projects: one kids story and one mystery story

---

## 16. First-use exercise to include in the README

Add this exercise as the recommended first session:

```markdown
# First Writing Session: Tiny Scene

Open a new story project and start a 30–45 minute session.

Goal: write one small scene, not a chapter.

Prompt:

A character wants something simple, but another character misunderstands why it matters.

During the session:

1. Create a character profile.
2. Create a scene card.
3. Define the emotional turn.
4. Write 300–700 words.
5. Run quick feedback.
6. Update continuity.
7. Write the next tiny action.
```

---

## 17. Build order

Please build in this order:

1. Create the repo structure.
2. Add templates.
3. Add shared skill markdown files.
4. Add root and local agent guide templates.
5. Implement CLI scaffold commands.
6. Implement index command.
7. Implement session/recap helpers.
8. Add README.
9. Add basic tests.
10. Run tests and fix failures.

Keep the implementation simple and readable. Favor boring, useful file operations over clever abstractions.

---

## 18. Final note for Claude

This project is successful if it makes it easy for me to sit down, open a story folder, and quickly enter a creative writing session with useful AI help.

The main UX should feel like:

```bash
cd shake_spear/projects/no_one_dies_here_usually
code .
```

Then I can tell Claude:

```text
Use the immersive session skill. Help me write for 45 minutes. Read active_state.md first.
```

Or:

```text
Use quick_feedback.md on this scene. Be direct and practical.
```

Or:

```text
Use continuity_auditor.md and update continuity.md with anything new from this draft.
```

Build the system around that workflow.
