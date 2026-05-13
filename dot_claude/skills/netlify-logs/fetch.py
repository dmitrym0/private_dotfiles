#!/usr/bin/env python3
"""Fetch Netlify observability request logs with client IPs."""

import sys
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone

def get_token():
    import os
    config_path = os.path.expanduser('~/Library/Preferences/netlify/config.json')
    with open(config_path) as f:
        d = json.load(f)
    for uid, user in d.get('users', {}).items():
        token = user.get('auth', {}).get('token', '')
        if token:
            return token
    raise RuntimeError('No Netlify auth token found in ~/Library/Preferences/netlify/config.json')

def parse_args(args):
    site_id = None
    window = '1h'
    status = None
    count = 100

    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--site', '-s') and i + 1 < len(args):
            site_id = args[i + 1]; i += 2
        elif a in ('--window', '-w') and i + 1 < len(args):
            window = args[i + 1]; i += 2
        elif a in ('--status') and i + 1 < len(args):
            status = args[i + 1]; i += 2
        elif a in ('--count', '-n') and i + 1 < len(args):
            count = int(args[i + 1]); i += 2
        else:
            i += 1

    return site_id, window, status, count

def parse_window(window):
    now_ms = int(time.time() * 1000)
    unit = window[-1]
    val = int(window[:-1])
    seconds = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}.get(unit, 3600) * val
    return now_ms - seconds * 1000, now_ms

def post(url, payload, token):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get(url, token):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def fetch_list(site_id, from_ts, to_ts, token, status, count):
    list_url = f'https://app.netlify.com/access-control/bb-api/api/v1/sites/{site_id}/observability/query/lists?from_ts={from_ts}&to_ts={to_ts}'
    filters = [
        {'field': 'Branch', 'op': '=', 'value': 'production'},
        {'field': 'Branch', 'op': '=', 'value': '__nf-no-branch-production-traffic'},
    ]
    if status:
        filters.append({'field': 'StatusCode', 'op': '=', 'value': int(status)})

    all_items = []
    page = 1
    while len(all_items) < count:
        per_page = min(50, count - len(all_items))
        payload = {'data': [{'attributes': {'queries': [{'name': 'edge_requests_logs',
            'filters': filters, 'page': page, 'per_page': per_page}]}}]}
        items = post(list_url, payload, token)['data'][0]['attributes']['list']
        all_items.extend(items)
        if len(items) < per_page:
            break
        page += 1

    return all_items[:count]

def fetch_detail(item, site_id, from_ts, to_ts, token):
    rid = item['request_id']
    url = (f'https://app.netlify.com/access-control/bb-api/api/v1/sites/{site_id}'
           f'/observability/requests/{rid}?from_ts={from_ts}&to_ts={to_ts}'
           f'&branch=production&branch=__nf-no-branch-production-traffic')
    try:
        d = get(url, token)
        client = d.get('client', {})
        return {
            'ip': client.get('address', 'unknown'),
            'ua': (client.get('user_agent') or '')[:100],
            'country': client.get('country', ''),
            'url': item['url'],
            'status': item.get('status_code') or 0,
            'duration_ms': round(item['duration_ns'] / 1e6),
            'cache': item.get('edge_cache_result', ''),
            'timestamp': item.get('timestamp', ''),
        }
    except Exception:
        return {
            'ip': 'error', 'ua': '', 'country': '',
            'url': item.get('url', ''), 'status': item.get('status_code') or 0,
            'duration_ms': round(item['duration_ns'] / 1e6),
            'cache': item.get('edge_cache_result', ''),
            'timestamp': item.get('timestamp', ''),
        }

def main():
    site_id, window, status, count = parse_args(sys.argv[1:])

    if not site_id:
        print('Error: --site <site_id> is required', file=sys.stderr)
        sys.exit(1)

    token = get_token()
    from_ts, to_ts = parse_window(window)

    print(f'Fetching up to {count} requests | window={window} | status={status or "all"}', file=sys.stderr)
    items = fetch_list(site_id, from_ts, to_ts, token, status, count)
    print(f'Listed {len(items)} requests, fetching details...', file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(fetch_detail, item, site_id, from_ts, to_ts, token): item for item in items}
        for i, f in enumerate(as_completed(futures)):
            results.append(f.result())
            if (i + 1) % 100 == 0:
                print(f'  {i+1}/{len(items)}...', file=sys.stderr)

    results.sort(key=lambda x: x.get('timestamp', ''))

    n = len(results)
    ip_counts = Counter(r['ip'] for r in results)

    print(f'\nTotal: {n} requests\n')

    print('=== TOP IPs ===')
    for ip, cnt in ip_counts.most_common(20):
        print(f'  {cnt:4d} ({cnt/n*100:5.1f}%)  {ip}')

    print('\n=== STATUS CODES ===')
    for code, cnt in sorted(Counter(r['status'] for r in results).items()):
        print(f'  {code}: {cnt}')

    print('\n=== PER-IP BREAKDOWN ===')
    for ip, _ in ip_counts.most_common(10):
        ip_reqs = [r for r in results if r['ip'] == ip]
        codes = Counter(r['status'] for r in ip_reqs)
        durs = [r['duration_ms'] for r in ip_reqs]
        avg_ms = sum(durs) // len(durs) if durs else 0
        print(f'  {ip}  n={len(ip_reqs)}  avg={avg_ms}ms  {dict(sorted(codes.items()))}')

    print('\n=== USER AGENTS ===')
    for ip, _ in ip_counts.most_common(5):
        uas = list({r['ua'] for r in results if r['ip'] == ip and r['ua']})
        print(f'  {ip}:')
        for ua in uas[:3]:
            print(f'    {ua}')

    print(f'\n=== ALL REQUESTS ===')
    print(f"{'TIMESTAMP':<32} {'IP':<18} {'MS':>7} {'ST':>4} {'CACHE':<6} URL")
    print('-' * 120)
    for r in results:
        print(f"{r['timestamp']:<32} {r['ip']:<18} {r['duration_ms']:>7} {r['status']:>4} {r['cache']:<6} {r['url'][:60]}")

if __name__ == '__main__':
    main()
