# Claude Code Skills Reference

## File Structure

```
~/.claude/skills/<name>/        # global (all projects)
.claude/skills/<name>/          # project-level
  SKILL.md                      # required entrypoint
  reference.md                  # optional supporting docs
  examples/                     # optional examples
  scripts/                      # optional scripts
```

## SKILL.md Format

```yaml
---
name: my-skill
description: What this skill does and when to use it (used for auto-invocation)
when_to_use: Additional context for automatic invocation
argument-hint: [hint shown in / autocomplete]
arguments: [arg1, arg2]         # enables $arg1, $arg2 substitution
allowed-tools: Bash(git *) Read Write
disable-model-invocation: true  # user-only invocation
user-invocable: false           # Claude-only invocation
context: fork                   # run in isolated subagent
agent: Explore                  # subagent type (with context: fork)
model: claude-opus-4-7          # model override
effort: high                    # low | medium | high | xhigh | max
paths: src/**/*.ts              # limit auto-activation to these paths
shell: bash                     # bash (default) or powershell
---

Skill instructions here...
```

## String Substitutions

| Variable | Value |
|---|---|
| `$ARGUMENTS` | All arguments passed on invocation |
| `$ARGUMENTS[N]` | Nth argument (0-based) |
| `$N` | Shorthand for `$ARGUMENTS[N]` |
| `$argname` | Named argument from `arguments:` list |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | Current effort level |
| `${CLAUDE_SKILL_DIR}` | Directory containing SKILL.md |

## Dynamic Context Injection

Shell commands that run at skill load time (before Claude sees the content):

```markdown
Inline: !`git branch --show-current`

Multi-line:
```!
git status --short
npm --version
```
```

Output replaces the placeholder. Disable with `"disableSkillShellExecution": true` in settings.

## Invocation Control

| Frontmatter | User `/name` | Claude auto | Use for |
|---|---|---|---|
| (neither) | ✓ | ✓ | General purpose |
| `disable-model-invocation: true` | ✓ | ✗ | Side effects: create, deploy, send |
| `user-invocable: false` | ✗ | ✓ | Background knowledge, conventions |

## allowed-tools Patterns

```yaml
# Specific command prefix
allowed-tools: Bash(git *) Bash(npm test*)

# Multiple tools
allowed-tools: Read Write Glob Grep

# Space or YAML list both work
allowed-tools:
  - Bash(jira *)
  - Read
```

## Subagent Isolation

```yaml
context: fork
agent: Explore   # Explore | Plan | general-purpose
```

Skill runs as an isolated subagent with no conversation history. The skill content becomes the subagent's task prompt.

## Live Change Detection

- Edits to existing skill files → take effect immediately
- New top-level skill directory → requires Claude Code restart
