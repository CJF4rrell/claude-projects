# Hedge Watch

A mobile-friendly FX + crypto rate tracker (EUR, USD, GBP, JPY, CHF, BTC, ETH)
for reviewing historical trends and spotting hedge signals.

- `index.html` — the page itself (static, no build step).
- `data/fx-data.json` — daily EUR-based rates. Fiat from Frankfurter/ECB,
  crypto from Kraken, cross-converted through EUR/USD.
- `scripts/refresh.py` — pulls the prior day's close-of-business rates and
  appends them to `data/fx-data.json`. Run by
  `.github/workflows/hedge-watch-refresh.yml` every morning.

## Hosting

Enable GitHub Pages on this repo (Settings → Pages → Deploy from branch →
`main` → `/ (root)`), then the site is served at:

  https://cjf4rrell.github.io/claude-projects/hedge-watch/

## Refresh schedule

The included GitHub Actions workflow runs daily at 05:00 UTC (06:00
Europe/Dublin during Irish Summer Time) and commits the updated dataset
automatically. It needs "Read and write permissions" enabled under
Settings → Actions → General → Workflow permissions for the commit-back
step to succeed. You can also trigger it manually from the Actions tab
("Run workflow").
