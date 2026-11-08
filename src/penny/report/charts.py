from html import escape


def quote_chart(low: int, high: int, actual: int) -> str:
    scale = max(high, actual, 1)

    def width(v):
        return round(v / scale * 540, 2)

    return f'''<svg viewBox="0 0 600 100" role="img" aria-labelledby="quote-title quote-desc"><title id="quote-title">Quote versus actual tokens</title><desc id="quote-desc">Estimate {low} to {high} tokens; actual {actual} tokens.</desc><rect x="30" y="20" width="{width(high)}" height="22" rx="4" fill="var(--line)"/><rect x="30" y="54" width="{width(actual)}" height="22" rx="4" class="chartbar"/><text x="30" y="96" font-size="12" fill="currentColor">Estimate range {low:,}–{high:,} · Actual {actual:,}</text></svg>'''


def grouped(rows: list[dict], metric: str) -> str:
    max_value = max([r.get(metric) or 0 for r in rows] + [1])
    height = len(rows) * 42 + 40
    bars = []
    for n, row in enumerate(rows):
        value = row.get(metric)
        label = f"{row['task']} / {row['agent']}: {value if value is not None else 'price not configured'}"
        bars.append(
            f'<text x="8" y="{n * 42 + 18}" fill="currentColor" font-size="12">{escape(label)}</text><rect x="8" y="{n * 42 + 24}" width="{(value or 0) / max_value * 570:.2f}" height="10" class="{"chartbar" if row["agent"] == "penny" else "chartbaseline"}"/>'
        )
    return f'<svg viewBox="0 0 600 {height}" role="img" aria-label="{escape(metric)} by task and agent"><title>{escape(metric)} comparison</title><desc>Bars show observed means; text provides each value.</desc>{"".join(bars)}</svg>'
