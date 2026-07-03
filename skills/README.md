# Shared Skills

Reusable AI prompt skills for the shake_spear writing workshop. Each file is a
self-contained instruction set any AI assistant can follow — Claude, ChatGPT,
or anything else that reads markdown. They all share the same skeleton
(Purpose / Use when / Inputs to read first / Process / Output format / Things
to avoid), so once you know one, you know how to read them all.

The skill files in this folder are the single source of truth. The slash
wrappers and story-local wrappers described below carry no content of their
own — they only point here.

## Skill catalog

| Skill file | Slash wrapper | One-line purpose |
|---|---|---|
| `immersive_session.md` | `/immersive-session` | Guide a focused 45-minute writing session, warm start to shutdown |
| `scene_planner.md` | `/scene-planner` | Turn a vague idea into a concrete scene plan |
| `quick_feedback.md` | `/quick-feedback` | Fast, direct, practical feedback without derailing the session |
| `revision_passes.md` | `/revision-passes` | Revise one dimension at a time |
| `continuity_auditor.md` | `/continuity-auditor` | Detect contradictions and update continuity notes |
| `character_keeper.md` | `/character-keeper` | Create and maintain character profiles |
| `world_keeper.md` | `/world-keeper` | Organize worldbuilding without overbuilding |
| `story_bible_builder.md` | `/story-bible-builder` | Build a compact story bible |
| `dialogue_doctor.md` | `/dialogue-doctor` | Improve dialogue: subtext, voice, rhythm, what is not said |
| `voice_and_taste.md` | `/voice-and-taste` | Preserve the writer's taste via craft traits, never living-author imitation |
| `kids_story_mode.md` | `/kids-story-mode` | Children's stories: clarity, warmth, read-aloud rhythm, safe stakes |
| `mystery_mode.md` | `/mystery-mode` | Mysteries: clues, red herrings, fair play, knowledge gaps |
| `recap_and_resume.md` | `/recap-and-resume` | Stop/resume ritual: capture state, resume in minutes |
| `prompt_smith.md` | `/prompt-smith` | Turn vague AI requests into well-formed prompts |

## In Claude Code: slash wrappers

Every skill has a kebab-case slash wrapper under the workshop root's
`.claude/skills/` (e.g. `quick_feedback.md` becomes `/quick-feedback`). The
wrapper is a thin pointer: it tells Claude to read the shared file in this
folder and follow it exactly, so there is no second copy to drift.

From a Claude Code session at the workshop root, just invoke the skill:

```text
/quick-feedback
```

You can pass your ask in the same breath: `/quick-feedback the kitchen scene
in drafts/ch02.md — be blunt about the pacing`.

## In any other assistant: paste or point

The skills are plain markdown, so any assistant can use them. Two ways:

- **Point** (when the assistant can read files): say

  ```text
  Read skills/quick_feedback.md and apply it to the scene below.
  ```

- **Paste** (when it cannot): open the skill file, paste its full contents
  into the chat, then add your material and say "apply this."

Either way, also give the assistant the story context the skill's "Inputs to
read first" section asks for (paste `active_state.md`, the scene card, etc. if
the assistant cannot read files itself).

## Inside a story folder (`code .`)

Each story under `projects/` works standalone: `cd projects/<your_story>`
then `code .`, and the story's local guide files orient the assistant.

- **Claude Code:** the story ships with generated story-local wrappers in its
  own `.claude/skills/`, so the same slash commands (`/immersive-session`,
  `/quick-feedback`, ...) work with the story folder as the workspace root.
- **Any assistant:** the shared skills are two levels up — reference them by
  relative path:

  ```text
  Read ../../skills/mystery_mode.md and audit my clue placement.
  ```

- The story-local `CLAUDE.md` / `AGENTS.md` list these paths, and the local
  read-first files (`story_bible.md`, `active_state.md`, `continuity.md`)
  live right in the story folder, so the assistant has full context without
  the workshop root open.

## Picking a skill

Starting a session? `immersive_session.md`. Stuck before writing?
`scene_planner.md` or `story_bible_builder.md`. Just wrote something?
`quick_feedback.md`. Editing? `revision_passes.md`, `dialogue_doctor.md`.
Keeping the story straight? `continuity_auditor.md`, `character_keeper.md`,
`world_keeper.md`, `mystery_mode.md`. Writing for kids? `kids_story_mode.md`.
Sounding like yourself? `voice_and_taste.md`. Stopping or coming back?
`recap_and_resume.md`. Asking an AI for anything at all? `prompt_smith.md`.
