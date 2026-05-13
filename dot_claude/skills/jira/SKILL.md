---
name: jira
description: Perform Jira operations using the jira CLI. Use when the user asks to find, view, or create Jira issues/tickets/stories/epics, or asks to look something up in Jira.
argument-hint: [find <keyword> | create ticket under <parent> | view <key> | ...]
allowed-tools: Bash(jira *)
---

Perform the following Jira operation: $ARGUMENTS

## CLI Reference

### Search / Find Issues
```bash
# By keyword in summary (no ORDER BY — not supported)
jira issue list --jql 'summary ~ "keyword"'

# Children of an epic
jira issue list --jql '"Epic Link" = MEX-123 OR parentEpic = MEX-123'

# My open issues
jira issue list --jql 'assignee = currentUser() AND resolution = Unresolved'

# By project
jira issue list -p MEX
```

### View an Issue
```bash
jira issue view MEX-123
```

### Create a Ticket
```bash
jira issue create \
  -p PROJECT \
  -t Task \
  -s "Summary" \
  -P PARENT-KEY \
  -y sev4 \
  -a "Dmitry Markushevich" \
  --body "BODY" \
  --no-input
```

### List Projects
```bash
jira project list
```

## Workflow: "find X and create ticket: Y"

1. Search for the parent: `jira issue list --jql 'summary ~ "X"'`
2. Pick the best match — prefer epics that are In Progress and assigned to current user
3. View it to get project key and context: `jira issue view ISSUE-KEY`
4. Craft a description using the template below
5. Create the child ticket with `--no-input`
6. Output the new ticket URL

## Ticket Body Template

```
## Objective
One sentence goal.

## Context
Why this is needed and relevant background.

## Requirements
- Specific requirement
- Reference related patterns or issues where applicable

## Acceptance Criteria
- [ ] Checkbox item defining done
```

## Defaults
- Project: MEX
- Type: Task
- Priority: sev4
- Assignee: Dmitry Markushevich
