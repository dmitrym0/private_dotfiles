---
name: new-skill
description: Create a new Claude Code skill. Use when the user asks to create a skill, build a skill, or add a /skill-name command.
argument-hint: [description of the skill to create]
allowed-tools: Read, Write, Bash, Glob
---

Create a new Claude Code skill based on: $ARGUMENTS

Refer to [reference.md](reference.md) for the complete skills specification.

## Step 1: Decide Scope

Ask (or infer from context):
- **Global** (`~/.claude/skills/<name>/`) — useful across all projects (e.g., Jira, git workflows, general tools)
- **Project** (`.claude/skills/<name>/`) — specific to this codebase (e.g., migration generator, component scaffolder)

## Step 2: Design the Skill

Determine from $ARGUMENTS and context:

| Decision | Options (see reference.md) |
|---|---|
| Who invokes? | Both (default) / user-only (`disable-model-invocation: true`) / Claude-only (`user-invocable: false`) |
| Needs isolation? | `context: fork` + `agent: <type>` |
| Needs tool access? | `allowed-tools: Bash(cmd *) Read Write ...` |
| Takes arguments? | Use `$ARGUMENTS`, named `arguments:` list, or `$ARGUMENTS[N]` |
| Needs live data? | Use `` !`command` `` for dynamic context injection |
| Supporting files? | Templates, scripts, examples → reference from SKILL.md |

**Rules of thumb:**
- Side-effect operations (create, deploy, send) → `disable-model-invocation: true`
- Background knowledge/conventions → `user-invocable: false`
- Everything else → default (both)
- Keep SKILL.md under 500 lines; put detailed docs in supporting files

## Step 3: Create the Files

Create the skill directory and SKILL.md:

```
~/.claude/skills/<name>/SKILL.md       # global
.claude/skills/<name>/SKILL.md         # project
```

Frontmatter template:
```yaml
---
name: skill-name
description: What it does and when to use it. Be specific — Claude uses this for auto-invocation.
argument-hint: [hint shown in autocomplete]
allowed-tools: Bash(specific-cmd *) Read Write
# disable-model-invocation: true   # uncomment for user-only
# user-invocable: false             # uncomment for Claude-only
# context: fork                     # uncomment to run in isolated subagent
# agent: Explore                    # subagent type if context: fork
---
```

## Step 4: Verify

After writing the files:
1. Confirm the path is correct
2. Show the user the full SKILL.md content
3. Note: new top-level skill directories require a Claude Code restart to appear in `/` autocomplete; edits to existing skills take effect immediately
