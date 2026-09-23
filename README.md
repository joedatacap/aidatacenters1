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

## GPU Rental Market Monitor (`/gpu/`)

A public, static comparison of provider-attributed GPU rental price levels at
**aidc.datacap.xyz/gpu/**. It is a market monitor, not a blended price index
and not a booking or cheapest-price tool.

### Sources and scope

- **Vast.ai:** public on-demand, verified, rentable, non-rented single-GPU
  marketplace offers. The page shows median listed offer rates, counts, and
  thin-market flags. It is not a transaction-price feed.
- **RunPod:** public Pods pricing only, with Community Pod and Secure Pod
  published separately. Serverless and Clusters are excluded.
- **Lambda:** public self-serve Instances pricing. The currently captured
  entries are per-GPU rates inside an 8x bundle, so they remain provider-native
  context rather than direct single-GPU comparables.

`gpu/data.json` is the public source-of-record export. It contains per-source
capture metadata, source URLs, product labels, eligibility rules, the six-GPU
comparison cohort, and the prior Vast-only historical table. `gpu/index.html`
is a standalone static renderer with no provider fetch. `gpu/validate.py`
checks the source schema, exact rendered values, thin-market/bundle exclusions,
source links, no-blended-language rule, and HTML nesting.

### Reading the matrix

The `Comparable price band` is the low-to-high range of eligible rates in one
GPU row. It never averages or pools provider prices. Vast rows with fewer than
five offers and Lambda 8x bundle rows are visible but excluded from this band.
Each rate retains a source product label, so Community Pod, Secure Pod,
marketplace offer, and bundled instance cannot silently become equivalent.

### Refresh policy

Refresh manually monthly and out of cycle when any material source change occurs:

- a listed rate moves 10% or more;
- a GPU model or product tier is added or removed;
- an availability or billing-minimum rule changes; or
- a source correction is found.

Use a staging capture before publishing: collect source records, update
`gpu/data.json`, run `python3 gpu/validate.py`, inspect the static page on
desktop and mobile, then commit the changed data and renderer together. Keep
the prior valid export if a source becomes unavailable or its format changes.

### Future automation

Do not automate page scraping until the manual contract has survived several
clean refreshes. A future source job should write staging JSON, validate it
against this schema, preserve the last-good public export on failure, and flag
each provider stale independently. The page remains a stateless renderer, never
the source of research.

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
