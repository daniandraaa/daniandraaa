"""Vendor pinned Simple Icons paths into offline, labeled profile strips.

Uses Python's standard library, with system curl as a TLS fallback.
Network is needed only for regeneration.
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import subprocess
from urllib.error import URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSION = '13.21.0'
BASE = f'https://cdn.jsdelivr.net/npm/simple-icons@{VERSION}/'
GROUPS = {
    'languages': ('LANGUAGES', [('Python', 'python', '3776AB'), ('TypeScript', 'typescript', '3178C6'), ('JavaScript', 'javascript', 'F7DF1E'), ('Go', 'go', '00ADD8'), ('PHP', 'php', 'A5ABDA'), ('Dart', 'dart', '54C5F8')]),
    'frameworks': ('WEB / MOBILE', [('React', 'react', '61DAFB'), ('Next.js', 'nextdotjs', 'FFFFFF'), ('Flutter', 'flutter', '54C5F8'), ('Laravel', 'laravel', 'FF5C56'), ('Tailwind CSS', 'tailwindcss', '38BDF8')]),
    'ai-devops': ('AI / DATA / DEVOPS', [('PyTorch', 'pytorch', 'EE4C2C'), ('Docker', 'docker', '2496ED'), ('PostgreSQL', 'postgresql', '74A6CF'), ('Supabase', 'supabase', '3FCF8E'), ('Git', 'git', 'F05032'), ('Linux', 'linux', 'FCC624')]),
}


def fetch(relative):
    try:
        with urlopen(Request(BASE + relative, headers={'User-Agent': 'profile-logo-vendor/1.0'}), timeout=10) as response:
            return response.read()
    except (URLError, TimeoutError):
        # Some sandboxes block Python TLS while permitting the system curl TLS stack.
        return subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                                        '--retry', '2', '--max-time', '45', BASE + relative])


def main():
    items = [item for _, group in GROUPS.values() for item in group]
    with ThreadPoolExecutor(max_workers=6) as pool:
        sources = dict(zip([slug for _, slug, _ in items], pool.map(fetch, ['icons/' + slug + '.svg' for _, slug, _ in items])))
    license_text = fetch('LICENSE.md').decode()
    assert 'CC0' in license_text
    directory = ROOT / 'assets/skills'
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (heading, group) in GROUPS.items():
        labels = ', '.join(label for label, _, _ in group)
        lines = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="178" viewBox="0 0 720 178" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(heading.title())} technology logos</title>',
            f'<desc id="desc">{escape(labels)}. Original Simple Icons brand paths, bundled locally; six-column layout.</desc>',
            '<rect width="720" height="178" rx="16" fill="#080f18"/>',
            '<rect x=".5" y=".5" width="719" height="177" rx="16" fill="none" stroke="#233445"/>',
            f'<text x="20" y="32" fill="#55dce5" font-size="20" letter-spacing="2" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">{heading}</text>',
        ]
        for index, (label, slug, color) in enumerate(group):
            raw = sources[slug]
            svg = ET.fromstring(raw)
            assert svg.get('viewBox') == '0 0 24 24'
            paths = [p.attrib['d'] for p in svg.findall('{http://www.w3.org/2000/svg}path')]
            assert paths and all(paths)
            manifest[label] = {'url': BASE + 'icons/' + slug + '.svg', 'sha256': sha256(raw).hexdigest(), 'paths': paths, 'license': 'CC0-1.0'}
            x = 12 + index * 116
            lines += [f'<g data-brand="{escape(label)}">', f'<rect x="{x}" y="49" width="112" height="113" rx="10" fill="#101d2b" stroke="#233445"/>', f'<g transform="translate({x + 30} 63) scale(2.1666666667)" fill="#{color}">']
            lines += ['<path d="' + escape(d, quote=True) + '"/>' for d in paths]
            lines += ['</g>', f'<text x="{x + 56}" y="145" text-anchor="middle" fill="#e7f0f6" font-size="{18 if len(label) > 9 else 20}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">{escape(label)}</text>', '</g>']
        lines.append('</svg>')
        (ROOT / f'assets/skills-{name}.svg').write_text('\n'.join(lines) + '\n')
    (directory / 'sources.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (directory / 'LICENSE.simple-icons').write_text(license_text)
    attribution = f'''# Technology logo attribution

All 17 brand silhouettes in the three `../skills-*.svg` strips are actual SVG
path data downloaded from **Simple Icons {VERSION}**, distributed under
**CC0 1.0 Universal (CC0-1.0)**. No Devicon artwork is used.

- Upstream: https://github.com/simple-icons/simple-icons
- Pinned package: {BASE}
- Upstream license: {BASE}LICENSE.md
- Preserved license: [LICENSE.simple-icons](LICENSE.simple-icons)
- Exact download URLs, source SHA-256 digests, and original path data:
  [sources.json](sources.json)

The surrounding cards, labels, and colors are profile presentation. Brand paths
are not replaced by letter placeholders; some display colors are lightened for
contrast on the dark background. Brand names and logos remain trademarks of
their respective owners; inclusion does not imply endorsement. CC0 applies to
the icon collection and does not grant trademark rights.

Regenerate from the repository root with `python scripts/generate_skills.py`.
Only regeneration requires network access; the generated SVGs are entirely
self-contained and use no images, external fonts, scripts, or href references.

## Included marks

'''
    attribution += '\n'.join('- ' + label + ': ' + manifest[label]['url'] for label, _, _ in items) + '\n'
    (directory / 'ATTRIBUTION.md').write_text(attribution)
    print(f'Generated 3 self-contained strips with {len(manifest)} upstream logos (Simple Icons {VERSION}).')


if __name__ == '__main__':
    main()
