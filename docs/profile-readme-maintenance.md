# Profile README updater maintenance

The profile README contains generated sections bounded by HTML markers:

- `stats`
- `languages`
- `activity`

The `scripts/update_readme.py` script should only replace content inside those markers. Keep the surrounding profile text human-curated.

## Local checks

```bash
python -m py_compile scripts/update_readme.py
python scripts/update_readme.py
git diff --check
git diff -- README.md
```

The updater calls the public GitHub API and may be affected by rate limits or temporary failures. If an individual section fails, the intended behavior is to preserve that section's previous text. Inspect the diff before accepting a generated change.

## Workflow safety

- The scheduled workflow uses GitHub Actions' short-lived `GITHUB_TOKEN`.
- Never place a personal access token or other secret in the script or README.
- Keep workflow permissions to the minimum required.
- Verify generated output before changing the workflow's schedule or write behavior.
- The workflow's six-hour schedule is for profile freshness, not a promise that every public event will be visible in the API response.

## Troubleshooting

If the README does not update, open the Actions run and inspect the failing step. Test the script locally with `GITHUB_TOKEN` unset to confirm public-API operation, remembering that unauthenticated API rate limits are stricter.
