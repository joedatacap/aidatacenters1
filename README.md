# The AI Receipts

A free, public, single-page ledger of the US AI data-center buildout — announced vs.
delivered, with every figure traced back to a dated, sourced event.

- `data.json` — the source of record. Every site, every dated event, every source
  link, plus the aggregate stats (sites tracked, announced capex, MW live vs.
  planned) shown on the page.
- `index.html` — a standalone, static page rendered from `data.json` by hand. No
  build step, no framework, no runtime fetch — open it directly in a browser or
  serve it as-is.

Coverage is curated, not exhaustive: sites are included only when they have
verifiable, linkable public sourcing. See the Methodology and Limitations
sections on the page for details.

## Hosting: GitHub Pages with a custom domain

This repo is served at **aidc.datacap.xyz** via GitHub Pages.

1. **DNS** — at the domain registrar/DNS provider for `datacap.xyz`, add a `CNAME`
   record for the `aidc` subdomain pointing at `<github-username>.github.io`.
2. **Repo config** — the `CNAME` file at the repo root (this file, containing just
   `aidc.datacap.xyz`) tells GitHub Pages which custom domain to serve. Keep it in
   sync with whatever's configured in the repo's Settings → Pages → Custom domain
   field — GitHub will otherwise overwrite or flag it on the next deploy.
3. **Enable Pages** — in Settings → Pages, set the source to the branch/folder
   containing `index.html` and `CNAME` (repo root). GitHub issues a Let's Encrypt
   TLS cert for the custom domain automatically once DNS resolves; check "Enforce
   HTTPS" once the certificate is ready.
4. **Verify** — GitHub Pages serves `index.html` at `/` automatically, so
   `https://aidc.datacap.xyz/` should load the ledger directly.

## Updating the ledger (manual, monthly)

There's no automation — this is a manual, monthly pass:

1. For each site in `data.json`, check for new public developments (news,
   filings, permits, company statements) since `last_verified`.
2. Append new dated `events` entries with a real, checkable `source` URL,
   `source_type`, and `confidence` rating (see Methodology in `index.html` for
   the rubric). Update `stage`, `mw_live`, `power_status`, `consent_status`, and
   `last_verified` on the site if they've changed.
3. Recompute `aggregate_stats` (`sites_tracked`, `announced_capex_usd_b`,
   `announced_capex_sites`, `mw_live_observed`, `mw_planned_total`,
   `pct_delivered`, `pct_reached_construction`, `pct_operational`) from the
   updated `sites` array.
4. Hand-edit `index.html` to reflect any changed headline numbers, the top-sites
   selection, and the receipts list, and bump the `updated` date in both files.
5. Commit and push — GitHub Pages redeploys automatically.

## GPU Price Index (`/gpu/`)

A second, independent page: a static snapshot of Vast.ai on-demand listings at
**aidc.datacap.xyz/gpu/**.

- `gpu/data.json` records listed-offer median/minimum $/hr, offer count, days
  observed, and change since first observation. It also carries explicit
  normalization, reproducibility, and thin-market limits.
- `gpu/index.html` is a standalone static page. A small local script only
  calculates the visible freshness badge; it makes no provider fetch.
- `gpu/validate.py` checks JSON validity, table/data correspondence, 18 records,
  60 offers, the 16 thin-market rows, HTML nesting, and the current methodology
  claims. Run it before every publish.

**Refresh is manual, not automated.** The underlying snapshot is derived from a
private internal tracker; this repo holds a public-safe export. There is no
script or CI job that pulls fresh provider data. To refresh:

1. Re-derive the latest values from the private source and retain a normalized,
   append-only raw offer snapshot outside this public repo when possible.
2. Update `gpu/data.json` with the new records, exact observation dates, source
   metadata, and the current normalization/reproducibility statement.
3. Update `gpu/index.html` so its table, takeaways, snapshot timestamp, and
   `data-snapshot` freshness attribute match the export.
4. Run `python3 gpu/validate.py` from the repository root, then commit and push
   the changed files together.

**Second-provider policy.** Do not blend Vast.ai marketplace offers with a
fixed-price provider into one median. If a second source is added, publish a
separate, clearly labelled provider panel with its own source URL, configuration,
price unit, capture time, and comparable GPU cohort. Start with a small RunPod
on-demand reference set only after its data contract is documented and
reproducible.

## Stage map (`/`)

The root page includes a static, interactive stage map of the named sites in the ledger. Its pin positions, stage, and disclosed MW values are hand-rendered from `data.json`; it makes no map-API or network request. When refreshing the ledger, update the map pin/data payload and verify the named-site count, the undisclosed-site note, stage colors, and the selected-pin panel before publishing.

## Social card (`assets/aidc-social-card.png`)

`assets/aidc-social-card.html` is the self-contained (no framework, no external
image/map dependency), fixed 1200x630 source for the Open Graph / Twitter card
image referenced in `index.html`'s `<head>`. It hand-codes the same headline
numbers as the ledger (sites tracked, announced capex, delivered %) plus a
restrained abstract US stage-map motif in the site's stage colors.

**Regenerate the PNG whenever a headline number changes** (sites tracked,
announced capex, delivered %) or the stage-map motif goes stale relative to
`data.json`:

1. Hand-edit the stat values (and map dots, if warranted) in
   `assets/aidc-social-card.html` to match the updated `data.json`.
2. Render it to `assets/aidc-social-card.png` at exactly 1200x630 — e.g. with
   Playwright:
   ```
   python3 -c "
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       b = p.chromium.launch()
       page = b.new_page(viewport={'width':1200,'height':630}, device_scale_factor=1)
       page.goto('file://' + __import__('os').path.abspath('assets/aidc-social-card.html'))
       page.screenshot(path='assets/aidc-social-card.png')
       b.close()
   "
   ```
3. Confirm the output is still 1200x630 and commit both files together.
