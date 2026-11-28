# Profile assets

All README images are local files. No statistics renderer, icon CDN, font service, or snake output branch is required.

## Refresh analytics

Requirements: Python 3.10+ and an authenticated GitHub CLI (`gh auth login` locally, or `GH_TOKEN` in Actions). No pip packages are required.

```sh
python scripts/generate_analytics.py --username daniandraaa
python -m unittest discover -s tests -v
```

The generator fetches a 365-day UTC contribution calendar via GraphQL, paginates all public owned repositories via REST, filters forks, then requests every eligible repository's language bytes. Archived repositories are included. It rejects an incomplete calendar or a contribution total mismatch. No estimated statistics are substituted after errors. All network requests complete before any output assets are written; a failed collection leaves the previous snapshot untouched.

`assets/github-data.json` is the reproducible data snapshot; `overview.svg`, `contributions.svg`, and `languages.svg` are rendered from it. Tests cover metric scope, calendar integrity, self-contained parseable SVGs, local README image/link targets, corrected contact links, and the GIF's frame count and loop extension. Charts have accessible titles/descriptions and ordinary SVG geometry, so animation is not required to read any data. The calendar scan respects reduced-motion preferences. The GIF itself cannot obey that preference; it uses subtle motion and no flashing.

## Daily automation

`.github/workflows/analytics.yml` runs daily at 06:23 UTC, on manual dispatch, and when generator/tests/workflow source changes on main. GitHub schedules are best-effort and may be delayed. The workflow uses Python and the runner's preinstalled `gh`; it grants `contents: write` explicitly and commits only the four analytics artifacts to main. Analytics-only commits do not retrigger the workflow.

The built-in GitHub token is sufficient for public API data. It does not grant access to private repositories elsewhere. Calendar visibility can differ from a personal token; GitHub's own contribution settings apply. If branch protection forbids bot pushes, allow this workflow or change delivery to a pull request. A concurrent human push can reject the bot's non-force push; rerun the workflow rather than force pushing. This workflow has not been remotely executed as part of a local-only update.

The previous snake workflow was removed: the new contribution calendar replaces that fragile output-branch dependency. Older decorative assets are retained, but are no longer referenced in the README.

## Rebuild the decorative hero

The 48-frame, 1200 × 330 GIF is prebuilt and versioned; daily analytics do not rebuild it or install Pillow.

```sh
python -m pip install 'Pillow>=10,<14'
python scripts/generate_hero.py
python -m unittest discover -s tests -v
```

Pillow's DejaVu Sans fonts are used with no network fonts. The cyan signal is abstract decoration, not activity data. Preserve `profile.jpg` and the corrected contact URLs in the README when editing the layout.
