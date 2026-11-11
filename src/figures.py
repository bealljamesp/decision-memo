"""Static figures for the memo.

Usage:
    python src/figures.py --acs data/raw/acs_2024_06037.json --fhfa data/raw/fhfa_hpi_31084.json \
        --mortgage-rate 0.065 --out memo/figures

Figure 1: five-year buy advantage for each down payment share, at trailing and fixed growth.
Figure 2: heatmap of five-year buy advantage (20% down) across mortgage rates and price growth,
with the zero contour marking the break-even line.

Colors: the advantage is signed around zero, so it uses a diverging purple-orange map with
a neutral midpoint at zero. Bars use the Okabe-Ito blue and orange, which stay distinct under
the common forms of color-vision deficiency.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402

from model import Assumptions, compare_rent_vs_buy, trailing_one_year_growth  # noqa: E402
from sensitivity import DEFAULT_GROWTHS, DEFAULT_RATES, advantage_grid  # noqa: E402

INK = "#1f1f1f"
MUTED = "#6b6b6b"
BAR_COLORS = {0.20: "#0072B2", 0.05: "#E69F00"}  # Okabe-Ito blue and orange
DIVERGING = "PuOr"


def figure_down_payment(price0, rent0, a, growth_trailing, growth_fixed, out_path: Path) -> None:
    labels = [f"{d:.0%} down" for d in BAR_COLORS]
    scenarios = [("Trailing FHFA growth", growth_trailing), (f"{growth_fixed:.0%} growth", growth_fixed)]
    width = 0.36
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    for i, (scenario_label, g) in enumerate(scenarios):
        values = [compare_rent_vs_buy(price0, rent0, g, a, d)["buy_advantage"] for d in BAR_COLORS]
        xs = [j + (i - 0.5) * width for j in range(len(BAR_COLORS))]
        for x, value, down in zip(xs, values, BAR_COLORS):
            ax.bar(
                x,
                value / 1000,
                width=width * 0.92,
                color=BAR_COLORS[down],
                alpha=1.0 if i == 0 else 0.45,
                edgecolor="white",
                linewidth=1.0,
            )
            ax.annotate(
                f"{value / 1000:+,.0f}k",
                (x, value / 1000),
                xytext=(0, 4 if value >= 0 else -12),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=INK,
            )
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_xticks(range(len(BAR_COLORS)), labels)
    ax.set_ylabel("Buy advantage over renting, $ thousands", color=INK)
    ax.set_title("Five-year buy advantage by down payment", loc="left", color=INK, fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=INK)
    # Leave headroom above zero so the legend sits clear of the bars and their labels.
    lo, hi = ax.get_ylim()
    span = hi - lo
    ax.set_ylim(lo - 0.05 * span, hi + 0.35 * span)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#777777", alpha=1.0),
        plt.Rectangle((0, 0), 1, 1, color="#777777", alpha=0.45),
    ]
    ax.legend(
        handles,
        [s[0] for s in scenarios],
        frameon=False,
        loc="upper right",
        ncol=2,
        fontsize=8,
        labelcolor=INK,
    )
    fig.text(0.01, 0.01, "Base mortgage rate. Solid bars: trailing growth. Faded bars: fixed growth.", color=MUTED, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_path)
    plt.close(fig)


def figure_heatmap(price0, rent0, a, out_path: Path) -> None:
    grid = advantage_grid(price0, rent0, a, DEFAULT_RATES, DEFAULT_GROWTHS, down_share=0.20)
    values_k = [[v / 1000 for v in row] for row in grid]
    limit = max(abs(v) for row in values_k for v in row)
    norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=200)
    image = ax.imshow(values_k, cmap=DIVERGING, norm=norm, aspect="auto", origin="lower")
    ax.set_xticks(range(len(DEFAULT_GROWTHS)), [f"{g:.0%}" for g in DEFAULT_GROWTHS], fontsize=8)
    ax.set_yticks(range(len(DEFAULT_RATES)), [f"{r:.1%}" for r in DEFAULT_RATES], fontsize=8)
    ax.set_xlabel("Annual home price growth", color=INK)
    ax.set_ylabel("Mortgage rate", color=INK)
    ax.set_title("Five-year buy advantage, 20% down ($ thousands)", loc="left", color=INK, fontsize=11)
    for i, row in enumerate(values_k):
        for j, value in enumerate(row):
            # Dark ink on light cells, white on the saturated ends of the scale.
            text_color = "white" if abs(value) > 0.6 * limit else INK
            ax.text(j, i, f"{value:,.0f}", ha="center", va="center", fontsize=6.5, color=text_color)
    ax.contour(
        range(len(DEFAULT_GROWTHS)),
        range(len(DEFAULT_RATES)),
        values_k,
        levels=[0.0],
        colors=INK,
        linewidths=1.4,
    )
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Buy advantage, $ thousands", color=INK)
    cbar.outline.set_visible(False)
    fig.text(0.01, 0.01, "Black line: break-even. Purple cells: buying wins. Orange cells: renting wins.", color=MUTED, fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_path)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--acs", type=Path, required=True)
    parser.add_argument("--fhfa", type=Path, required=True)
    parser.add_argument("--mortgage-rate", type=float, required=True)
    parser.add_argument("--fixed-growth", type=float, default=0.03, help="second growth scenario for figure 1")
    parser.add_argument("--out", type=Path, default=Path("memo/figures"))
    args = parser.parse_args(argv)

    acs = json.loads(args.acs.read_text())
    growth = trailing_one_year_growth(json.loads(args.fhfa.read_text())["rows"])
    a = Assumptions(mortgage_rate=args.mortgage_rate)
    args.out.mkdir(parents=True, exist_ok=True)

    price0, rent0 = acs["median_home_value"], acs["median_gross_rent"]
    figure_down_payment(price0, rent0, a, growth, args.fixed_growth, args.out / "fig1_buy_advantage_by_down.png")
    figure_heatmap(price0, rent0, a, args.out / "fig2_sensitivity_heatmap.png")
    print(f"Wrote figures to {args.out}")


if __name__ == "__main__":
    main()
