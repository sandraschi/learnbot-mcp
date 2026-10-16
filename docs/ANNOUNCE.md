# Announce pilot - learnbot-mcp -> #fleet-learnbot

Target channel: `#fleet-learnbot` (`1558203571894362129`).
Transport: local discord-mcp backend (`http://127.0.0.1:10756`, NSSM service `discord-mcp`).
No token in repo.

## Recipes

```powershell
# preview (no send)
just announce-dry "hello fleet"
just announce-file-dry "reports/announce-draft-abc123.md"

# send (after editing the draft)
just announce "hello fleet"
just announce-file "reports/announce-draft-abc123.md"

# install the post-commit hook (one time per clone)
just install-announce-hook
```

Channel override: `$env:ANNOUNCE_CHANNEL = '<channel-id>'`.

## What fires automatically

Nothing sends automatically. The `post-commit` hook calls
`scripts/check-announce.ps1`, which detects a *major* commit:

- subject matches `^feat[(...)]?[!]?:` AND
- touches `src/learnbot_mcp/`, `scripts/`, `docs/TOOLS.md`,
  `webapp/public/ui-map.json` or `pyproject.toml`

On major it writes `reports/announce-draft-<sha>.md` and prints the exact
`just announce` command. Edit the draft, then send. `chore`/`docs`/`fix`
commits never draft.

## Why this shape

- discord-mcp rate limits: 10/min global, 3/min per channel, 5s interval.
  `announce-discord.ps1` chunks at 1900 chars and sleeps 6s between chunks.
- ASCII hygiene enforced at send (em/en dashes, smart quotes normalized).
- Backend down = clear POST error, commit unaffected (hook never fails).
