#!/usr/bin/env python3
"""Generate local profile assets using only the standard library and GitHub CLI."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, LINE, TEXT, MUTED, CYAN = '#080f18', '#101c29', '#233445', '#e7f0f6', '#9aaebe', '#55dce5'


def api(*args):
    result = subprocess.run(['gh', 'api', *args], check=True, text=True, capture_output=True)
    data = json.loads(result.stdout)
    if isinstance(data, dict) and data.get('errors'):
        raise RuntimeError(json.dumps(data['errors']))
    return data


def summarize_repositories(repos, languages):
    owned = [r for r in repos if not r['private'] and not r['fork']]
    totals = Counter()
    for repo in owned:
        totals.update(languages(repo))
    return {'repositories': len(owned), 'stars': sum(r['stargazers_count'] for r in owned),
            'language_bytes': dict(totals)}


def collect(username, now):
    end = now.date()
    start = end - timedelta(days=364)
    query = '''query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) { contributionsCollection(from:$from,to:$to) {
        contributionCalendar { totalContributions weeks { contributionDays {
          date contributionCount contributionLevel weekday
        } } }
      } }
    }'''
    result = api('graphql', '-f', 'query=' + query, '-f', 'login=' + username,
                 '-f', 'from=' + start.isoformat() + 'T00:00:00Z',
                 '-f', 'to=' + end.isoformat() + 'T23:59:59Z')
    user = result['data']['user']
    if user is None:
        raise ValueError('GitHub user not found')
    calendar = user['contributionsCollection']['contributionCalendar']
    repos = []
    page_number = 1
    while True:
        page = api(f'users/{username}/repos?type=owner&per_page=100&page={page_number}')
        repos.extend(repo for repo in page if repo['owner']['login'].lower() == username.lower())
        if len(page) < 100:
            break
        page_number += 1
    stats = summarize_repositories(repos, lambda r: api(f'repos/{username}/{r["name"]}/languages'))
    days = [d for w in calendar['weeks'] for d in w['contributionDays'] if start.isoformat() <= d['date'] <= end.isoformat()]
    if len(days) != 365 or sum(d['contributionCount'] for d in days) != calendar['totalContributions']:
        raise ValueError('Incomplete or inconsistent contribution calendar; refusing to publish')
    return {'username': username, 'generated_at': now.isoformat(timespec='seconds'),
            'from': start.isoformat(), 'to': end.isoformat(), 'calendar': calendar, **stats,
            'scope': 'Owned public non-fork repositories (including archived); GitHub contribution calendar as visible to the generating token. Language bytes are not expertise or time spent.'}


def label(x, y, value, size=16, color=TEXT, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def svg(title, description, height, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}} .scan{{animation:scan 14s linear infinite}} @keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX(906px)}}}} @media(prefers-reduced-motion:reduce){{.scan{{animation:none;opacity:0}}}}</style>
<rect width="1000" height="{height}" rx="16" fill="{BG}"/><rect x=".5" y=".5" width="999" height="{height-1}" rx="16" fill="none" stroke="{LINE}"/>{body}</svg>\n'''


def render(data):
    days = [d for w in data['calendar']['weeks'] for d in w['contributionDays']]
    count = data['calendar']['totalContributions']
    active = sum(d['contributionCount'] > 0 for d in days)
    date_range = f'{data["from"]} — {data["to"]} · UTC'
    body = label(32, 38, 'GITHUB / FIELD NOTES', 13, CYAN, 'letter-spacing="2"')
    body += label(32, 66, date_range, 14, MUTED)
    for x, value, name in [(32, f'{count:,}', 'contributions'), (280, active, 'active days'),
                            (528, data['repositories'], 'public original repos'), (776, data['stars'], 'stars on those repos')]:
        body += label(x, 125, value, 36) + label(x, 153, name, 14, MUTED)
    body += label(32, 194, 'GitHub-defined contributions · repository totals are a current snapshot', 13, MUTED)
    outputs = {'overview.svg': svg('GitHub activity overview', f'{count} contributions; {active} active days. {date_range}', 220, body)}
    body = label(32, 39, 'CONTRIBUTION CALENDAR', 14, CYAN, 'letter-spacing="2"') + label(32, 65, date_range, 14, MUTED)
    colors = {'NONE': '#192a38', 'FIRST_QUARTILE': '#174a55', 'SECOND_QUARTILE': '#247884', 'THIRD_QUARTILE': '#38acb8', 'FOURTH_QUARTILE': CYAN}
    for wi, week in enumerate(data['calendar']['weeks']):
        for day in week['contributionDays']:
            x, y = 48 + wi * 17, 92 + day['weekday'] * 19
            body += f'<rect x="{x}" y="{y}" width="13" height="15" rx="3" fill="{colors[day["contributionLevel"]]}"><title>{day["date"]}: {day["contributionCount"]} contributions</title></rect>'
    body += '<rect class="scan" x="45" y="87" width="2" height="139" fill="#d7feff" opacity=".45"/>'
    body += label(32, 261, 'One square = one day · intensity follows GitHub’s contribution levels', 13, MUTED)
    for i, color in enumerate(colors.values()):
        body += f'<rect x="{848+i*19}" y="248" width="13" height="13" rx="3" fill="{color}"/>'
    outputs['contributions.svg'] = svg('Daily GitHub contributions', f'{date_range}. {count} GitHub-defined contributions. Animated scan is decorative.', 286, body)
    ranked = sorted(data['language_bytes'].items(), key=lambda pair: (-pair[1], pair[0]))
    total = sum(value for _, value in ranked)
    shown = ranked[:6]
    if len(ranked) > 6:
        shown.append(('Other', sum(value for _, value in ranked[6:])))
    body = label(32, 39, 'LANGUAGES / REPOSITORY BYTES', 14, CYAN, 'letter-spacing="2"')
    body += label(32, 66, 'Owned public non-fork repos · includes archived repos · not a measure of proficiency', 14, MUTED)
    for i, (name, value) in enumerate(shown):
        y = 105 + i * 32
        body += label(32, y+4, name, 15)
        body += f'<rect x="230" y="{y-10}" width="580" height="12" rx="6" fill="{PANEL}"/><rect x="230" y="{y-10}" width="{580*value/total:.2f}" height="12" rx="6" fill="{CYAN}"/>'
        body += label(840, y+4, f'{value/total:.1%}', 14, MUTED)
    if not total:
        body += label(32, 110, 'No language bytes reported by GitHub.', 16, MUTED)
    height = max(180, 132 + len(shown)*32)
    body += label(32, height-24, f'{total:,} bytes indexed · snapshot {data["generated_at"][:10]}', 13, MUTED)
    outputs['languages.svg'] = svg('Repository language distribution', 'Language byte share from GitHub REST languages endpoint. ' + data['scope'], height, body)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default='daniandraaa')
    args = parser.parse_args()
    # Collect everything before writing: failures leave the last good assets intact.
    data = collect(args.username, datetime.now(timezone.utc))
    rendered = render(data)
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    for name, content in rendered.items():
        (assets / name).write_text(content, encoding='utf-8')
    (assets / 'github-data.json').write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: data[k] for k in ('generated_at', 'from', 'to', 'repositories', 'stars')}))
    print('Contributions:', data['calendar']['totalContributions'])


if __name__ == '__main__':
    main()
