import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AnalyticsTests(unittest.TestCase):
    def test_public_nonfork_language_totals(self):
        script = ROOT / 'scripts/generate_analytics.py'
        self.assertTrue(script.exists(), 'analytics generator is missing')
        spec = importlib.util.spec_from_file_location('analytics', script)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        repos = [
            {'name': 'original', 'private': False, 'fork': False, 'stargazers_count': 3},
            {'name': 'fork', 'private': False, 'fork': True, 'stargazers_count': 99},
            {'name': 'secret', 'private': True, 'fork': False, 'stargazers_count': 9},
        ]
        calls = []
        def languages(repo):
            calls.append(repo['name'])
            return {'Python': 120, 'Go': 80}
        result = module.summarize_repositories(repos, languages)
        self.assertEqual(result, {'repositories': 1, 'stars': 3, 'language_bytes': {'Python': 120, 'Go': 80}})
        self.assertEqual(calls, ['original'])

    def test_svg_assets_are_self_contained_and_accessible(self):
        import xml.etree.ElementTree as ET
        for name in ('overview.svg', 'contributions.svg', 'languages.svg'):
            source = (ROOT / 'assets' / name).read_text()
            element = ET.fromstring(source)
            self.assertEqual(element.tag, '{http://www.w3.org/2000/svg}svg')
            self.assertIsNotNone(element.find('{http://www.w3.org/2000/svg}title'))
            self.assertNotIn('<script', source)
            self.assertNotIn('<image', source)
            self.assertNotIn('href=', source)
        calendar = (ROOT / 'assets/contributions.svg').read_text()
        self.assertIn('prefers-reduced-motion', calendar)
        self.assertIn('@keyframes scan', calendar)

    def test_snapshot_calendar_totals_and_scope(self):
        import json
        from datetime import date
        data = json.loads((ROOT / 'assets/github-data.json').read_text())
        days = [day for week in data['calendar']['weeks'] for day in week['contributionDays']]
        self.assertEqual(len(days), 365)
        self.assertEqual(len({d['date'] for d in days}), 365)
        self.assertEqual(sum(d['contributionCount'] for d in days), data['calendar']['totalContributions'])
        self.assertEqual((date.fromisoformat(data['to']) - date.fromisoformat(data['from'])).days, 364)
        self.assertIn('non-fork', data['scope'])
        self.assertTrue(all(value >= 0 for value in data['language_bytes'].values()))

    def test_readme_has_only_local_images_and_valid_local_links(self):
        import re
        from urllib.parse import urlparse
        source = (ROOT / 'README.md').read_text()
        images = re.findall(r'<img[^>]+src="([^"]+)"', source)
        images += re.findall(r'!\[[^\]]*\]\(([^)]+)\)', source)
        self.assertGreaterEqual(len(images), 5)
        for image in images:
            self.assertFalse(urlparse(image).scheme, image)
            self.assertTrue((ROOT / image).is_file(), image)
        for link in re.findall(r'\]\(([^)]+)\)', source):
            if not urlparse(link).scheme and not link.startswith('#'):
                self.assertTrue((ROOT / link).is_file(), link)
        self.assertIn('mailto:daniandraprayudisty@gmail.com', source)
        self.assertIn('linkedin.com/in/daniandra-prayudisty', source)
        self.assertIn('youtube.com/@daniandraprayudisty6466', source)
        self.assertIn('src="profile.jpg"', source)

    def test_gif_has_real_frames_and_loops(self):
        import struct
        data = (ROOT / 'assets/hero.gif').read_bytes()
        self.assertIn(data[:6], (b'GIF87a', b'GIF89a'))
        self.assertIn(b'NETSCAPE2.0', data)
        self.assertEqual(struct.unpack('<HH', data[6:10]), (1200, 330))
        pos = 13
        if data[10] & 128:
            pos += 3 * 2 ** ((data[10] & 7) + 1)
        frames = 0
        while data[pos] != 0x3B:
            marker = data[pos]
            pos += 1
            if marker == 0x21:
                pos += 1
            elif marker == 0x2C:
                packed = data[pos + 8]
                pos += 9
                if packed & 128:
                    pos += 3 * 2 ** ((packed & 7) + 1)
                pos += 1
                frames += 1
            else:
                self.fail(f'Unexpected GIF block {marker}')
            while data[pos]:
                pos += 1 + data[pos]
            pos += 1
        self.assertEqual(frames, 48)


if __name__ == '__main__':
    unittest.main()
