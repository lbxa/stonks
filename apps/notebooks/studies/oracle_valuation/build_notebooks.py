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
        DcfInputs,
        MarketPremiumInputs,
        OptionScenario,
        SegmentValuation,
        SotpInputs,
        build_sensitivity_grid,
        discounted_cash_flow,
        implied_margin_for_enterprise_value,
        implied_revenue_for_enterprise_value,
        market_premium_value,
        probability_weighted_option_value,
        sotp_equity_value,
    )

    DATA_DIR = next(
        candidate / "apps/notebooks/studies/oracle_valuation/data"
        for candidate in (Path.cwd(), *Path.cwd().parents)
        if (candidate / "apps/notebooks/studies/oracle_valuation/data").exists()
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

            Purpose: maintain an auditable source log and extraction checklist for an
            Oracle public-equity valuation. This v1 model is source-aware and
            offline-runnable: public facts seed the current setup, while the
            assumptions remain easy to replace when filings are normalized.
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
            ## Current Fact Pattern

            Oracle is being underwritten less like a mature software company and more
            like a capital-intensive AI infrastructure buildout attached to a durable
            database and applications franchise.
            """
        ),
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            current_facts = (
                assumptions[
                    assumptions["segment"].eq("Market")
                    & assumptions["case"].eq("base")
                    & assumptions["metric"].isin(
                        [
                            "current price",
                            "current equity value",
                            "FY2027 revenue guide",
                            "FY2027 adjusted EPS guide",
                            "remaining performance obligations",
                            "FY2026 capex",
                            "FY2026 free cash flow",
                            "FY2027 gross capex guide",
                            "FY2027 net capex cash outlay",
                        ]
                    )
                ]
                .loc[:, ["metric", "value", "unit", "source_id", "notes"]]
                .reset_index(drop=True)
            )
            current_facts
            """
        ),
        md(
            """
            ## Extraction Checklist

            Replace seed assumptions as filings and company materials are normalized:

            - consolidated revenue, operating income, capex, free cash flow and debt
            - OCI revenue, cloud applications revenue, database support and license trends
            - RPO roll-forward, customer concentration, prepayments and bring-your-own-hardware terms
            - cash, debt, leases, equity issuance, diluted shares and SBC dilution
            - data-center capacity, power availability, depreciation and mature OCI margin evidence
            - consensus revenue, EPS, FCF and capex estimates through FY2030
            """
        ),
        code(
            """
            extraction_fields = pd.DataFrame(
                [
                    ("Reported financials", "Revenue / operating margin / capex / FCF", "ORCL-Q4-FY2026"),
                    ("Cloud infrastructure", "OCI revenue / capacity / RPO conversion / margin", "ORCL-Q4-FY2026"),
                    ("Software durability", "Database support / applications / license migration", "ORCL-SEC"),
                    ("Capital structure", "Cash / debt / leases / equity issuance / diluted shares", "ORCL-SEC"),
                    ("Market data", "Price / market cap / EV bridge / forward EPS multiple", "MW-ORCL-PRICE"),
                    ("Evidence gaps", "Consensus, customer concentration, mature OCI returns", "ANALYST-SEED"),
                ],
                columns=["workstream", "required_fields", "primary_source"],
            )
            extraction_fields
            """
        ),
    ),
)


OCI_NOTEBOOK = NotebookSpec(
    filename="01_oci_rpo_and_ai_capacity_model.ipynb",
    title="01 OCI RPO and AI Capacity Model",
    cells=(
        md(
            """
            # 01 OCI, RPO and AI Capacity Model

            Key question: how much value should Oracle get for AI infrastructure
            backlog when the same contracts require very large capex, financing and
            execution through FY2030?
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            oci = (
                assumptions[assumptions["segment"].eq("OCI")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                .reindex(["bear", "base", "bull"])
            )
            oci
            """
        ),
        code(
            """
            oci_case = oci.assign(
                ebitda_usd_bn=lambda df: df["FY2030 revenue"] * df["EBITDA margin"],
                undiscounted_ev_usd_bn=lambda df: df["FY2030 revenue"]
                * df["EBITDA margin"]
                * df["EV/EBITDA multiple"],
                present_value_usd_bn=lambda df: df["undiscounted_ev_usd_bn"] * df["discount factor"],
            )
            oci_case
            """
        ),
        code(
            """
            revenue_margin_grid = build_sensitivity_grid(
                row_values=[95, 120, 145, 166, 190, 220],
                column_values=[0.25, 0.30, 0.34, 0.38, 0.42],
                formula=lambda revenue, margin: revenue * margin * 14.0 * 0.68,
                row_name="FY2030 OCI revenue (USD bn)",
                column_name="OCI EBITDA margin",
            )
            revenue_margin_grid
            """
        ),
        code(
            """
            rpo = assumptions[
                assumptions["segment"].eq("Market")
                & assumptions["metric"].eq("remaining performance obligations")
            ].iloc[0]["value"]
            rpo_conversion_grid = build_sensitivity_grid(
                row_values=[0.30, 0.40, 0.50, 0.60],
                column_values=[0.25, 0.30, 0.35, 0.40],
                formula=lambda conversion, margin: rpo * conversion * margin * 12.0 * 0.68,
                row_name="RPO converted into steady-state OCI revenue",
                column_name="OCI EBITDA margin",
            )
            rpo_conversion_grid
            """
        ),
        code(
            """
            ax = oci_case[["FY2030 revenue", "ebitda_usd_bn", "present_value_usd_bn"]].plot(
                kind="bar", figsize=(9, 4), title="OCI FY2030 Case Outputs"
            )
            ax.set_ylabel("USD bn")
            ax.set_xlabel("")
            plt.tight_layout()
            """
        ),
    ),
)


SOFTWARE_NOTEBOOK = NotebookSpec(
    filename="02_database_apps_and_support_model.ipynb",
    title="02 Database Apps and Support Model",
    cells=(
        md(
            """
            # 02 Database, Apps and Support Model

            Oracle's software franchise funds the AI buildout and keeps the downside
            from being a pure infrastructure balance-sheet story. This notebook
            separates cloud applications, database support and services/hardware.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            cases = ["bear", "base", "bull"]

            def segment_case(segment):
                return (
                    assumptions[assumptions["segment"].eq(segment)]
                    .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                    .reindex(cases)
                )

            software_segments = {
                segment: segment_case(segment)
                for segment in ["Cloud Apps", "Database Support", "Services Hardware"]
            }
            software_segments["Cloud Apps"]
            """
        ),
        code(
            """
            segment_outputs = []
            for segment, table in software_segments.items():
                output = table.assign(
                    ebitda_usd_bn=lambda df: df["FY2030 revenue"] * df["EBITDA margin"],
                    present_value_usd_bn=lambda df: df["FY2030 revenue"]
                    * df["EBITDA margin"]
                    * df["EV/EBITDA multiple"]
                    * df["discount factor"],
                )
                output["segment"] = segment
                segment_outputs.append(output.reset_index())

            software_value = pd.concat(segment_outputs, ignore_index=True)
            software_value.pivot_table(
                index=["segment", "case"],
                values=["FY2030 revenue", "ebitda_usd_bn", "present_value_usd_bn"],
            )
            """
        ),
        code(
            """
            apps_margin_multiple_grid = build_sensitivity_grid(
                row_values=[35, 40, 45, 50, 55],
                column_values=[13, 16, 19, 22],
                formula=lambda revenue, multiple: revenue * 0.38 * multiple * 0.68,
                row_name="FY2030 cloud apps revenue (USD bn)",
                column_name="EV/EBITDA multiple",
            )
            apps_margin_multiple_grid
            """
        ),
        code(
            """
            database_decay_grid = build_sensitivity_grid(
                row_values=[28, 31, 34, 37, 40],
                column_values=[8, 10, 12, 14],
                formula=lambda revenue, multiple: revenue * 0.48 * multiple * 0.68,
                row_name="FY2030 database support revenue (USD bn)",
                column_name="EV/EBITDA multiple",
            )
            database_decay_grid
            """
        ),
    ),
)


OPTIONS_NOTEBOOK = NotebookSpec(
    filename="03_ai_capacity_and_capex_options.ipynb",
    title="03 AI Capacity and Capex Options",
    cells=(
        md(
            """
            # 03 AI Capacity and Capex Options

            RPO is not the same as equity value. This notebook keeps upside from
            additional AI capacity separate from downside tied to capex, financing,
            customer concentration and delayed conversion.
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
            capex_funding_grid = build_sensitivity_grid(
                row_values=[60, 70, 80, 90, 100],
                column_values=[0.00, 0.15, 0.25, 0.35],
                formula=lambda gross_capex, customer_funded_pct: gross_capex * (1 - customer_funded_pct),
                row_name="FY2027 gross capex (USD bn)",
                column_name="Customer-funded percentage",
            )
            capex_funding_grid
            """
        ),
        code(
            """
            dilution_grid = build_sensitivity_grid(
                row_values=[175, 185, 200, 225],
                column_values=[10, 20, 30, 40],
                formula=lambda share_price, equity_raise: equity_raise / share_price,
                row_name="Equity raise price ($)",
                column_name="Equity raise (USD bn)",
            )
            dilution_grid
            """
        ),
        code(
            """
            option_frame = pd.DataFrame(
                [{"option": name, "probability_weighted_value_usd_bn": value} for name, value in option_values.items()]
            )
            ax = option_frame.plot.barh(
                x="option",
                y="probability_weighted_value_usd_bn",
                figsize=(8, 3),
                title="Probability-Weighted Oracle AI/Capex Options",
            )
            ax.set_xlabel("USD bn")
            plt.tight_layout()
            option_frame
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

            Oracle comps are a split debate: hyperscalers frame capacity scale,
            software names frame margin durability, and AI infrastructure names frame
            scarcity. An average multiple would hide the actual underwriting question.
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            comps = pd.read_csv(DATA_DIR / "public_comps.csv")
            comps
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
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            market = (
                assumptions[assumptions["segment"].eq("Market")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
            )
            current_price = market.loc["base", "current price"]
            eps_guide = market.loc["base", "FY2027 adjusted EPS guide"]
            current_pe = current_price / eps_guide
            pd.DataFrame(
                [
                    {
                        "current_price": current_price,
                        "FY2027_adjusted_EPS_guide": eps_guide,
                        "implied_forward_PE": current_pe,
                    }
                ]
            )
            """
        ),
        code(
            """
            premiums = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            base_fundamental_equity_value = 700.0
            premium_rows = []
            for case, row in premiums.iterrows():
                result = market_premium_value(
                    base_fundamental_equity_value,
                    MarketPremiumInputs(
                        ai_scarcity_premium=row.ai_scarcity_premium,
                        ipo_scarcity_premium=row.mega_cap_liquidity_premium,
                        strategic_asset_premium=row.strategic_asset_premium,
                        governance_discount=row.governance_discount,
                        execution_haircut=row.execution_haircut,
                    ),
                )
                premium_rows.append(
                    {
                        "case": case,
                        "fundamental_equity_value_usd_bn": base_fundamental_equity_value,
                        "net_premium_discount": result.net_premium,
                        "market_adjusted_equity_value_usd_bn": result.market_value,
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

            Final question: after the post-earnings pullback, does Oracle's current
            price pay too little, too much, or about enough for the OCI backlog?
            """
        ),
        COMMON_IMPORTS,
        code(
            """
            assumptions = pd.read_csv(DATA_DIR / "segment_assumptions.csv")
            options = pd.read_csv(DATA_DIR / "option_scenarios.csv")
            premiums = pd.read_csv(DATA_DIR / "market_premiums.csv").set_index("case")
            cases = ["bear", "base", "bull"]

            def case_table(segment):
                return (
                    assumptions[assumptions["segment"].eq(segment)]
                    .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
                    .reindex(cases)
                )

            def segment_value(table):
                return (
                    table["FY2030 revenue"]
                    * table["EBITDA margin"]
                    * table["EV/EBITDA multiple"]
                    * table["discount factor"]
                )
            """
        ),
        code(
            """
            segment_tables = {
                segment: case_table(segment)
                for segment in ["OCI", "Cloud Apps", "Database Support", "Services Hardware"]
            }
            for table in segment_tables.values():
                table["ebitda_usd_bn"] = table["FY2030 revenue"] * table["EBITDA margin"]
                table["selected_value_usd_bn"] = segment_value(table)

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
                    SegmentValuation("OCI", segment_tables["OCI"].loc[case, "selected_value_usd_bn"], "FY2030 EV/EBITDA PV"),
                    SegmentValuation("Cloud Apps", segment_tables["Cloud Apps"].loc[case, "selected_value_usd_bn"], "FY2030 EV/EBITDA PV"),
                    SegmentValuation("Database Support", segment_tables["Database Support"].loc[case, "selected_value_usd_bn"], "FY2030 EV/EBITDA PV"),
                    SegmentValuation("Services Hardware", segment_tables["Services Hardware"].loc[case, "selected_value_usd_bn"], "FY2030 EV/EBITDA PV"),
                    SegmentValuation("AI capacity conversion", option_values["AI capacity conversion"], "Probability weighted option"),
                    SegmentValuation("Capex/customer stress", option_values["Capex and customer concentration stress"], "Probability weighted option"),
                ]
                bridge = sotp_equity_value(
                    SotpInputs(
                        segments=segments,
                        cash=capital.loc["base", "cash"],
                        debt=capital.loc["base", "debt and lease liabilities"],
                        dilution=capital.loc["base", "dilution"],
                        fully_diluted_shares=capital.loc["base", "fully diluted shares"],
                    )
                )
                premium = premiums.loc[case]
                market = market_premium_value(
                    bridge.equity_value,
                    MarketPremiumInputs(
                        ai_scarcity_premium=premium.ai_scarcity_premium,
                        ipo_scarcity_premium=premium.mega_cap_liquidity_premium,
                        strategic_asset_premium=premium.strategic_asset_premium,
                        governance_discount=premium.governance_discount,
                        execution_haircut=premium.execution_haircut,
                    ),
                )
                sotp_rows.append(
                    {
                        "case": case,
                        "segment_value_usd_bn": bridge.segment_value,
                        "equity_value_before_premium_usd_bn": bridge.equity_value,
                        "net_premium_discount": market.net_premium,
                        "market_adjusted_equity_value_usd_bn": market.market_value,
                        "value_per_share_usd": market.market_value / capital.loc["base", "fully diluted shares"],
                    }
                )
            sotp = pd.DataFrame(sotp_rows).set_index("case")
            sotp
            """
        ),
        code(
            """
            market = (
                assumptions[assumptions["segment"].eq("Market")]
                .pivot_table(index="case", columns="metric", values="value", aggfunc="first")
            )
            current_price = market.loc["base", "current price"]
            current_equity_value = current_price * capital.loc["base", "fully diluted shares"]
            current_enterprise_value = (
                current_equity_value
                - capital.loc["base", "cash"]
                + capital.loc["base", "debt and lease liabilities"]
                + capital.loc["base", "dilution"]
            )
            current_context = pd.DataFrame(
                [
                    {
                        "current_price": current_price,
                        "current_equity_value_usd_bn": current_equity_value,
                        "current_enterprise_value_usd_bn": current_enterprise_value,
                        "base_value_per_share_usd": sotp.loc["base", "value_per_share_usd"],
                        "base_upside_downside": sotp.loc["base", "value_per_share_usd"] / current_price - 1,
                    }
                ]
            )
            current_context
            """
        ),
        code(
            """
            base = "base"
            base_premium = premiums.loc[base]
            base_net_premium = (
                base_premium.ai_scarcity_premium
                + base_premium.mega_cap_liquidity_premium
                + base_premium.strategic_asset_premium
                + base_premium.governance_discount
                + base_premium.execution_haircut
            )
            required_equity_before_premium = current_equity_value / (1 + base_net_premium)
            required_segment_value = (
                required_equity_before_premium
                - (capital.loc["base", "cash"] - capital.loc["base", "debt and lease liabilities"])
                + capital.loc["base", "dilution"]
            )
            non_oci_value = sum(
                segment_tables[segment].loc[base, "selected_value_usd_bn"]
                for segment in ["Cloud Apps", "Database Support", "Services Hardware"]
            ) + sum(option_values.values())
            required_oci_present_value = required_segment_value - non_oci_value
            oci_base = segment_tables["OCI"].loc[base]
            required_oci_revenue = (
                required_oci_present_value
                / oci_base["discount factor"]
                / oci_base["EBITDA margin"]
                / oci_base["EV/EBITDA multiple"]
            )
            priced_in = pd.DataFrame(
                [
                    {
                        "current_price": current_price,
                        "required_OCI_PV_usd_bn": required_oci_present_value,
                        "required_FY2030_OCI_revenue_usd_bn": required_oci_revenue,
                        "base_case_FY2030_OCI_revenue_usd_bn": oci_base["FY2030 revenue"],
                        "discount_to_base_OCI_revenue": required_oci_revenue / oci_base["FY2030 revenue"] - 1,
                    }
                ]
            )
            priced_in
            """
        ),
        code(
            """
            dcf_inputs = {
                "bear": DcfInputs(free_cash_flow=12.0, growth_rate=0.08, discount_rate=0.105, terminal_growth_rate=0.025, years=7),
                "base": DcfInputs(free_cash_flow=24.0, growth_rate=0.13, discount_rate=0.095, terminal_growth_rate=0.030, years=7),
                "bull": DcfInputs(free_cash_flow=38.0, growth_rate=0.16, discount_rate=0.090, terminal_growth_rate=0.035, years=7),
            }
            dcf_rows = []
            for case, inputs in dcf_inputs.items():
                result = discounted_cash_flow(inputs)
                equity_value = (
                    result.enterprise_value
                    + capital.loc["base", "cash"]
                    - capital.loc["base", "debt and lease liabilities"]
                    - capital.loc["base", "dilution"]
                )
                dcf_rows.append(
                    {
                        "case": case,
                        "dcf_enterprise_value_usd_bn": result.enterprise_value,
                        "dcf_equity_value_usd_bn": equity_value,
                        "dcf_value_per_share_usd": equity_value / capital.loc["base", "fully diluted shares"],
                    }
                )
            dcf_cross_check = pd.DataFrame(dcf_rows).set_index("case")
            dcf_cross_check
            """
        ),
        code(
            """
            reverse_grid = build_sensitivity_grid(
                row_values=[95, 120, 145, 166, 190, 220],
                column_values=[0.25, 0.30, 0.34, 0.38, 0.42],
                formula=lambda revenue, margin: revenue * margin * 14.0 * 0.68,
                row_name="FY2030 OCI revenue (USD bn)",
                column_name="OCI EBITDA margin",
            )
            reverse_grid
            """
        ),
        code(
            """
            football = pd.DataFrame(
                {
                    "method": [
                        "OCI FY2030 EV/EBITDA PV",
                        "Cloud apps",
                        "Database support",
                        "Options and stress",
                        "SOTP before premium",
                        "Market-adjusted SOTP",
                        "DCF cross-check",
                    ],
                    "low": [
                        segment_tables["OCI"].loc["bear", "selected_value_usd_bn"],
                        segment_tables["Cloud Apps"].loc["bear", "selected_value_usd_bn"],
                        segment_tables["Database Support"].loc["bear", "selected_value_usd_bn"],
                        min(option_values.values()),
                        sotp.loc["bear", "equity_value_before_premium_usd_bn"],
                        sotp.loc["bear", "market_adjusted_equity_value_usd_bn"],
                        dcf_cross_check.loc["bear", "dcf_equity_value_usd_bn"],
                    ],
                    "high": [
                        segment_tables["OCI"].loc["bull", "selected_value_usd_bn"],
                        segment_tables["Cloud Apps"].loc["bull", "selected_value_usd_bn"],
                        segment_tables["Database Support"].loc["bull", "selected_value_usd_bn"],
                        max(option_values.values()),
                        sotp.loc["bull", "equity_value_before_premium_usd_bn"],
                        sotp.loc["bull", "market_adjusted_equity_value_usd_bn"],
                        dcf_cross_check.loc["bull", "dcf_equity_value_usd_bn"],
                    ],
                }
            )
            ax = football.plot.barh(x="method", y=["low", "high"], figsize=(9, 5), title="Oracle Valuation Football Field")
            ax.set_xlabel("USD bn")
            plt.tight_layout()
            football
            """
        ),
        md(
            """
            ## Research Memo Draft

            At roughly $184 per share, Oracle is no longer just a mature database
            software underwriting. The current price appears to imply about $124B of
            FY2030 OCI revenue under the base margin, multiple and discount framework,
            below the seeded base case of $166B, but only after accepting meaningful
            funding, dilution and execution haircuts.

            What has to go right:

            - RPO must convert into revenue rather than remain a financing-heavy backlog headline.
            - OCI margins need to move toward management's mature 30-40 percent frame as capacity fills.
            - Customer prepayments and bring-your-own-hardware terms must reduce cash-flow strain.
            - Database support and applications must remain durable enough to fund the transition.
            - Debt, leases and equity issuance must not absorb the equity upside from OCI growth.

            What breaks first in downside is not demand; it is conversion economics. If
            capacity slips, customer concentration rises, or capex keeps outrunning
            revenue recognition, the equity can de-rate even while reported RPO remains
            large. The current setup is best treated as screen-grade and worth
            re-underwriting when the FY2026 10-K, customer concentration detail and
            FY2027 capex funding mix are normalized.
            """
        ),
    ),
)


NOTEBOOK_SPECS = (
    SOURCE_LOG_NOTEBOOK,
    OCI_NOTEBOOK,
    SOFTWARE_NOTEBOOK,
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
