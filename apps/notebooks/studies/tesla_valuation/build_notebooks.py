# ruff: noqa: E501
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

NOTEBOOK_DIR = Path(__file__).parent


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
        implied_margin_for_enterprise_value,
        implied_revenue_for_enterprise_value,
        market_premium_value,
        probability_weighted_option_value,
        sotp_equity_value,
    )

    DATA_DIR = next(
        candidate / "apps/notebooks/studies/tesla_valuation/data"
        for candidate in (Path.cwd(), *Path.cwd().parents)
        if (candidate / "apps/notebooks/studies/tesla_valuation/data").exists()
    )
    pd.options.display.float_format = "{:,.2f}".format
    """
)


SOURCE_LOG_NOTEBOOK = NotebookSpec(
    filename="00_source_log_and_financial_extraction.ipynb",
    title="00 Source Log and Financial Extraction",
    cells=(
        md(
            """
            # 00 Source Log and Financial Extraction

            Purpose: maintain an auditable source log and extraction checklist for a
            Tesla public-equity valuation. This v1 model is source-aware and scaffolded:
            live market data is optional, while seed assumptions keep the suite runnable
            offline.
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
            ## Extraction Checklist

            Replace seed assumptions as filings and company materials are normalized:

            - consolidated revenue, gross profit, operating income, EBITDA, capex and FCF
            - Auto, Energy, Services and software revenue/margin disclosures
            - deliveries, ASP, regulatory credits, leasing, inventory and working capital
            - cash, debt, leases, diluted shares, SBC and option dilution
            - FSD deferred revenue, autonomy milestones, robotaxi disclosures and Optimus evidence
            """
        ),
        code(
            """
            extraction_fields = pd.DataFrame(
                [
                    ("Reported financials", "Revenue / margin / capex / FCF", "TSLA-SEC"),
                    ("Segment schedule", "Auto / Energy / Services / software split", "TSLA-SEC"),
                    ("Market data", "Price / market cap / EV bridge", "YF-TSLA"),
                    ("Capital structure", "Cash / debt / diluted shares / SBC", "TSLA-SEC"),
                    ("Autonomy options", "FSD, robotaxi, Optimus milestones", "TSLA-IR"),
                    ("Evidence gaps", "Consensus, source-backed WACC, latest share count", "ANALYST-SEED"),
                ],
                columns=["workstream", "required_fields", "primary_source"],
            )
            extraction_fields
            """
        ),
    ),
)


AUTO_NOTEBOOK = NotebookSpec(
    filename="01_auto_deliveries_and_margin_model.ipynb",
    title="01 Auto Deliveries and Margin Model",
    cells=(
        md(
            """
            # 01 Auto Deliveries and Margin Model

            Key question: how much of Tesla's current valuation can be supported by
            auto deliveries, ASP, manufacturing margins and operating leverage before
            giving credit to autonomy or robotics?
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            auto = assumptions[assumptions["segment"].eq("Auto")]
            auto.pivot_table(index="metric", columns="case", values="value", aggfunc="first")
            """
        ),
        code(
            """
            cases = ["bear", "base", "bull"]
            auto_case = (
                auto.pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(cases)
                .assign(
                    revenue_usd_bn=lambda df: df["2030 deliveries"] * df["ASP"] / 1_000,
                    ebitda_usd_bn=lambda df: df["revenue_usd_bn"] * df["EBITDA margin"],
                    fcf_margin=lambda df: df["EBITDA margin"] - [0.05, 0.04, 0.03],
                    ev_revenue_multiple=[1.5, 2.5, 4.0],
                    ev_ebitda_multiple=[10.0, 15.0, 22.0],
                )
            )
            auto_case["fcf_usd_bn"] = auto_case["revenue_usd_bn"] * auto_case["fcf_margin"]
            auto_case["ev_revenue_value_usd_bn"] = auto_case["revenue_usd_bn"] * auto_case["ev_revenue_multiple"]
            auto_case["ev_ebitda_value_usd_bn"] = auto_case["ebitda_usd_bn"] * auto_case["ev_ebitda_multiple"]
            auto_case["selected_value_usd_bn"] = auto_case[
                ["ev_revenue_value_usd_bn", "ev_ebitda_value_usd_bn"]
            ].mean(axis=1)
            auto_case
            """
        ),
        code(
            """
            deliveries_asp_grid = build_sensitivity_grid(
                row_values=[4, 5, 6, 7, 8, 10],
                column_values=[32_000, 36_000, 40_000, 44_000],
                formula=lambda deliveries_m, asp: deliveries_m * asp / 1_000,
                row_name="2030 deliveries (m)",
                column_name="ASP ($)",
            )
            deliveries_asp_grid
            """
        ),
        code(
            """
            margin_multiple_grid = build_sensitivity_grid(
                row_values=[0.10, 0.14, 0.18, 0.22, 0.26],
                column_values=[1.5, 2.5, 3.5, 4.5],
                formula=lambda margin, multiple: auto_case.loc["base", "revenue_usd_bn"] * margin * multiple,
                row_name="Auto EBITDA margin",
                column_name="EV / revenue",
            )
            margin_multiple_grid
            """
        ),
        code(
            """
            ax = auto_case[["revenue_usd_bn", "ebitda_usd_bn", "fcf_usd_bn"]].plot(
                kind="bar", figsize=(9, 4), title="Auto 2030 Case Outputs"
            )
            ax.set_ylabel("USD bn")
            ax.set_xlabel("")
            plt.tight_layout()
            """
        ),
    ),
)


ENERGY_NOTEBOOK = NotebookSpec(
    filename="02_energy_services_and_supercharging.ipynb",
    title="02 Energy Services and Supercharging",
    cells=(
        md(
            """
            # 02 Energy, Services and Supercharging

            Energy storage and recurring services can matter a lot if they compound
            with higher margins than auto. This notebook separates those cash-flow
            engines from FSD/robotaxi option value.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            cases = ["bear", "base", "bull"]
            segment_tables = {}
            for segment in ["Energy", "Services"]:
                segment_tables[segment] = (
                    assumptions[assumptions["segment"].eq(segment)]
                    .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                    .reindex(cases)
                )
            segment_tables["Energy"]
            """
        ),
        code(
            """
            energy = segment_tables["Energy"].assign(
                ebitda_usd_bn=lambda df: df["2030 revenue"] * df["EBITDA margin"],
                ev_revenue_multiple=[2.0, 4.0, 6.0],
                ev_ebitda_multiple=[15.0, 22.0, 30.0],
            )
            energy["selected_value_usd_bn"] = (
                energy["2030 revenue"] * energy["ev_revenue_multiple"]
                + energy["ebitda_usd_bn"] * energy["ev_ebitda_multiple"]
            ) / 2
            energy
            """
        ),
        code(
            """
            services = segment_tables["Services"].assign(
                ebitda_usd_bn=lambda df: df["2030 revenue"] * df["EBITDA margin"],
                ev_revenue_multiple=[1.5, 2.5, 4.0],
                ev_ebitda_multiple=[12.0, 18.0, 25.0],
            )
            services["selected_value_usd_bn"] = (
                services["2030 revenue"] * services["ev_revenue_multiple"]
                + services["ebitda_usd_bn"] * services["ev_ebitda_multiple"]
            ) / 2
            services
            """
        ),
        code(
            """
            storage_grid = build_sensitivity_grid(
                row_values=[100, 200, 300, 400, 500],
                column_values=[0.10, 0.15, 0.20, 0.25, 0.30],
                formula=lambda gwh, gross_margin: gwh * 0.25 * gross_margin,
                row_name="Storage deployments (GWh)",
                column_name="Storage gross margin",
            )
            storage_grid
            """
        ),
    ),
)


OPTIONS_NOTEBOOK = NotebookSpec(
    filename="03_fsd_robotaxi_and_optimus_options.ipynb",
    title="03 FSD Robotaxi and Optimus Options",
    cells=(
        md(
            """
            # 03 FSD, Robotaxi and Optimus Options

            FSD software can sit inside segment cash flow. Robotaxi and Optimus stay
            as probability-weighted option values until filings or operating data
            support base-case revenue recognition.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            options = pd.read_csv(DATA_DIR / "option_scenarios.csv")
            fsd = (
                assumptions[assumptions["segment"].eq("FSD")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(["bear", "base", "bull"])
            )
            fsd
            """
        ),
        code(
            """
            fsd_case = fsd.assign(
                ebitda_usd_bn=lambda df: df["2030 revenue"] * df["EBITDA margin"],
                ev_revenue_multiple=[5.0, 10.0, 15.0],
                ev_ebitda_multiple=[18.0, 26.0, 35.0],
            )
            fsd_case["selected_value_usd_bn"] = (
                fsd_case["2030 revenue"] * fsd_case["ev_revenue_multiple"]
                + fsd_case["ebitda_usd_bn"] * fsd_case["ev_ebitda_multiple"]
            ) / 2
            fsd_case
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
            fsd_attach_grid = build_sensitivity_grid(
                row_values=[0.10, 0.20, 0.30, 0.40, 0.50],
                column_values=[50, 75, 100, 125, 150],
                formula=lambda attach_rate, monthly_fee: 30_000_000 * attach_rate * monthly_fee * 12 / 1_000_000_000,
                row_name="FSD attach rate",
                column_name="Monthly fee ($)",
            )
            fsd_attach_grid
            """
        ),
        code(
            """
            robotaxi_grid = build_sensitivity_grid(
                row_values=[0.10, 0.25, 0.40, 0.55],
                column_values=[250_000, 500_000, 1_000_000, 2_000_000],
                formula=lambda success_probability, active_units: success_probability * active_units * 60_000 / 1_000_000_000,
                row_name="Robotaxi success probability",
                column_name="Active robotaxi units",
            )
            robotaxi_grid
            """
        ),
    ),
)


COMPS_NOTEBOOK = NotebookSpec(
    filename="04_public_comps_and_market_implied_debate.ipynb",
    title="04 Public Comps and Market Implied Debate",
    cells=(
        md(
            """
            # 04 Public Comps and Market-Implied Debate

            Tesla comps are a debate, not an average. Mature OEMs anchor auto cash
            flow, EV peers frame sentiment, and AI/platform names are narrative
            markers for option value rather than direct valuation averages.
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

                rows = []
                for ticker in comps["ticker"].dropna().unique():
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
                    [
                        {
                            "ticker": "DATA_UNAVAILABLE",
                            "market_cap": np.nan,
                            "last_price": np.nan,
                            "currency": str(exc),
                        }
                    ]
                )
            live_market.head()
            """
        ),
        code(
            """
            premiums = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            base_fundamental_value = 800.0
            premium_rows = []
            for case, row in premiums.iterrows():
                inputs = MarketPremiumInputs(
                    musk_premium=row.musk_premium,
                    ai_scarcity_premium=row.ai_autonomy_premium,
                    ipo_scarcity_premium=row.mega_cap_liquidity_premium,
                    strategic_asset_premium=row.energy_growth_premium,
                    governance_discount=row.governance_discount,
                    execution_haircut=row.execution_haircut,
                )
                result = market_premium_value(base_fundamental_value, inputs)
                premium_rows.append(
                    {
                        "case": case,
                        "fundamental_value_usd_bn": base_fundamental_value,
                        "net_premium_discount": result.net_premium,
                        "market_implied_value_usd_bn": result.market_value,
                    }
                )
            pd.DataFrame(premium_rows)
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
    filename="05_dcf_sotp_sensitivities_and_memo.ipynb",
    title="05 DCF SOTP Sensitivities and Memo",
    cells=(
        md(
            """
            # 05 DCF, SOTP, Sensitivities and Memo

            Final question: at Tesla's current market valuation, what has to go right?
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            options = pd.read_csv(DATA_DIR / "option_scenarios.csv")
            premiums = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            cases = ["bear", "base", "bull"]
            """
        ),
        code(
            """
            def case_table(segment):
                return (
                    assumptions[assumptions["segment"].eq(segment)]
                    .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                    .reindex(cases)
                )


            auto = case_table("Auto")
            auto["revenue_usd_bn"] = auto["2030 deliveries"] * auto["ASP"] / 1_000
            auto["ebitda_usd_bn"] = auto["revenue_usd_bn"] * auto["EBITDA margin"]
            auto["selected_value_usd_bn"] = auto["revenue_usd_bn"] * [1.5, 2.5, 4.0]

            energy = case_table("Energy")
            energy["ebitda_usd_bn"] = energy["2030 revenue"] * energy["EBITDA margin"]
            energy["selected_value_usd_bn"] = energy["2030 revenue"] * [2.0, 4.0, 6.0]

            services = case_table("Services")
            services["ebitda_usd_bn"] = services["2030 revenue"] * services["EBITDA margin"]
            services["selected_value_usd_bn"] = services["2030 revenue"] * [1.5, 2.5, 4.0]

            fsd = case_table("FSD")
            fsd["ebitda_usd_bn"] = fsd["2030 revenue"] * fsd["EBITDA margin"]
            fsd["selected_value_usd_bn"] = fsd["2030 revenue"] * [5.0, 10.0, 15.0]

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
            capital = (
                assumptions[assumptions["segment"].eq("Capital")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
            )
            sotp_rows = []
            for case in cases:
                segments = [
                    SegmentValuation("Auto", auto.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("Energy", energy.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("Services/Supercharging", services.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("FSD/software", fsd.loc[case, "selected_value_usd_bn"], "EV/Revenue"),
                    SegmentValuation("Robotaxi option", option_values["Robotaxi"], "Probability weighted option"),
                    SegmentValuation("Optimus option", option_values["Optimus"], "Probability weighted option"),
                ]
                bridge = sotp_equity_value(
                    SotpInputs(
                        segments=segments,
                        cash=capital.loc["base", "cash"],
                        debt=capital.loc["base", "debt"],
                        dilution=capital.loc["base", "dilution"],
                        fully_diluted_shares=capital.loc["base", "fully diluted shares"],
                    )
                )
                premium = premiums.loc[case]
                market = market_premium_value(
                    bridge.equity_value,
                    MarketPremiumInputs(
                        musk_premium=premium.musk_premium,
                        ai_scarcity_premium=premium.ai_autonomy_premium,
                        ipo_scarcity_premium=premium.mega_cap_liquidity_premium,
                        strategic_asset_premium=premium.energy_growth_premium,
                        governance_discount=premium.governance_discount,
                        execution_haircut=premium.execution_haircut,
                    ),
                )
                sotp_rows.append(
                    {
                        "case": case,
                        "fundamental_sotp_usd_bn": bridge.equity_value,
                        "net_premium_discount": market.net_premium,
                        "market_implied_value_usd_bn": market.market_value,
                        "value_per_share_usd": market.market_value / capital.loc["base", "fully diluted shares"],
                    }
                )
            sotp = pd.DataFrame(sotp_rows).set_index("case")
            sotp
            """
        ),
        code(
            """
            reverse_grid = build_sensitivity_grid(
                row_values=[150, 200, 250, 300, 350, 400],
                column_values=[0.12, 0.18, 0.24, 0.30],
                formula=lambda revenue, margin: revenue * margin * 25.0,
                row_name="2030 revenue (USD bn)",
                column_name="EBITDA margin",
            )
            reverse_grid
            """
        ),
        code(
            """
            current_equity_value = 1_400.0
            implied_requirements = pd.DataFrame(
                [
                    {
                        "exit_multiple": multiple,
                        "target_margin": margin,
                        "required_2030_revenue_usd_bn": implied_revenue_for_enterprise_value(
                            current_equity_value, margin, multiple
                        ),
                        "required_margin_at_250bn_revenue": implied_margin_for_enterprise_value(
                            current_equity_value, 250.0, multiple
                        ),
                    }
                    for multiple in [18.0, 25.0, 32.0]
                    for margin in [0.18, 0.24, 0.30]
                ]
            )
            implied_requirements
            """
        ),
        code(
            """
            football = pd.DataFrame(
                {
                    "method": [
                        "Auto cash flow",
                        "Energy storage",
                        "Services / charging",
                        "FSD software",
                        "SOTP",
                        "Market premium",
                        "Bull option case",
                    ],
                    "low": [80, 70, 35, 40, sotp.loc["bear", "fundamental_sotp_usd_bn"], sotp.loc["bear", "market_implied_value_usd_bn"], 900],
                    "high": [1_720, 840, 300, 1_200, sotp.loc["bull", "fundamental_sotp_usd_bn"], sotp.loc["bull", "market_implied_value_usd_bn"], 3_000],
                }
            )
            ax = football.plot.barh(x="method", y=["low", "high"], figsize=(9, 5), title="Tesla Valuation Football Field")
            ax.set_xlabel("USD bn")
            plt.tight_layout()
            football
            """
        ),
        md(
            """
            ## Research Memo Draft

            At Tesla's current market valuation, the stock is not being valued as a
            normal auto OEM. The valuation debate is whether auto cash flow, energy
            storage scale, recurring software, autonomy and robotics can compound into
            a platform-like earnings base before market patience fades.

            What has to go right:

            - Auto deliveries must recover without requiring structurally lower margins.
            - Energy storage must become a large, profitable second cash-flow engine.
            - FSD must convert from feature promise into high-margin recurring software.
            - Robotaxi must prove real unit economics before it deserves base-case credit.
            - Optimus must show source-backed milestones before large value moves out of option value.
            - Public markets must keep awarding Tesla an AI/autonomy premium despite governance and execution risk.

            This is research and modeling support, not a recommendation or portfolio action.
            """
        ),
    ),
)


NOTEBOOK_SPECS = (
    SOURCE_LOG_NOTEBOOK,
    AUTO_NOTEBOOK,
    ENERGY_NOTEBOOK,
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
    return new_notebook(
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
