#!/usr/bin/env python3
"""Validate the public GPU Rental Market Monitor data contract and static rendering."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'gpu' / 'data.json'
HTML_PATH = ROOT / 'gpu' / 'index.html'
ROOT_HTML_PATH = ROOT / 'index.html'

EXPECTED_VARIANTS = ['H200', 'H100 SXM', 'H100 NVL', 'A100 SXM', 'RTX 5090', 'RTX 4090']


class TagBalance(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag not in self.VOID:
            if not self.stack or self.stack[-1] != tag:
                self.errors.append((tag, self.stack[-5:]))
            else:
                self.stack.pop()


def section(html, marker_id):
    m = re.search(
        rf'<div class="tbl-wrap" id="{marker_id}">(.*?</table>)(?:\s*<div class="table-asof">.*?</div>)?\s*</div>',
        html,
        flags=re.S,
    )
    assert m, marker_id
    return m.group(1)


def fmt(n):
    return f'${n:.2f}'


def main():
    data = json.loads(DATA_PATH.read_text())
    html = HTML_PATH.read_text()
    root_html = ROOT_HTML_PATH.read_text()
    assert 'GPU Rental Market Monitor</a>' in root_html
    assert 'provider-attributed GPU rental price levels' in root_html

    # --- schema shape -----------------------------------------------------
    assert data['schema_version'] == 2
    providers = data['providers']
    assert set(providers.keys()) == {'vast', 'runpod', 'lambda'}, 'must have exactly 3 sources'
    assert len(providers) == 3

    variants = data['comparable_variants']
    assert len(variants) == 6, 'must have exactly six comparable GPU variants'
    assert [v['variant'] for v in variants] == EXPECTED_VARIANTS

    thresh = data['eligibility_rules']['thin_market_threshold_offers']
    assert thresh == 5

    # --- eligibility / thin-market / bundle rules, recomputed -------------
    thin_count = 0
    bundle_count = 0
    na_count = 0
    for v in variants:
        rows_by_provider = {}
        for row in v['rows']:
            rows_by_provider.setdefault(row['provider'], []).append(row)

        vast_row = rows_by_provider['vast'][0]
        if vast_row['usd_per_hr'] is None:
            assert vast_row['eligible'] is False and vast_row['badge'] == 'n/a'
            na_count += 1
        elif vast_row['offers'] < thresh:
            assert vast_row['eligible'] is False and vast_row['badge'] == 'thin market'
            thin_count += 1
        else:
            assert vast_row['eligible'] is True and vast_row['badge'] is None

        for rp_row in rows_by_provider['runpod']:
            assert rp_row['eligible'] is True and rp_row['badge'] is None

        lambda_row = rows_by_provider['lambda'][0]
        if lambda_row['usd_per_hr'] is None:
            assert lambda_row['eligible'] is False and lambda_row['badge'] == 'n/a'
            na_count += 1
        else:
            assert lambda_row['eligible'] is False and lambda_row['badge'] == '8x bundle'
            bundle_count += 1

        # band recomputed strictly from eligible rows only, never averaged
        eligible_vals = [row['usd_per_hr'] for row in v['rows'] if row['eligible']]
        assert eligible_vals, v['variant']
        assert v['band']['min_usd_per_hr'] == min(eligible_vals)
        assert v['band']['max_usd_per_hr'] == max(eligible_vals)
        assert v['band']['source_count'] == len(eligible_vals)
        assert v['band']['min_display'] == fmt(v['band']['min_usd_per_hr'])
        assert v['band']['max_display'] == fmt(v['band']['max_usd_per_hr'])

    assert thin_count == 3, 'Vast rows below the thin-market threshold must be exactly 3'
    assert bundle_count == 2, 'Lambda 8x-bundle comparable rows must be exactly 2'
    assert na_count == 5, 'n/a cells across Vast/Lambda in the comparable table must be exactly 5'

    # --- comparable table: exact value -> HTML mapping ---------------------
    cmp_html = section(html, 'comparable-table')
    assert cmp_html.count('>thin market') == thin_count
    assert cmp_html.count('>8x bundle<') == bundle_count
    assert cmp_html.count('class="na-badge"') == na_count

    for v in variants:
        row_match = re.search(
            rf'<tr>\s*<td class="model">{re.escape(v["variant"])}</td>(.*?)</tr>',
            cmp_html,
            flags=re.S,
        )
        assert row_match, v['variant']
        row = row_match.group(0)
        for r in v['rows']:
            assert r['usd_per_hr_display'] in row, (v['variant'], r['provider'], r['usd_per_hr_display'])
        assert v['band']['min_display'] in row and v['band']['max_display'] in row
        assert f">{v['band']['source_count']}</td>" in row

    # --- RunPod: all eight tiers, both product lines, sixteen rate values -
    runpod = providers['runpod']
    assert len(runpod['pricing_sheet']) == 8
    for tier in runpod['pricing_sheet']:
        c = fmt(tier['community_usd_per_hr'])
        s = fmt(tier['secure_usd_per_hr'])
        assert c in html, f'RunPod community rate missing from HTML: {tier["model"]} {c}'
        assert s in html, f'RunPod secure rate missing from HTML: {tier["model"]} {s}'

    # --- Lambda pricing sheet present ---------------------------------------
    lam = providers['lambda']
    assert len(lam['pricing_sheet']) == 5
    for tier in lam['pricing_sheet']:
        assert fmt(tier['usd_per_gpu_hr']) in html, tier['model']

    # --- source links --------------------------------------------------------
    # Vast's source_url is a raw API endpoint (not a human-facing page), so its
    # required clickable link is docs_url instead; the other two sources link
    # their own pricing page directly.
    required_links = {
        'vast': ('homepage_url', 'docs_url'),
        'runpod': ('source_url',),
        'lambda': ('source_url',),
    }
    for key, link_keys in required_links.items():
        p = providers[key]
        for link_key in link_keys:
            assert f'href="{p[link_key]}"' in html, (key, link_key)

    # --- no blended / market-clearing language --------------------------------
    # The page is allowed to *disclaim* blending/averaging/clearing (e.g. "not a
    # blended index"), but every occurrence must sit next to a negation word --
    # an un-negated occurrence would mean the page is claiming to *be* one.
    lowered = html.lower()
    negations = ('not a', 'not the', 'never', 'no ', "isn't", 'is not')
    for forbidden in (
        'blended',
        'market-clearing',
        'market clearing',
        'pooled',
        'weighted average',
        'single clearing price',
        'cheapest gpu is',
        'cheapest-gpu',
        'across all providers is $',
    ):
        start = 0
        while True:
            idx = lowered.find(forbidden, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 30):idx]
            assert any(neg in window for neg in negations), (forbidden, window)
            start = idx + 1

    # --- required copy --------------------------------------------------------
    for required in (
        '<title>GPU Rental Market Monitor',
        'Comparable provider snapshot',
        'Vast.ai median (verified, 1× GPU)',
        'How to read the snapshot',
        'Vast marketplace detail',
        'Methodology / limitations',
        'not a blended market index and not a cheapest-GPU finder',
        'not a single settled rate for any GPU model',
        'no verified offer',
        'thin market and excluded from headline rankings',
    ):
        assert required in html, required

    # --- historical Vast-only detail table (unchanged snapshot) --------------
    hist = data['vast_historical_detail']
    gpus = hist['gpus']
    assert hist['price_label'] == 'listed offer $/hr'
    assert hist['thin_market_threshold_offers'] == 5
    assert 'Not normalized' in hist['normalization_status']
    assert 'cannot independently reproduce' in hist['reproducibility_status']
    assert len(gpus) == 18
    assert sum(gpu['offers'] for gpu in gpus) == 60
    assert sum(gpu['offers'] < hist['thin_market_threshold_offers'] for gpu in gpus) == 16

    hist_html = section(html, 'historical-table')
    for gpu in gpus:
        row_match = re.search(
            rf'<tr><td class="model">{re.escape(gpu["model"])}</td>(.*?)</tr>',
            hist_html,
            flags=re.S,
        )
        assert row_match, gpu['model']
        row = row_match.group(0)
        displayed_change = gpu['change_since_first_observation_pct_text'].removeprefix('— ')
        displayed_days = 'n/a' if gpu['days_observed'] is None else str(gpu['days_observed'])
        assert f'<td class="{gpu["change_direction"]}">{displayed_change}</td>' in row
        assert f'<td>{displayed_days}</td>' in row
        assert f'<td>{gpu["offers"]}' in row
        assert f'${gpu["median_usd_per_hr"]:.3f}' in row
        assert f'${gpu["min_usd_per_hr"]:.3f}' in row
        assert f'>{gpu["dlperf_per_dollar"]:,}</td>' in row

    assert len(re.findall(r'>thin</span>', hist_html)) == 16

    # --- balanced HTML ---------------------------------------------------------
    balance = TagBalance()
    balance.feed(html)
    assert not balance.errors and not balance.stack, (balance.errors, balance.stack)

    print(
        'PASS: 3 sources, 6 comparable variants (3 thin / 2 bundle / 5 n/a), '
        '16 RunPod rates, 5 Lambda rates, 18 historical records, 60 historical offers, '
        '16 historical thin rows, schema/render contract, source links, no blended language, '
        'balanced HTML'
    )


if __name__ == '__main__':
    main()
