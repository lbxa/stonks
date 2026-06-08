# ruff: noqa: E501
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

NOTEBOOK_DIR = Path(__file__).parent
DATA_DIR = NOTEBOOK_DIR / "data"


@dataclass(frozen=True)
class NotebookSpec:
    filename: str
    title: str
    cells: tuple[str, ...]


def md(text: str) -> str:
    return dedent(text).strip()


def code(text: str) -> str:
    return dedent(text).strip()


COMMON_IMPORTS = code(
    """
    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    from valuation import (
        MarketPremiumInputs,
        OptionScenario,
        SegmentValuation,
        SotpInputs,
        build_sensitivity_grid,
        market_premium_value,
        probability_weighted_option_value,
        sotp_equity_value,
    )

    DATA_DIR = next(
        candidate / "apps/notebooks/studies/spacex_ipo/data"
        for candidate in (Path.cwd(), *Path.cwd().parents)
        if (candidate / "apps/notebooks/studies/spacex_ipo/data").exists()
    )
    USD_BN = 1_000_000_000
    pd.options.display.float_format = "{:,.2f}".format
    """
)


SOURCE_LOG_NOTEBOOK = NotebookSpec(
    filename="00_source_log_and_sec_extraction.ipynb",
    title="00 Source Log and SEC Extraction",
    cells=(
        md(
            """
            # 00 Source Log and SEC Extraction

            Purpose: maintain an auditable source log and a checklist for turning the
            SpaceX S-1 package into normalized model inputs. This v1 notebook is
            intentionally source-log first: if the S-1 or Reuters pages are not
            reachable, the model still runs from analyst seed assumptions.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            source_log = pd.read_csv(DATA_DIR / "source_log.csv")
            source_log
            """
        ),
        md(
            """
            ## SEC Extraction Checklist

            Normalize the S-1 into tables before replacing seed assumptions:

            - historical consolidated revenue, gross profit, EBITDA, capex and FCF
            - segment revenue and margin disclosure
            - backlog, contract duration, cancellability and customer concentration
            - debt, preferred conversion, RSUs, options, warrants and lockups
            - related-party transactions, governance, voting control and use of proceeds
            """
        ),
        code(
            """
            extraction_fields = pd.DataFrame(
                [
                    ("Historical financials", "Revenue / EBITDA / capex / FCF", "SEC-S1-INDEX"),
                    ("Segment financials", "Starlink / Launch / Defense / AI split", "SEC-S1-INDEX"),
                    ("Capital structure", "Fully diluted shares, debt, cash, SBC", "SEC-S1-INDEX"),
                    ("AI contracts", "Backlog, duration, GPU count, margins", "RTRS-AI-CONTRACTS"),
                    ("IPO context", "Deal size, demand, scarcity setup", "RTRS-IPO-DEMAND"),
                    ("Starshield", "Allied adoption and procurement concentration", "RTRS-STARSHIELD-UK"),
                ],
                columns=["workstream", "required_fields", "primary_source"],
            )
            extraction_fields
            """
        ),
    ),
)


STARLINK_NOTEBOOK = NotebookSpec(
    filename="01_starlink_model.ipynb",
    title="01 Starlink Model",
    cells=(
        md(
            """
            # 01 Starlink Model

            Key question: is Starlink a high-growth telco, satellite utility, or
            capex-heavy broadband network? This notebook builds subscriber revenue,
            network economics, DCF-style FCF, and multiple valuation ranges.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            starlink = assumptions[assumptions["segment"].eq("Starlink")]
            starlink.pivot_table(index="metric", columns="case", values="value", aggfunc="first")
            """
        ),
        code(
            """
            cases = ["bear", "base", "bull"]
            starlink_case = (
                starlink.pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
                .assign(
                    revenue_usd_bn=lambda df: df["2030 subscribers"] * df["2030 ARPU"] * 12 / 1_000,
                    ebitda_usd_bn=lambda df: df["revenue_usd_bn"] * df["EBITDA margin"],
                    fcf_margin=lambda df: df["EBITDA margin"] - [0.12, 0.10, 0.08],
                    fcf_usd_bn=lambda df: df["revenue_usd_bn"] * df["fcf_margin"],
                    ev_revenue_multiple=[7.0, 10.0, 14.0],
                    ev_ebitda_multiple=[20.0, 26.0, 32.0],
                )
            )
            starlink_case["ev_revenue_value_usd_bn"] = (
                starlink_case["revenue_usd_bn"] * starlink_case["ev_revenue_multiple"]
            )
            starlink_case["ev_ebitda_value_usd_bn"] = (
                starlink_case["ebitda_usd_bn"] * starlink_case["ev_ebitda_multiple"]
            )
            starlink_case["selected_value_usd_bn"] = starlink_case[
                ["ev_revenue_value_usd_bn", "ev_ebitda_value_usd_bn"]
            ].mean(axis=1)
            starlink_case
            """
        ),
        code(
            """
            subscriber_arpu_grid = build_sensitivity_grid(
                row_values=[18, 24, 30, 36, 42],
                column_values=[70, 80, 90, 100, 110],
                formula=lambda subscribers_m, arpu: subscribers_m * arpu * 12 / 1_000,
                row_name="2030 subscribers (m)",
                column_name="ARPU ($/month)",
            )
            subscriber_arpu_grid
            """
        ),
        code(
            """
            ax = starlink_case[["revenue_usd_bn", "ebitda_usd_bn", "fcf_usd_bn"]].plot(
                kind="bar", figsize=(9, 4), title="Starlink 2030 Case Outputs"
            )
            ax.set_ylabel("USD bn")
            ax.set_xlabel("")
            plt.tight_layout()
            """
        ),
    ),
)


SEGMENTS_NOTEBOOK = NotebookSpec(
    filename="02_launch_starshield_ai_models.ipynb",
    title="02 Launch Starshield AI Models",
    cells=(
        md(
            """
            # 02 Launch, Starshield and AI Models

            Launch counts only external revenue. Internal Starlink launches are an
            avoided Starlink capex cost, not launch revenue. AI is split between
            contracted terrestrial GPU rental economics and speculative orbital AI.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            cases = ["bear", "base", "bull"]
            segment_tables = {}
            for segment in ["Launch", "Starshield", "AI"]:
                table = (
                    assumptions[assumptions["segment"].eq(segment)]
                    .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                    .reindex(cases)
                )
                segment_tables[segment] = table
            segment_tables["Launch"]
            """
        ),
        code(
            """
            launch = segment_tables["Launch"].assign(
                ebitda_usd_bn=lambda df: df["2030 revenue"] * df["EBITDA margin"],
                ev_revenue_multiple=[5.0, 7.5, 10.0],
                ev_ebitda_multiple=[17.0, 22.0, 28.0],
            )
            launch["selected_value_usd_bn"] = (
                launch["2030 revenue"] * launch["ev_revenue_multiple"]
                + launch["ebitda_usd_bn"] * launch["ev_ebitda_multiple"]
            ) / 2
            launch
            """
        ),
        code(
            """
            starshield = segment_tables["Starshield"].assign(
                defense_multiple=[8.0, 12.0, 16.0],
                concentration_haircut=[0.30, 0.20, 0.10],
            )
            starshield["gross_value_usd_bn"] = (
                starshield["2030 revenue"] * starshield["defense_multiple"]
            )
            starshield["selected_value_usd_bn"] = starshield["gross_value_usd_bn"] * (
                1 - starshield["concentration_haircut"]
            )
            starshield
            """
        ),
        code(
            """
            ai = segment_tables["AI"].assign(
                ebitda_usd_bn=lambda df: df["2030 revenue"] * df["EBITDA margin"],
                ev_revenue_multiple=[6.0, 10.0, 15.0],
                contract_duration_haircut=[0.35, 0.20, 0.10],
            )
            ai["gross_value_usd_bn"] = ai["2030 revenue"] * ai["ev_revenue_multiple"]
            ai["selected_value_usd_bn"] = ai["gross_value_usd_bn"] * (
                1 - ai["contract_duration_haircut"]
            )
            ai
            """
        ),
        code(
            """
            ai_sensitivity = build_sensitivity_grid(
                row_values=[15, 30, 45, 60, 75],
                column_values=[0.10, 0.20, 0.30, 0.40],
                formula=lambda revenue, gross_margin: revenue * gross_margin,
                row_name="AI revenue (USD bn)",
                column_name="AI gross margin",
            )
            ai_sensitivity
            """
        ),
    ),
)


OPTIONS_NOTEBOOK = NotebookSpec(
    filename="03_starship_and_orbital_compute_options.ipynb",
    title="03 Starship and Orbital Compute Options",
    cells=(
        md(
            """
            # 03 Starship and Orbital Compute Options

            Starship and orbital compute are valued as probability-weighted options,
            not base-case cash flows. The base case should only include option value
            supported by milestones or clear internal economics.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            options = pd.read_csv(DATA_DIR / "option_scenarios.csv")
            options
            """
        ),
        code(
            """
            option_values = {}
            for option_name, group in options.groupby("option"):
                scenarios = [
                    OptionScenario(row.case, row.probability, row.value_usd_bn)
                    for row in group.itertuples(index=False)
                ]
                option_values[option_name] = probability_weighted_option_value(scenarios)
            option_values
            """
        ),
        code(
            """
            starship_grid = build_sensitivity_grid(
                row_values=[0.10, 0.25, 0.40, 0.55, 0.70],
                column_values=[25, 50, 100, 150, 200],
                formula=lambda probability, cadence: probability * cadence * 2.5,
                row_name="Starship success probability",
                column_name="Reliable launches per year",
            )
            starship_grid
            """
        ),
        code(
            """
            cost_payload_grid = build_sensitivity_grid(
                row_values=[100, 250, 500, 1_000],
                column_values=[50, 100, 200, 400],
                formula=lambda cost_per_kg, demand_kt: demand_kt * 1_000_000 / cost_per_kg / 1_000,
                row_name="Cost per kg ($)",
                column_name="Payload demand (kt)",
            )
            cost_payload_grid
            """
        ),
    ),
)


COMPS_NOTEBOOK = NotebookSpec(
    filename="04_public_comps_and_market_premium.ipynb",
    title="04 Public Comps and Market Premium",
    cells=(
        md(
            """
            # 04 Public Comps and Market Premium

            The right output is not an average multiple. This notebook builds peer
            groups, optional live market pulls, narrative premium scoring, and the
            explicit market premium bridge from fundamental SOTP to IPO market value.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            comps = pd.read_csv(DATA_DIR / "public_comps.csv")
            comps.head()
            """
        ),
        code(
            """
            try:
                import yfinance as yf

                tickers = comps["ticker"].dropna().unique().tolist()
                rows = []
                for ticker in tickers:
                    info = yf.Ticker(ticker).fast_info
                    rows.append(
                        {
                            "ticker": ticker,
                            "market_cap": getattr(info, "market_cap", np.nan),
                            "last_price": getattr(info, "last_price", np.nan),
                            "currency": getattr(info, "currency", None),
                        }
                    )
                live_market = pd.DataFrame(rows)
            except Exception as exc:
                live_market = pd.DataFrame(
                    [{"ticker": "DATA_UNAVAILABLE", "market_cap": np.nan, "last_price": np.nan, "currency": str(exc)}]
                )
            live_market.head()
            """
        ),
        code(
            """
            premium_inputs = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            base_sotp = 1_350.0
            premium_bridge = []
            for case, row in premium_inputs.iterrows():
                result = market_premium_value(
                    base_sotp,
                    MarketPremiumInputs(
                        musk_premium=row.musk_premium,
                        ai_scarcity_premium=row.ai_scarcity_premium,
                        ipo_scarcity_premium=row.ipo_scarcity_premium,
                        strategic_asset_premium=row.strategic_asset_premium,
                        governance_discount=row.governance_discount,
                        execution_haircut=row.execution_haircut,
                    ),
                )
                premium_bridge.append(
                    {
                        "case": case,
                        "base_sotp_usd_bn": base_sotp,
                        "net_premium": result.net_premium,
                        "market_value_usd_bn": result.market_value,
                    }
                )
            pd.DataFrame(premium_bridge)
            """
        ),
        code(
            """
            comps.groupby("peer_group").agg(
                company_count=("company", "count"),
                avg_narrative_score=("narrative_premium_score", "mean"),
            ).sort_values("avg_narrative_score", ascending=False)
            """
        ),
    ),
)


SOTP_NOTEBOOK = NotebookSpec(
    filename="05_sotp_sensitivities_and_memo.ipynb",
    title="05 SOTP Sensitivities and Memo",
    cells=(
        md(
            """
            # 05 SOTP Sensitivities and Memo

            Final question: at the IPO valuation, what has to go right?
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            options = pd.read_csv(DATA_DIR / "option_scenarios.csv")
            premium_inputs = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            cases = ["bear", "base", "bull"]
            """
        ),
        code(
            """
            starlink = (
                assumptions[assumptions["segment"].eq("Starlink")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
            )
            starlink["revenue_usd_bn"] = starlink["2030 subscribers"] * starlink["2030 ARPU"] * 12 / 1_000
            starlink["ebitda_usd_bn"] = starlink["revenue_usd_bn"] * starlink["EBITDA margin"]
            starlink["selected_value_usd_bn"] = starlink["revenue_usd_bn"] * [7.0, 10.0, 14.0]

            launch = (
                assumptions[assumptions["segment"].eq("Launch")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
            )
            launch["selected_value_usd_bn"] = launch["2030 revenue"] * [5.0, 7.5, 10.0]

            starshield = (
                assumptions[assumptions["segment"].eq("Starshield")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
            )
            starshield["selected_value_usd_bn"] = starshield["2030 revenue"] * [8.0, 12.0, 16.0] * [0.70, 0.80, 0.90]

            ai = (
                assumptions[assumptions["segment"].eq("AI")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
            )
            ai["selected_value_usd_bn"] = ai["2030 revenue"] * [6.0, 10.0, 15.0] * [0.65, 0.80, 0.90]

            option_values = {}
            for option_name, group in options.groupby("option"):
                scenarios = [
                    OptionScenario(row.case, row.probability, row.value_usd_bn)
                    for row in group.itertuples(index=False)
                ]
                option_values[option_name] = probability_weighted_option_value(scenarios)
            option_values
            """
        ),
        code(
            """
            sotp_rows = []
            for case in cases:
                segments = [
                    SegmentValuation("Starlink", starlink.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("Launch", launch.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("Starshield", starshield.loc[case, "selected_value_usd_bn"], "Defense multiple"),
                    SegmentValuation("AI", ai.loc[case, "selected_value_usd_bn"], "AI infrastructure multiple"),
                    SegmentValuation("Starship option", option_values["Starship"], "Probability weighted option"),
                    SegmentValuation("Orbital compute option", option_values["Orbital compute"], "Probability weighted option"),
                ]
                bridge = sotp_equity_value(
                    SotpInputs(
                        segments=segments,
                        cash=75.0,
                        debt=25.0,
                        dilution=50.0,
                        fully_diluted_shares=3.5,
                    )
                )
                premium = premium_inputs.loc[case]
                market = market_premium_value(
                    bridge.equity_value,
                    MarketPremiumInputs(
                        musk_premium=premium.musk_premium,
                        ai_scarcity_premium=premium.ai_scarcity_premium,
                        ipo_scarcity_premium=premium.ipo_scarcity_premium,
                        strategic_asset_premium=premium.strategic_asset_premium,
                        governance_discount=premium.governance_discount,
                        execution_haircut=premium.execution_haircut,
                    ),
                )
                sotp_rows.append(
                    {
                        "case": case,
                        "fundamental_sotp_usd_bn": bridge.equity_value,
                        "net_market_premium": market.net_premium,
                        "market_value_usd_bn": market.market_value,
                        "value_per_share_usd": market.market_value / 3.5,
                    }
                )
            sotp = pd.DataFrame(sotp_rows).set_index("case")
            sotp
            """
        ),
        code(
            """
            implied_grid = build_sensitivity_grid(
                row_values=[125, 150, 175, 200, 225, 250],
                column_values=[0.20, 0.30, 0.40, 0.50],
                formula=lambda revenue, margin: revenue * margin * 25.0,
                row_name="2030 revenue (USD bn)",
                column_name="EBITDA margin",
            )
            implied_grid
            """
        ),
        code(
            """
            football = pd.DataFrame(
                {
                    "method": [
                        "Starlink DCF / multiples",
                        "Launch multiples",
                        "Starshield defense",
                        "AI infrastructure",
                        "SOTP",
                        "Market premium",
                        "Bull option case",
                    ],
                    "low": [250, 40, 20, 45, sotp.loc["bear", "fundamental_sotp_usd_bn"], sotp.loc["bear", "market_value_usd_bn"], 900],
                    "high": [700, 220, 260, 1_010, sotp.loc["bull", "fundamental_sotp_usd_bn"], sotp.loc["bull", "market_value_usd_bn"], 2_500],
                }
            )
            ax = football.plot.barh(x="method", y=["low", "high"], figsize=(9, 5), title="Valuation Football Field")
            ax.set_xlabel("USD bn")
            plt.tight_layout()
            football
            """
        ),
        md(
            """
            ## Investment Memo Draft

            At a $1.75T IPO valuation, SpaceX is not being valued as a space company.
            It is being valued as a hybrid of global telecom infrastructure, defense
            infrastructure, AI cloud infrastructure and Musk-led option value.

            What has to go right:

            - Starlink must scale into infrastructure-like EBITDA margins while managing replacement capex.
            - AI contracts must be durable and margin-accretive, not a low-margin GPU lease trade.
            - Starshield must broaden from US government concentration into allied sovereign adoption.
            - Starship must lower internal deployment costs and earn credible commercial cadence credit.
            - Public markets must continue awarding frontier scarcity, Musk and AI premiums despite governance risk.
            """
        ),
    ),
)


NOTEBOOK_SPECS = (
    SOURCE_LOG_NOTEBOOK,
    STARLINK_NOTEBOOK,
    SEGMENTS_NOTEBOOK,
    OPTIONS_NOTEBOOK,
    COMPS_NOTEBOOK,
    SOTP_NOTEBOOK,
)


def build_notebook(spec: NotebookSpec) -> nbformat.NotebookNode:
    cells = []
    for index, source in enumerate(spec.cells):
        if index == 0 or source.startswith("#") or source.startswith("##"):
            cells.append(new_markdown_cell(source))
        else:
            cells.append(new_code_cell(source))
    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
    )
    return notebook


def build_all_notebooks() -> list[Path]:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    output_paths = []
    for spec in NOTEBOOK_SPECS:
        path = NOTEBOOK_DIR / spec.filename
        nbformat.write(build_notebook(spec), path)
        output_paths.append(path)
    return output_paths


if __name__ == "__main__":
    for output_path in build_all_notebooks():
        print(output_path)
