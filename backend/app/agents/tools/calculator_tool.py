"""
Financial Calculator tool for the Finance Advisor.
"""

from __future__ import annotations

from typing import Any


def calculate_saas_metrics(
    arpu: float,
    churn_rate: float,
    cac: float,
    growth_rate: float = 0.0,
) -> dict[str, Any]:
    """
    Calculate core SaaS metrics (LTV, LTV/CAC ratio, Payback Period, Run Rate).

    Args:
        arpu: Average Revenue Per User/Account (Monthly).
        churn_rate: Monthly churn rate (e.g. 0.02 for 2%).
        cac: Customer Acquisition Cost.
        growth_rate: Estimated monthly growth rate.

    Returns:
        Dictionary of calculated financial indicators.
    """
    metrics = {
        "monthly_arpu": arpu,
        "monthly_churn": churn_rate,
        "cac": cac,
    }

    # LTV = ARPU / Churn
    if churn_rate > 0:
        ltv = arpu / churn_rate
        metrics["customer_lifetime_value_ltv"] = round(ltv, 2)
        if cac > 0:
            metrics["ltv_to_cac_ratio"] = round(ltv / cac, 2)
        else:
            metrics["ltv_to_cac_ratio"] = float("inf")
    else:
        metrics["customer_lifetime_value_ltv"] = float("inf")
        metrics["ltv_to_cac_ratio"] = float("inf")

    # Payback Period = CAC / (ARPU * Gross Margin (assumed 80%))
    gross_margin = 0.8
    if arpu > 0:
        payback = cac / (arpu * gross_margin)
        metrics["payback_period_months"] = round(payback, 1)
    else:
        metrics["payback_period_months"] = float("inf")

    return metrics
