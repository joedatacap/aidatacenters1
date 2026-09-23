#!/usr/bin/env python3
"""Validate the public GPU snapshot data contract and static rendering."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'gpu' / 'data.json'
HTML_PATH = ROOT / 'gpu' / 'index.html'


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


def main():
    data = json.loads(DATA_PATH.read_text())
    html = HTML_PATH.read_text()
    gpus = data['gpus']

    assert data['price_label'] == 'listed offer $/hr'
    assert data['thin_market_threshold_offers'] == 5
    assert 'Not normalized' in data['normalization_status']
    assert 'cannot independently reproduce' in data['reproducibility_status']
    assert len(gpus) == 18
    assert sum(gpu['offers'] for gpu in gpus) == 60
    assert sum(gpu['offers'] < data['thin_market_threshold_offers'] for gpu in gpus) == 16

    for gpu in gpus:
        assert 'days_observed' in gpu
        assert 'change_since_first_observation_pct_text' in gpu
        row_match = re.search(
            rf'<tr><td class="model">{re.escape(gpu["model"])}</td>(.*?)</tr>',
            html,
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

    balance = TagBalance()
    balance.feed(html)
    assert not balance.errors and not balance.stack, (balance.errors, balance.stack)

    for required in (
        'Median listed offer $/hr by GPU model',
        'A hand-refreshed snapshot of Vast.ai on-demand listings:',
        'Change since first observation',
        'Days observed',
        'data-snapshot="2026-09-21T10:00:00Z"',
        'freshness badge becomes stale after 24 hours',
        'thin market and excluded from headline rankings',
    ):
        assert required in html, required
    for forbidden in (
        'source of record',
        'per GPU-hour',
        'actual market clearing',
        'Vast.ai itself already excludes',
        'Δ 44d',
        'GPU rental prices from Vast.ai',
        'with 44-day trend',
    ):
        assert forbidden not in html, forbidden
    assert len(re.findall(r'>thin</span>', html)) == 16
    print('PASS: 18 records, 60 offers, 16 thin rows, schema/render contract, balanced HTML, and methodology claims')


if __name__ == '__main__':
    main()
