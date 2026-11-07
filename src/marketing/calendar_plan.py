"""
2027 campaign calendar: when to spend a yearly ad budget.

Every day of 2027 gets a weight. Ordinary days weigh 1. Days inside a campaign's ad
window weigh more, in proportion to how much better that campaign's ROAS was than
always-on ads in the (simulated) history, capped at 2x. Each month then gets its
share of the yearly budget from the sum of its daily weights.

This is a planning rule of thumb, not an optimisation: the optimizer itself has no
seasonality. Eid dates depend on the moon sighting and can move by a day or two.
Sources for the expected 2027 dates: officeholidays.com (Pakistan public holidays).
"""
import datetime as dt

import pandas as pd

YEAR = 2027
# name in the data -> (event date, ad window start, ad window end, note)
EVENTS = {
    "Eid ul Fitr Sale": ("2027-03-09", "2027-02-17", "2027-03-08",
                         "Expected 9 Mar 2027 (moon sighting). Ramadan starts around 8 Feb."),
    "Eid ul Adha Sale": ("2027-05-16", "2027-04-26", "2027-05-15",
                         "Expected 16 May 2027 (moon sighting)."),
    "Back to School": ("2027-08-01", "2027-07-20", "2027-08-10",
                       "Schools usually reopen around 1 August after the summer break."),
    "Winter Collection": ("2027-10-15", "2027-10-15", "2027-12-31",
                          "Season launch in mid-October."),
    "11.11 Mega Sale": ("2027-11-11", "2027-11-05", "2027-11-12",
                        "Fixed date: 11 November."),
}
MAX_BOOST = 2.0


def boosts(campaign_roas):
    """Weight per campaign: its ROAS relative to always-on ads, between 1 and 2."""
    base = campaign_roas["Always-On Brand"]
    return {c: min(max(campaign_roas[c] / base, 1.0), MAX_BOOST) for c in EVENTS}


def daily_plan(campaign_roas):
    """One row per day of 2027 with its weight and the campaign running (if any)."""
    b = boosts(campaign_roas)
    days = pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31", freq="D")
    rows = []
    for d in days:
        best, w = "Always-on", 1.0
        for c, (_, start, end, _) in EVENTS.items():
            if pd.Timestamp(start) <= d <= pd.Timestamp(end) and b[c] > w:
                best, w = c, b[c]
        rows.append(dict(date=d, campaign=best, weight=w))
    return pd.DataFrame(rows)


def monthly_plan(campaign_roas, yearly_budget):
    """Budget per month of 2027 and the main campaign running that month."""
    days = daily_plan(campaign_roas)
    days["month"] = days.date.dt.month
    total = days.weight.sum()
    out = []
    for m, g in days.groupby("month"):
        camp = g[g.campaign != "Always-on"].campaign
        main = ", ".join(dict.fromkeys(camp)) if len(camp) else "Always-on"
        out.append(dict(month=dt.date(YEAR, m, 1).strftime("%b"), month_num=m,
                        budget=yearly_budget * g.weight.sum() / total,
                        main_campaign=main, campaign_days=int(len(camp))))
    plan = pd.DataFrame(out)
    plan["vs_even_%"] = (plan.budget / (yearly_budget / 12) - 1) * 100
    return plan


def key_dates(campaign_roas):
    b = boosts(campaign_roas)
    rows = []
    for c, (event, start, end, note) in EVENTS.items():
        rows.append(dict(campaign=c, event_date=pd.Timestamp(event), ads_from=pd.Timestamp(start),
                         ads_to=pd.Timestamp(end), roas=campaign_roas[c], weight=b[c], note=note))
    return pd.DataFrame(rows).sort_values("ads_from").reset_index(drop=True)
