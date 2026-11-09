"""Live charts for the projector (Altair). Colours match the presentation deck."""
import altair as alt
import pandas as pd

import content as C

INK, MUTED, GRID = "#1C1B2E", "#5F6178", "#D7D9E3"
ZONE_COLORS = {"public": "#3D5A98", "social": "#2A9D8F", "personal": "#F2A33A", "intimate": "#E2553B"}
ZONE_LABEL = {k: C.DISTANCES[k][0] for k in C.ZONE_ORDER}
SHORT = {"public": "Public|4 m+", "social": "Social|2 m", "personal": "Personal|0.8 m", "intimate": "Intimate|0.3 m"}


def _cfg(chart):
    return (chart.properties(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelFont="Arial", titleFont="Arial", labelFontSize=14, titleFontSize=13,
                            labelColor=MUTED, titleColor=MUTED, domainColor=GRID, tickColor=GRID,
                            gridColor=GRID, gridWidth=0.5, labelLimit=260)
            .configure_title(font="Arial", fontSize=16, color=INK, anchor="start")
            .configure_legend(labelFont="Arial", labelFontSize=14, labelColor=INK, orient="top"))


METRICS = [("score", f"Numbers found (of {C.GRID_MAX})", C.GRID_MAX), ("absorb", "How absorbed (1–7)", 7),
           ("aware", "Aware of the intruder (1–7)", 7), ("comfort", "Intruder's comfort (1–7)", 7)]


def zone_metrics(df):
    """df columns: zone, metric, value  ->  one small bar chart per metric, zones far → near."""
    order = [SHORT[z] for z in C.ZONE_ORDER]
    charts = []
    for key, title, top in METRICS:
        sub = df[df["metric"] == key]
        rows = []
        for z in C.ZONE_ORDER:
            vals = pd.to_numeric(sub.loc[sub["zone"] == z, "value"], errors="coerce").dropna()
            rows.append(dict(zone=z, label=SHORT[z], mean=round(vals.mean(), 1) if len(vals) else None, n=len(vals)))
        d = pd.DataFrame(rows)
        base = alt.Chart(d).encode(x=alt.X("label:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=12, labelExpr="split(datum.label, '|')")))
        bars = base.mark_bar(width=38, cornerRadiusEnd=4).encode(
            y=alt.Y("mean:Q", scale=alt.Scale(domain=[0, top]), title=None),
            color=alt.Color("zone:N", scale=alt.Scale(domain=list(ZONE_COLORS), range=list(ZONE_COLORS.values())), legend=None),
            tooltip=[alt.Tooltip("label:N", title="Distance"), alt.Tooltip("mean:Q", title="Mean"), alt.Tooltip("n:Q", title="Answers")])
        text = base.mark_text(dy=-10, fontSize=15, fontWeight="bold", color=INK, font="Arial").encode(
            y="mean:Q", text=alt.Text("mean:Q", format=".1f"))
        charts.append((bars + text).properties(title=title, width=230, height=210))
    return _cfg(alt.hconcat(*charts, spacing=28))


def reactions_grid(df):
    """df columns: zone, reaction  ->  count grid (reaction × distance), single-hue scale."""
    rows = []
    for z in C.ZONE_ORDER:
        for r in C.REACTIONS:
            rows.append(dict(label=ZONE_LABEL[z], reaction=r, count=int(((df["zone"] == z) & (df["reaction"] == r)).sum())))
    d = pd.DataFrame(rows)
    thr = max(3, 0.55 * (d["count"].max() or 0))
    order = [ZONE_LABEL[z] for z in C.ZONE_ORDER]
    base = alt.Chart(d).encode(x=alt.X("label:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, orient="top")),
                               y=alt.Y("reaction:N", sort=C.REACTIONS, title=None))
    rect = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        color=alt.Color("count:Q", scale=alt.Scale(range=["#EEF0F5", "#3D5A98"]), legend=None),
        tooltip=[alt.Tooltip("reaction:N", title="Reaction"), alt.Tooltip("label:N", title="Distance"),
                 alt.Tooltip("count:Q", title="Seen")])
    text = base.mark_text(fontSize=15, fontWeight="bold", font="Arial").encode(
        text="count:Q", color=alt.condition(f"datum.count >= {thr}", alt.value("white"), alt.value(INK)))
    return _cfg((rect + text).properties(width=720, height=300, title="What observers saw the worker do"))


def votes(df, groups_with_ideas):
    """df columns: item (best|dark), value (group no.)  ->  two ranked bar charts."""
    charts = []
    for item, title, color in [("best", C.JUDGE_BEST, "#2A9D8F"), ("dark", C.JUDGE_DARK, "#E2553B")]:
        sub = df[df["item"] == item]
        d = pd.DataFrame([dict(group=f"Group {g}", votes=int((sub["value"] == str(g)).sum())) for g in groups_with_ideas])
        base = alt.Chart(d).encode(y=alt.Y("group:N", sort="-x", title=None))
        bars = base.mark_bar(height=24, cornerRadiusEnd=4, color=color).encode(
            x=alt.X("votes:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("group:N"), alt.Tooltip("votes:Q", title="Votes")])
        text = base.mark_text(align="left", dx=6, fontSize=15, fontWeight="bold", color=INK).encode(x="votes:Q", text="votes:Q")
        charts.append((bars + text).properties(title=title, width=380, height=36 * max(1, len(d))))
    return _cfg(alt.hconcat(*charts, spacing=40))
