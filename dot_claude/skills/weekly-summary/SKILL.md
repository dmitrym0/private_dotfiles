---
name: weekly-summary
description: Review work activity since last Monday across GitHub, Jira, and Confluence. Produces a structured summary of PRs, commits, Jira tickets, and Confluence pages. Use when asked for a weekly summary, work recap, or "what have I been working on".
argument-hint: [optional start date, e.g. 2026-04-20]
allowed-tools: Bash(gh *) Bash(jira *) Bash(curl *) Bash(python3 *) Bash(date *)
---

Produce a structured work summary for the period from **$ARGUMENTS** (if provided) or the most recent Monday, through today.

## Step 0 — Determine date range

```!
python3 -c "
from datetime import date, timedelta
today = date.today()
days_since_monday = today.weekday()
last_monday = today - timedelta(days=days_since_monday)
print(last_monday.isoformat())
"
```

If `$ARGUMENTS` is provided and looks like a date (YYYY-MM-DD), use that as the start date instead.

Set START_DATE to the resolved date. All queries below use `>= START_DATE`.

## Step 1 — GitHub: get authenticated user and events

```bash
LOGIN=$(gh api user --jq '.login')
gh api "users/${LOGIN}/events?per_page=100" \
  --jq --argjson since "\"${START_DATE}\"" \
  '[.[] | select(.created_at >= $since)] | group_by(.repo.name) | .[] | {repo: .[0].repo.name, events: [.[] | {type: .type, created_at: .created_at}]}'
```

From the grouped output, identify which repos had meaningful activity (PRs, pushes, issues — not just DeleteEvents alone).

## Step 2 — GitHub: PR and commit details per active repo

For each repo with meaningful activity, run in parallel:

```bash
# PRs
gh pr list --repo REPO --author $LOGIN --state all --limit 20 \
  --json number,title,state,createdAt,mergedAt 2>/dev/null

# Commits (skip if repo returns 404 — it's private/inaccessible)
gh api "repos/REPO/commits?author=${LOGIN}&since=${START_DATE}T00:00:00Z" \
  --jq '.[] | {sha: .sha[:7], message: (.commit.message | split("\n")[0]), date: .commit.author.date}' 2>/dev/null
```

Skip any repo that errors (private org repos without access). Note them as "activity seen but repo inaccessible."

For personal repos (dmitrym0/*), include commit messages verbatim.
For work repos (varsitytutors/*, MantaAPM/*), focus on PR titles and only include commits if there are no PRs.

## Step 3 — Jira: assigned tickets updated this period

```bash
jira issue list --jql "assignee = currentUser() AND updated >= \"${START_DATE}\""
```

Note: no ORDER BY — it is not supported by this CLI. For any interesting ticket keys in the output, view them:

```bash
jira issue view KEY
```

Categorize tickets as:
- **Closed/Done**: resolved during this period
- **In Progress**: actively worked, still open
- **Newly created**: created during this period, still in Triage/To Do

## Step 4 — Confluence: pages created or modified

```bash
START="${START_DATE}"
CQL="creator = currentUser() AND lastModified >= \"${START}\" AND type = page ORDER BY lastModified DESC"
ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$CQL")

curl -s -u "dmitry.markushevich@varsitytutors.com:$JIRA_API_TOKEN" \
  "https://varsity.atlassian.net/wiki/rest/api/content/search?cql=${ENCODED}&limit=25&expand=title,space,version" \
  -H "Accept: application/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
results = d.get('results', [])
print(f'Pages modified since cutoff: {len(results)}')
for r in results:
    v = r.get('version', {})
    space = r.get('space', {}).get('key', '?')
    modified = v.get('when', '')[:10]
    by = v.get('by', {}).get('displayName', '?')
    print(f'  [{r[\"id\"]}] [{space}] {r[\"title\"]} — modified {modified} by {by}')
    print(f'    https://varsity.atlassian.net/wiki{r[\"_links\"][\"webui\"]}')
"
```

If zero results: note "No Confluence pages created or modified in this window."

## Step 5 — Open PRs (all repos, current snapshot)

```bash
gh search prs --author $(gh api user --jq '.login') --state open --limit 50 \
  --json repository,number,title,createdAt,url
```

Group by repo. Flag any PRs older than 2 weeks as potentially stale.

## Step 6 — Produce the summary

Output a structured markdown summary with these sections:

```
## Work Summary: {START_DATE} – {TODAY}

### {Org} Repos (work)

**{repo-name}** — {one-line characterization}
- PR #{n} [{state}]: {title} ({date})
- ...

### Personal Repos

**{repo-name}**
- {commit message} ({date})
- ...

### Jira Tickets

#### Closed this week
| Key | Summary | Priority |
...

#### In Progress
| Key | Summary | Status |
...

#### Newly created (backlog/triage)
| Key | Summary | Created |
...

### Confluence
{List of pages, or "No activity in this window."}

### Open PRs
Group by repo. Mark PRs older than 2 weeks as **(stale)**.

| Repo | PR | Title | Age |
...

### Themes
{2–4 sentence synthesis: what were the dominant threads? Any notable sev2+ issues? Infrastructure work vs. feature work? Open loops to watch?}
```

Keep the Themes section concise and analytical — note patterns, not just facts.
