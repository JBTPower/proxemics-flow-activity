"""Live charts for the projector (Altair). Colours match the presentation deck."""
import altair as alt
import pandas as pd

import content as C

INK, MUTED, GRID = "#1C1B2E", "#5F6178", "#D7D9E3"
THEORY_COLORS = {"Proxemics": "#3D5A98", "Flow": "#E2553B", "Both": "#2A9D8F"}
ZONE_COLORS = {"Intimate": "#E2553B", "Personal": "#F2A33A", "Social": "#2A9D8F", "Public": "#3D5A98"}
# diverging: warm pole = disagree, cool pole = agree, neutral gray midpoint
LIKERT_COLORS = ["#B8432F", "#F0A493", "#C9CBD6", "#92A9D8", "#3D5A98"]


def _style(chart, height):
    return (chart.properties(height=height, background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelFont="Arial", titleFont="Arial", labelFontSize=15, titleFontSize=14,
                            labelColor=MUTED, titleColor=MUTED, domainColor=GRID, tickColor=GRID,
                            gridColor=GRID, gridWidth=0.5, labelLimit=360)
            .configure_legend(labelFont="Arial", titleFont="Arial", labelFontSize=15, titleFontSize=13,
                              labelColor=INK, titleColor=MUTED, orient="top", symbolType="circle",
                              symbolSize=180))


def r1_chart(df):
    """Stacked 100 % bars: which theory explains each scenario?"""
    rows = []
    for i, sc in enumerate(C.R1_SCENARIOS, 1):
        sub = df[df["item"] == sc["id"]]
        n = len(sub)
        for opt in C.R1_OPTIONS:
            k = int((sub["value"] == opt).sum())
            rows.append(dict(scenario=f"{i} · {sc['short']}", option=opt, count=k, n=n,
                             pct=(k / n) if n else 0.0, order=C.R1_OPTIONS.index(opt)))
    d = pd.DataFrame(rows)
    y_order = [f"{i} · {sc['short']}" for i, sc in enumerate(C.R1_SCENARIOS, 1)]
    base = alt.Chart(d).encode(
        y=alt.Y("scenario:N", sort=y_order, title=None),
        x=alt.X("pct:Q", stack="normalize", axis=alt.Axis(format="%", tickCount=5, grid=True), title=None),
        order=alt.Order("order:Q"),
    )
    bars = base.mark_bar(stroke="white", strokeWidth=2, height=34, cornerRadius=3).encode(
        color=alt.Color("option:N", title=None, sort=C.R1_OPTIONS,
                        scale=alt.Scale(domain=list(THEORY_COLORS), range=list(THEORY_COLORS.values()))),
        tooltip=[alt.Tooltip("scenario:N", title="Scenario"), alt.Tooltip("option:N", title="Answer"),
                 alt.Tooltip("count:Q", title="Votes"), alt.Tooltip("pct:Q", title="Share", format=".0%")],
    )
    # selective labels: share at the centre of segments wide enough to hold it
    labels =alt.Chart(d).transform_filter("datum.n > 0").transform_stack(
        stack="pct", as_=["x0", "x1"], groupby=["scenario"], sort=[alt.SortField("order")], offset="normalize"
    ).transform_calculate(mid="(datum.x0 + datum.x1) / 2").transform_filter("datum.pct >= 0.12").mark_text(
        color="white", fontWeight="bold", fontSize=15, font="Arial"
    ).encode(y=alt.Y("scenario:N", sort=y_order), x="mid:Q", text=alt.Text("pct:Q", format=".0%"))
    return _style(bars + labels, height=60 * len(C.R1_SCENARIOS))


def r2_chart(df):
    """Mean disruption (0-10) per event, coloured by Hall zone."""
    rows = []
    for it in C.R2_ITEMS:
        vals = pd.to_numeric(df.loc[df["item"] == it["id"], "value"], errors="coerce").dropna()
        rows.append(dict(event=f"{it['short']} ({it['dist']})", zone=it["zone"], n=len(vals),
                         mean=round(vals.mean(), 1) if len(vals) else None,
                         median=vals.median() if len(vals) else None))
    d = pd.DataFrame(rows)
    order = d["event"].tolist()
    base = alt.Chart(d).encode(y=alt.Y("event:N", sort=order, title=None))
    bars = base.mark_bar(height=30, cornerRadiusEnd=4).encode(
        x=alt.X("mean:Q", scale=alt.Scale(domain=[0, 10]), title="Average disruption (0 = none, 10 = flow gone)",
                axis=alt.Axis(tickCount=6, grid=True)),
        color=alt.Color("zone:N", title="Hall zone", sort=list(ZONE_COLORS),
                        scale=alt.Scale(domain=list(ZONE_COLORS), range=list(ZONE_COLORS.values()))),
        tooltip=[alt.Tooltip("event:N", title="Event"), alt.Tooltip("zone:N", title="Zone"),
                 alt.Tooltip("mean:Q", title="Mean"), alt.Tooltip("median:Q", title="Median"),
                 alt.Tooltip("n:Q", title="Answers")],
    )
    text = base.mark_text(align="left", dx=8, fontSize=16, fontWeight="bold", color=INK, font="Arial").encode(
        x="mean:Q", text=alt.Text("mean:Q", format=".1f"))
    return _style(bars + text, height=58 * len(C.R2_ITEMS))


def r4_chart(df):
    """Diverging stacked bars for the debate statements (neutral centred on 0)."""
    rows = []
    for st_ in C.R4_STATEMENTS:
        sub = df[df["item"] == st_["id"]]
        n = len(sub)
        pct = {lv: ((sub["value"] == lv).sum() / n if n else 0.0) for lv in C.LIKERT}
        start = -(pct[C.LIKERT[0]] + pct[C.LIKERT[1]] + pct[C.LIKERT[2]] / 2)
        for k, lv in enumerate(C.LIKERT):
            rows.append(dict(statement=st_["short"], level=lv, order=k, pct=pct[lv], n=n,
                             count=int((sub["value"] == lv).sum()), x0=start, x1=start + pct[lv]))
            start += pct[lv]
    d = pd.DataFrame(rows)
    order = [s["short"] for s in C.R4_STATEMENTS]
    bars = alt.Chart(d).mark_bar(height=40, stroke="white", strokeWidth=2).encode(
        y=alt.Y("statement:N", sort=order, title=None),
        x=alt.X("x0:Q", title="← disagree        agree →", scale=alt.Scale(domain=[-1, 1]),
                axis=alt.Axis(format="%", values=[-1, -0.5, 0, 0.5, 1], labelExpr="abs(datum.value) * 100 + '%'")),
        x2="x1:Q",
        color=alt.Color("level:N", title=None, sort=C.LIKERT,
                        scale=alt.Scale(domain=C.LIKERT, range=LIKERT_COLORS)),
        tooltip=[alt.Tooltip("statement:N", title="Statement"), alt.Tooltip("level:N", title="Answer"),
                 alt.Tooltip("count:Q", title="People"), alt.Tooltip("pct:Q", title="Share", format=".0%")],
    )
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=MUTED, strokeWidth=1).encode(x="x:Q")
    return _style(bars + zero, height=80 * len(C.R4_STATEMENTS))
