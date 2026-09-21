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
