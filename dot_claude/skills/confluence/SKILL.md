---
name: confluence
description: Search and read Confluence pages via the REST API. Use when the user asks to find, search, or read Confluence pages, docs, runbooks, specs, or post-mortems — or asks to look something up in Confluence.
argument-hint: [search query, page ID, or "list <space>"]
allowed-tools: Bash(curl *) Bash(python3 *)
---

Search and read Confluence pages at `https://varsity.atlassian.net/wiki/rest/api/`.

**Auth:** basic auth with `dmitry.markushevich@varsitytutors.com:$JIRA_API_TOKEN`.

## Handling $ARGUMENTS

Parse `$ARGUMENTS` to determine the operation:

1. **Get a specific page** — if args contain a numeric page ID (e.g. `get page 1805025284`, `page 1805025284`, or just `1805025284`)
2. **List a space** — if args start with `list` followed by a space key (e.g. `list MEX`, `list pages in ENG`)
3. **Search** — everything else is a search query (e.g. `find pages I created`, `pages about EdgeRouter`, `pages about lead forms in MEX space created last month`)

If `$ARGUMENTS` is empty, ask the user what they want to find.

---

## Operation 1 — Fetch a single page

```bash
curl -s -u "dmitry.markushevich@varsitytutors.com:$JIRA_API_TOKEN" \
  "https://varsity.atlassian.net/wiki/rest/api/content/<PAGE_ID>?expand=body.storage,title,space,version,history" \
  -H "Accept: application/json" | python3 -c "
import json, sys, re
d = json.load(sys.stdin)
print('TITLE:', d.get('title'))
print('SPACE:', d.get('space', {}).get('key'))
print('URL:  ', 'https://varsity.atlassian.net/wiki' + d.get('_links', {}).get('webui', ''))
v = d.get('version', {})
print('LAST MODIFIED:', v.get('when', '?'), 'by', v.get('by', {}).get('displayName', '?'))
print()
body = d.get('body', {}).get('storage', {}).get('value', '')
text = re.sub(r'<[^>]+>', '', body)
text = re.sub(r'\n{3,}', '\n\n', text).strip()
print(text)
"
```

Show the full content (no truncation).

---

## Operation 2 — List pages in a space

```bash
curl -s -u "dmitry.markushevich@varsitytutors.com:$JIRA_API_TOKEN" \
  "https://varsity.atlassian.net/wiki/rest/api/content?spaceKey=<SPACE_KEY>&limit=50&orderby=modified&expand=title,version" \
  -H "Accept: application/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for r in d.get('results', []):
    v = r.get('version', {})
    print(r['id'], r['title'], '—', v.get('when', '')[:10])
print()
print('Total:', d.get('size', 0), 'shown of', d.get('totalSize', '?'))
"
```

---

## Operation 3 — Search by CQL

Build a CQL query from the natural language request. Common mappings:

| User says | CQL clause |
|---|---|
| pages I created / my pages | `creator = currentUser()` |
| in MEX / in ENG space | `space = "MEX"` |
| about EdgeRouter / about X | `text ~ "EdgeRouter"` |
| titled X | `title ~ "X"` |
| last 4 months / since December | `created >= "2025-12-30"` |
| last month | `created >= now("-4w")` |
| recently updated | `lastModified >= now("-2w")` |
| pages (not comments) | `type = page` |

Combine clauses with `AND`. Default: add `type = page` unless the user specifically asks for comments. Order by `created DESC` unless recency of edits matters (use `lastModified DESC`).

URL-encode the CQL string before embedding in the URL.

```bash
CQL='creator = currentUser() AND created >= "2025-12-30" ORDER BY created DESC'
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$CQL'))")

curl -s -u "dmitry.markushevich@varsitytutors.com:$JIRA_API_TOKEN" \
  "https://varsity.atlassian.net/wiki/rest/api/content/search?cql=${ENCODED}&limit=25&expand=title,space,history" \
  -H "Accept: application/json" | python3 -c "
import json, sys, re
d = json.load(sys.stdin)
results = d.get('results', [])
print(f'Found {len(results)} results (total: {d.get(\"totalSize\", \"?\")})\n')
for r in results:
    created = r.get('history', {}).get('createdDate', '')[:10]
    space = r.get('space', {}).get('key', '?')
    print(f'[{r[\"id\"]}] [{space}] {r[\"title\"]} ({created})')
    print(f'  https://varsity.atlassian.net/wiki{r[\"_links\"][\"webui\"]}')
print()
"
```

After listing results, offer to fetch the full content of any page by ID.

---

## Output Format

- **Search results:** ID, space key, title, created date, URL — one per line. Offer to fetch full content.
- **Single page:** Full stripped text, preceded by title/space/URL/last-modified header.
- **List:** ID, title, last-modified date — one per line.

Keep output clean. Strip all HTML tags with `re.sub(r'<[^>]+>', '', body)` and collapse excess newlines with `re.sub(r'\n{3,}', '\n\n', text)`.
