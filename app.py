"""Proxemics × Flow — live class activity (Theories in HCI, PLUS Salzburg, WiSe 26).

6 groups · Join → 1 Feel it (experiment) → 2 See it → 3 Design it → 4 Judge it → Wrap-up.
Participants:  open the app URL (QR code on the projector).
Host:          open the app URL with  ?host=1  and enter the host password.
Run locally:   streamlit run app.py
"""
import html
import io
import json
import os
import time
import uuid
import zipfile

import pandas as pd
import streamlit as st

IS_HOST_URL = "host" in st.query_params
st.set_page_config(page_title="Proxemics × Flow", page_icon=":material/groups:",
                   layout="wide" if IS_HOST_URL else "centered",
                   initial_sidebar_state="expanded" if IS_HOST_URL else "collapsed")

import charts  # noqa: E402
import content as C  # noqa: E402
import store  # noqa: E402

st.html("""
<style>
  .chip {display:inline-block; padding:2px 10px; margin:2px 4px 2px 0; border-radius:999px;
         font-size:0.8rem; font-weight:600; background:#F2F3F7; color:#1C1B2E; border:1px solid #D7D9E3;}
  .chip.dim {background:#E9EEF8; border-color:#C9D3EA;}
  .chip.flow {background:#FCE8E4; border-color:#F3C4B9;}
  .kicker {letter-spacing:.12em; text-transform:uppercase; font-weight:700; font-size:.8rem; color:#E2553B;}
  .muted {color:#5F6178;}
  .bigtask {font-size:1.35rem; line-height:1.45; color:#1C1B2E;}
  .timer {font-size:2.2rem; font-weight:700; font-variant-numeric:tabular-nums; color:#1C1B2E;}
  .timer.low {color:#E2553B;}
  .quote {font-size:1.05rem; padding:.4rem 0; border-bottom:1px solid #E6E7EE;}
  .role {font-size:1.6rem; font-weight:800; margin:.2rem 0 .1rem 0;}
  .dist {font-size:1.1rem; font-weight:700;}
</style>
""")
ZONE_HEX = {"public": "#3D5A98", "social": "#2A9D8F", "personal": "#B86E06", "intimate": "#E2553B"}


# =====================================================================
# HELPERS
# =====================================================================
def esc(s):
    return html.escape(str(s or ""))


def chips(values, cls=""):
    return "".join(f'<span class="chip {cls}">{esc(v)}</span>' for v in values if v)


def phase():
    p = store.get_state("phase", "lobby")
    return p if p in C.PHASES else "lobby"


def trial():
    try:
        return min(max(int(store.get_state("trial", "1")), 1), C.N_TRIALS)
    except ValueError:
        return 1


def n_groups():
    return int(store.get_state("tables", str(C.N_GROUPS)))


def scenario(group):
    return C.SCENARIOS[(int(group) - 1) % len(C.SCENARIOS)]


def distance(group, t):
    return C.GROUP_ORDERS[((int(group) - 1) % len(C.GROUP_ORDERS)) + 1][t - 1]


def timer_left():
    end = float(store.get_state("timer_end", "0") or 0)
    return max(0, int(end - time.time())) if end else None


def fmt_left(sec):
    return f"{sec // 60:02d}:{sec % 60:02d}"


def _secret(key):
    try:
        return st.secrets.get(key)
    except Exception:  # no secrets.toml present
        return None


def join_url():
    url = store.get_state("join_url") or _secret("APP_URL")
    if url:
        return url.strip()
    host = st.context.headers.get("host", "localhost:8501")
    scheme = "http" if host.startswith(("localhost", "127.", "192.168.", "10.")) else "https"
    return f"{scheme}://{host}"


def host_password():
    return _secret("HOST_PASSWORD") or os.environ.get("HOST_PASSWORD") or "proxemics"


def qr_png(url):
    import qrcode
    img = qrcode.make(url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)  # PNG by default for both qrcode image backends
    return buf.getvalue()


# ---------------------------------------------------------------- groups & roles
def live_roster():
    df = store.participants().sort_values("joined")
    out = {}
    for _, r in df.iterrows():
        out.setdefault(int(r["table_no"]), []).append(r["pid"])
    return out


def roster():
    """Group membership frozen when step 1 starts (late joiners become observers)."""
    snap = store.get_state("roster")
    return {int(k): v for k, v in json.loads(snap).items()} if snap else live_roster()


def snapshot_roster():
    store.set_state("roster", json.dumps(live_roster()))


def roles(group, t):
    members = roster().get(int(group), [])
    if not members:
        return {}
    n = len(members)
    out = {pid: "observer" for pid in members}
    out[members[(t - 1) % n]] = "worker"
    if n >= 2:
        out[members[t % n]] = "intruder"
    return out


def names():
    df = store.participants()
    return dict(zip(df["pid"], df["name"]))


def experiment_frames():
    """Long tables for the charts and the export: metrics (zone, metric, value) and reactions (zone, reaction)."""
    ans = store.answers("exp")
    grp = dict(zip(store.participants()["pid"], store.participants()["table_no"]))
    skipped = set()
    for _, a in ans.iterrows():
        t, key = a["item"].split(":")
        if key == "skip" and a["value"] == "1" and a["pid"] in grp:
            skipped.add((int(grp[a["pid"]]), int(t[1:])))
    met, rea = [], []
    for _, a in ans.iterrows():
        if a["pid"] not in grp:
            continue
        t, key = a["item"].split(":")
        g, tt = int(grp[a["pid"]]), int(t[1:])
        if (g, tt) in skipped or key == "skip":
            continue
        z = distance(g, tt)
        if key == "react":
            for r in [x for x in a["value"].split("|") if x]:
                rea.append(dict(group=g, trial=tt, zone=z, reaction=r))
        else:
            met.append(dict(group=g, trial=tt, zone=z, metric=key, value=a["value"]))
    return (pd.DataFrame(met, columns=["group", "trial", "zone", "metric", "value"]),
            pd.DataFrame(rea, columns=["group", "trial", "zone", "reaction"]))


def insight(group):
    raw = store.get_state(f"insight_{group}")
    return json.loads(raw) if raw else None


# =====================================================================
# PARTICIPANT
# =====================================================================
def participant_view():
    # Identity lives in the session; it is written to the URL only once, after joining,
    # so a reload keeps the same person. Nothing touches the URL on the first visit.
    pid = st.query_params.get("pid") or st.session_state.get("pid") or uuid.uuid4().hex[:12]
    st.session_state["pid"] = pid
    me = store.get_participant(pid)
    current = phase()

    st.markdown(f'<div class="kicker">{esc(C.SUBTITLE)}</div>', unsafe_allow_html=True)
    st.title(C.TITLE)

    if me is None:
        with st.form("join"):
            name = st.text_input("Nickname (optional)", max_chars=24, placeholder="e.g. Anna")
            group = st.selectbox("Which group are you in?", list(range(1, n_groups() + 1)),
                                 format_func=lambda g: f"Group {g}")
            if st.form_submit_button("Join", type="primary", width="stretch"):
                store.join(pid, name.strip() or f"Guest {pid[:3].upper()}", group)
                st.query_params["pid"] = pid
                st.rerun()
        theory_cards()
        return

    st.caption(f"You: **{me['name']}** · Group {me['table_no']}")
    watch_state((current, trial()))
    meta = C.PHASE_META[current]
    st.subheader(meta["title"])
    st.markdown(f'<p class="muted">{esc(meta["task"])}</p>', unsafe_allow_html=True)
    {"lobby": p_lobby, "feel": p_feel, "see": p_see, "design": p_design, "judge": p_judge, "wrap": p_wrap}[current](pid, me)


@st.fragment(run_every="3s")
def watch_state(seen):
    """Polls the shared step and trial; reloads the page when the hosts move on. Also shows the timer."""
    if (phase(), trial()) != seen:
        st.rerun()
    left = timer_left()
    if left is not None and left > 0:
        st.markdown(f'<div class="muted">⏱ {fmt_left(left)} left</div>', unsafe_allow_html=True)
    elif left == 0:
        st.markdown('<div class="muted">⏱ Time is up</div>', unsafe_allow_html=True)


def theory_cards():
    with st.expander("Both theories in 30 seconds", icon=":material/menu_book:"):
        cols = st.columns(2)
        for col, (name, card) in zip(cols, C.THEORY_CARDS.items()):
            with col:
                st.markdown(f"**{name}**  \n*{card['who']}*")
                st.markdown(f"**Focus:** {card['focus']}  \n**Unit:** {card['unit']}  \n"
                            f"**Key concepts:** {card['concepts']}  \n**In HCI:** {card['hci']}")


def p_lobby(pid, me):
    st.success(f"You're in. Sit with group {me['table_no']} and look at the projector.", icon=":material/check_circle:")
    theory_cards()


def p_feel(pid, me):
    g, t = int(me["table_no"]), trial()
    d = distance(g, t)
    label, zone, intruder_text = C.DISTANCES[d]
    r = roles(g, t).get(pid, "observer")
    nm = names()
    who = roles(g, t)
    worker = next((nm.get(p, "?") for p, ro in who.items() if ro == "worker"), "–")
    intruder = next((nm.get(p, "?") for p, ro in who.items() if ro == "intruder"), "a host")
    st.markdown(f'<span class="dist" style="color:{ZONE_HEX[d]}">Trial {t} of {C.N_TRIALS} · {esc(label)} ({zone} zone)</span>',
                unsafe_allow_html=True)
    st.caption(f"Worker: {worker} · Intruder: {intruder}")
    role_name, role_text = C.ROLE_TEXT[r]
    st.markdown(f'<div class="role">You are the {role_name}</div>', unsafe_allow_html=True)
    st.markdown(esc(intruder_text if r == "intruder" else role_text))
    mine = store.my_answers("exp", pid)
    key = f"t{t}:"
    with st.form(f"exp_{t}"):
        if r == "worker":
            score = st.select_slider("How far did you get? (last number crossed out)", list(range(0, C.GRID_MAX + 1)),
                                     value=int(mine.get(key + "score", 0)))
            absorb = st.slider("How absorbed were you in the task?", 1, 7, int(mine.get(key + "absorb", 4)),
                               help="1 = not at all, 7 = completely")
            aware = st.slider("How aware were you of the intruder?", 1, 7, int(mine.get(key + "aware", 4)),
                              help="1 = not at all, 7 = constantly")
            skip = st.checkbox("We skipped this distance", value=mine.get(key + "skip") == "1")
            vals = {"score": score, "absorb": absorb, "aware": aware, "skip": int(skip)}
        elif r == "intruder":
            comfort = st.slider("How comfortable were you at this distance?", 1, 7, int(mine.get(key + "comfort", 4)),
                                help="1 = very uncomfortable, 7 = completely fine")
            vals = {"comfort": comfort}
        else:
            prev = [x for x in mine.get(key + "react", "").split("|") if x]
            picked = [rc for rc in C.REACTIONS if st.checkbox(rc, value=rc in prev, key=f"rc_{t}_{rc}")]
            vals = {"react": "|".join(picked)}
        if st.form_submit_button("Save", type="primary", width="stretch"):
            for k, v in vals.items():
                store.save_answer("exp", key + k, pid, v)
            st.toast("Saved. Wait for the next trial.", icon=":material/check:")
    if any(k.startswith(key) for k in mine):
        st.caption("✓ Saved for this trial. You can still change it.")
    st.caption(C.OPT_OUT)


def p_see(pid, me):
    g = int(me["table_no"])
    st.info("Look at the projector: the class results by distance.", icon=":material/bar_chart:")
    for q in C.SEE_QUESTIONS:
        st.markdown(f"- {esc(q)}")
    cur = insight(g)
    if cur:
        st.caption(f"Saved by {cur['author']}. Anyone in your group can change it.")
    with st.form("insight"):
        txt = st.text_area(C.INSIGHT_PROMPT, value=(cur or {}).get("text", ""), max_chars=220)
        if st.form_submit_button("Save our insight", type="primary", width="stretch") and txt.strip():
            store.set_state(f"insight_{g}", json.dumps(dict(text=txt.strip(), author=me["name"], ts=time.time())))
            st.toast("Saved!", icon=":material/check:")


def p_design(pid, me):
    g = int(me["table_no"])
    sc = scenario(g)
    st.markdown(f"#### Group {g}: {sc['name']}")
    st.markdown(f'<p class="muted">{esc(sc["prompt"])}</p>', unsafe_allow_html=True)
    st.markdown(f"**Your mission:** {C.DESIGN_MISSION}")
    existing = store.idea_for_table(g) or {}
    if existing.get("title"):
        st.caption(f"Saved by {existing['author']} at {time.strftime('%H:%M', time.localtime(existing['ts']))}. "
                   "Anyone in your group can edit it.")
    with st.form("idea"):
        title = st.text_input("Name of your idea", value=existing.get("title", ""), max_chars=60)
        body = st.text_area("How does it work? (2–3 sentences)", value=existing.get("body", ""), max_chars=500)
        dims = st.multiselect("Which proxemic dimensions does it sense?", C.DIMENSIONS,
                              default=[d for d in (existing.get("dims") or "").split("|") if d in C.DIMENSIONS])
        flow = st.multiselect("Which flow condition does it support?", C.FLOW_CONDITIONS,
                              default=[f for f in (existing.get("flow") or "").split("|") if f in C.FLOW_CONDITIONS])
        risk = st.text_area("Dark side: how could it be misused?", value=existing.get("risk", ""), max_chars=300)
        if st.form_submit_button("Save our idea", type="primary", width="stretch"):
            if not title.strip():
                st.warning("Give your idea a name first.")
            else:
                store.save_idea(g, sc["name"], title.strip(), body.strip(), dims, flow, risk.strip(), me["name"])
                st.toast("Idea saved to the wall!", icon=":material/check:")


def p_judge(pid, me):
    g = int(me["table_no"])
    df = store.ideas()
    others = df[df["table_no"] != g]
    if others.empty:
        st.caption("No ideas from other groups yet.")
        return
    for _, row in others.iterrows():
        with st.container(border=True):
            st.markdown(f"**Group {int(row['table_no'])} · {esc(row['title'])}**  \n"
                        f"<span class='muted'>{esc(row['body'])}</span>", unsafe_allow_html=True)
            if row["risk"]:
                st.caption(f"Dark side (their view): {row['risk']}")
    mine = store.my_answers("judge", pid)
    opts = [int(x) for x in others["table_no"].tolist()]
    fmt = lambda x: f"Group {x}"
    with st.form("judge"):
        best = st.radio(C.JUDGE_BEST, opts, format_func=fmt, horizontal=True,
                        index=opts.index(int(mine["best"])) if mine.get("best") and int(mine["best"]) in opts else None)
        dark = st.radio(C.JUDGE_DARK, opts, format_func=fmt, horizontal=True,
                        index=opts.index(int(mine["dark"])) if mine.get("dark") and int(mine["dark"]) in opts else None)
        if st.form_submit_button("Vote", type="primary", width="stretch"):
            for k, v in (("best", best), ("dark", dark)):
                if v is not None:
                    store.save_answer("judge", k, pid, v)
            st.toast("Thanks for voting!", icon=":material/check:")


def p_wrap(pid, me):
    st.info("Look at the projector for the results.", icon=":material/emoji_events:")
    with st.form("exit"):
        txt = st.text_input(C.EXIT_PROMPT, max_chars=200)
        if st.form_submit_button("Send", type="primary", width="stretch") and txt.strip():
            store.save_exit(pid, txt.strip())
            st.toast("Thanks!", icon=":material/check:")


# =====================================================================
# HOST / PROJECTOR
# =====================================================================
def host_view():
    if not st.session_state.get("is_host"):
        st.title("Host login")
        pw = st.text_input("Host password", type="password")
        if st.button("Enter", type="primary"):
            if pw == host_password():
                st.session_state["is_host"] = True
                st.rerun()
            else:
                st.error("Wrong password.")
        if host_password() == "proxemics":
            st.caption("Default password in use. Set HOST_PASSWORD in the app's secrets before class.")
        return

    url = join_url()
    with st.sidebar:
        st.markdown(f'<div class="kicker">{esc(C.TITLE)} · host</div>', unsafe_allow_html=True)
        st.image(qr_png(url), width="stretch")
        st.code(url, language=None)
        sidebar_live()
        with st.expander("Settings"):
            new_url = st.text_input("Join URL shown in the QR code", value=url)
            groups = st.number_input("Number of groups", 1, 12, n_groups())
            if st.button("Save settings"):
                store.set_state("join_url", new_url.strip())
                store.set_state("tables", int(groups))
                st.rerun()
        with st.expander("Results & reset"):
            st.download_button("Download all results (CSV zip)", export_zip(),
                               file_name=f"proxemics_flow_results_{time.strftime('%Y%m%d_%H%M')}.zip",
                               mime="application/zip", width="stretch")
            confirm = st.text_input("Type RESET to delete all data")
            if st.button("Delete all data", disabled=confirm != "RESET"):
                store.reset_all()
                st.rerun()

    current = phase()
    labels = {p: C.PHASE_META[p]["label"] for p in C.PHASES}
    pick = st.segmented_control("Step", C.PHASES, format_func=labels.get, default=current, key="phase_ctl",
                                label_visibility="collapsed")
    if pick and pick != current:
        store.set_state("phase", pick)
        store.set_state("timer_end", 0)
        if pick == "feel" and not store.get_state("roster"):
            snapshot_roster()
            store.set_state("trial", 1)
        st.rerun()

    meta = C.PHASE_META[current]
    left_col, right_col = st.columns([4, 1.3], vertical_alignment="bottom")
    with left_col:
        st.markdown(f'<div class="kicker">{esc(C.SUBTITLE)}</div>', unsafe_allow_html=True)
        st.header(meta["title"], anchor=False)
        st.markdown(f'<p class="bigtask">{esc(meta["task"])}</p>', unsafe_allow_html=True)
    with right_col:
        timer_widget(C.TRIAL_SECONDS / 60 if current == "feel" else meta["minutes"])
    {"lobby": h_lobby, "feel": h_feel, "see": h_see, "design": h_design, "judge": h_judge, "wrap": h_wrap}[current](url)


def export_zip():
    met, rea = experiment_frames()
    buf = io.BytesIO(store.export_zip())
    with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as z:
        z.writestr("experiment_metrics.csv", met.to_csv(index=False))
        z.writestr("experiment_reactions.csv", rea.to_csv(index=False))
        z.writestr("insights.csv", pd.DataFrame([dict(group=g, **(insight(g) or {})) for g in range(1, n_groups() + 1)])
                   .to_csv(index=False))
    return buf.getvalue()


@st.fragment(run_every="3s")
def sidebar_live():
    st.metric("People joined", len(store.participants()))


@st.fragment(run_every="1s")
def timer_widget(default_min):
    left = timer_left()
    if left is not None:
        cls = "timer low" if left <= 10 else "timer"
        st.markdown(f'<div class="{cls}">{fmt_left(left)}</div>', unsafe_allow_html=True)
    label = f"{int(default_min * 60)} s" if default_min < 1 else f"{int(default_min)} min"
    c1, c2, c3 = st.columns(3)
    if c1.button(label, help="Start the suggested time", width="stretch"):
        store.set_state("timer_end", time.time() + 60 * default_min)
        st.rerun(scope="fragment")
    if c2.button("+1", help="Add one minute", width="stretch"):
        base = max(time.time(), float(store.get_state("timer_end", "0") or 0))
        store.set_state("timer_end", base + 60)
        st.rerun(scope="fragment")
    if c3.button("■", help="Stop the timer", width="stretch"):
        store.set_state("timer_end", 0)
        st.rerun(scope="fragment")


def h_lobby(url):
    c1, c2 = st.columns([1, 1.4], vertical_alignment="center")
    with c1:
        st.image(qr_png(url), width="stretch")
    with c2:
        st.markdown(f"### {esc(url)}")
        lobby_live()


@st.fragment(run_every="3s")
def lobby_live():
    df = store.participants()
    st.metric("People joined", len(df))
    for g in range(1, n_groups() + 1):
        members = df[df["table_no"] == g]["name"].tolist()
        st.markdown(f"**Group {g}** ({len(members)}) " + chips(members), unsafe_allow_html=True)


def h_feel(url):
    t = trial()
    c1, c2 = st.columns([3, 1], vertical_alignment="center")
    with c1:
        pick = st.segmented_control("Trial", list(range(1, C.N_TRIALS + 1)), default=t, key="trial_ctl",
                                    format_func=lambda x: f"Trial {x}", label_visibility="collapsed")
        if pick and pick != t:
            store.set_state("trial", pick)
            store.set_state("timer_end", 0)
            st.rerun()
    with c2:
        if st.button("Refresh groups", help="Re-read group membership (use if people joined late)"):
            snapshot_roster()
            st.rerun()
    st.markdown(f"**Trial {t}:** workers take **sheet {t}**, intruders go to the distance shown on their phone. "
                f"Start the {C.TRIAL_SECONDS} s timer when everyone is in place. {esc(C.OPT_OUT)}")
    feel_progress(t)


@st.fragment(run_every="3s")
def feel_progress(t):
    nm = names()
    mine = store.answers("exp")
    done = set(mine[mine["item"].str.startswith(f"t{t}:")]["pid"]) if len(mine) else set()
    rows = []
    for g in range(1, n_groups() + 1):
        ro = roles(g, t)
        if not ro:
            continue
        d = distance(g, t)
        w = next((p for p, r in ro.items() if r == "worker"), None)
        i = next((p for p, r in ro.items() if r == "intruder"), None)
        obs = [p for p, r in ro.items() if r == "observer"]
        rows.append({"Group": g, "Distance": C.DISTANCES[d][0], "Worker": nm.get(w, "–") + (" ✓" if w in done else ""),
                     "Intruder": (nm.get(i, "–") + (" ✓" if i in done else "")) if i else "host",
                     "Observers saved": f"{sum(p in done for p in obs)}/{len(obs)}"})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("Nobody has joined a group yet.")


def h_see(url):
    see_live()
    st.markdown("**Discuss:** " + " · ".join(esc(q) for q in C.SEE_QUESTIONS))
    insights_live()


@st.fragment(run_every="3s")
def see_live():
    met, rea = experiment_frames()
    n_trials = len(met[met["metric"] == "score"])
    st.caption(f"{n_trials} worker trials · {len(rea)} observed reactions (skipped trials left out)")
    st.altair_chart(charts.zone_metrics(met), width="stretch", theme=None)
    st.altair_chart(charts.reactions_grid(rea), width="stretch", theme=None)


@st.fragment(run_every="3s")
def insights_live():
    items = [(g, insight(g)) for g in range(1, n_groups() + 1)]
    items = [(g, i) for g, i in items if i]
    if items:
        st.markdown("#### Group insights")
        for g, i in items:
            st.markdown(f"<div class='quote'><b>Group {g}:</b> “{esc(i['text'])}”</div>", unsafe_allow_html=True)


def h_design(url):
    with st.expander("Group settings", expanded=False):
        cols = st.columns(3)
        for g in range(1, n_groups() + 1):
            cols[(g - 1) % 3].markdown(f"**Group {g}:** {esc(scenario(g)['name'])}")
    st.markdown(chips([f"Dimensions: {', '.join(C.DIMENSIONS)}"], "dim") +
                chips([f"Flow conditions: {', '.join(C.FLOW_CONDITIONS)}"], "flow"), unsafe_allow_html=True)
    idea_wall(moderate=True)


@st.fragment(run_every="3s")
def idea_wall(moderate=False):
    df = store.ideas()
    if df.empty:
        st.info("The idea wall fills up as soon as the first group saves its idea.")
        return
    cols = st.columns(3)
    for k, (_, row) in enumerate(df.iterrows()):
        with cols[k % 3].container(border=True):
            st.markdown(f"<div class='kicker' style='color:#5F6178'>Group {int(row['table_no'])} · {esc(row['scenario'])}</div>"
                        f"<h4 style='margin:.2rem 0'>{esc(row['title'])}</h4><p>{esc(row['body'])}</p>"
                        f"{chips([d for d in (row['dims'] or '').split('|')], 'dim')}"
                        f"{chips([f for f in (row['flow'] or '').split('|')], 'flow')}"
                        + (f"<p class='muted' style='margin-top:.5rem'><b>Dark side:</b> {esc(row['risk'])}</p>"
                           if row["risk"] else ""), unsafe_allow_html=True)
            if moderate and st.button("Hide", key=f"hide_{row['table_no']}", help="Remove from the wall"):
                store.hide_idea(int(row["table_no"]))
                st.rerun(scope="fragment")


def h_judge(url):
    show = st.toggle("Show votes", key="show_votes", help="Keep hidden while people vote, to avoid bandwagon effects")
    judge_live(show)


@st.fragment(run_every="3s")
def judge_live(show):
    v = store.answers("judge")
    st.caption(f"{v['pid'].nunique() if len(v) else 0} people voted")
    groups = [int(x) for x in store.ideas()["table_no"].tolist()]
    if show and groups:
        st.altair_chart(charts.votes(v, groups), width="stretch", theme=None)
    elif not show:
        idea_wall()


def h_wrap(url):
    v = store.answers("judge")
    ideas = store.ideas().set_index("table_no")
    met, _ = experiment_frames()
    c1, c2, c3 = st.columns(3)
    for col, (item, title) in zip((c1, c2), (("best", C.JUDGE_BEST), ("dark", C.JUDGE_DARK))):
        with col:
            st.markdown(f"#### {title}")
            sub = v[v["item"] == item]["value"].value_counts()
            if len(sub) and int(sub.index[0]) in ideas.index:
                g = int(sub.index[0]); row = ideas.loc[g]
                st.markdown(f"**Group {g} · {esc(row['title'])}** ({int(sub.iloc[0])} votes)  \n{esc(row['body'])}")
            else:
                st.caption("No votes yet.")
    with c3:
        st.markdown("#### What we measured")
        for key, label in (("score", "Numbers found"), ("absorb", "Absorption")):
            sub = met[met["metric"] == key]
            far = pd.to_numeric(sub[sub["zone"] == "public"]["value"]).mean()
            near = pd.to_numeric(sub[sub["zone"] == "intimate"]["value"]).mean()
            if pd.notna(far) and pd.notna(near):
                st.markdown(f"**{label}:** {far:.1f} far away → {near:.1f} over the shoulder")
    insights_live()
    st.markdown(f"#### {esc(C.EXIT_PROMPT)}")
    exit_live()


@st.fragment(run_every="3s")
def exit_live():
    df = store.exits()
    if df.empty:
        st.caption("Waiting for the first sentences…")
    for _, row in df.head(20).iterrows():
        c1, c2 = st.columns([8, 1])
        c1.markdown(f"<div class='quote'>“{esc(row['text'])}”</div>", unsafe_allow_html=True)
        if c2.button("✕", key=f"hx_{row['pid']}", help="Hide"):
            store.hide_exit(row["pid"])
            st.rerun(scope="fragment")


# =====================================================================
# DIAGNOSIS  (open the app with ?diag=1 if something does not load)
# =====================================================================
def diag_view():
    import platform
    import sys
    from importlib.metadata import version
    st.title("Diagnosis")
    rows = {"Python": sys.version.split()[0], "Platform": platform.platform(),
            "Working directory": os.getcwd(), "Database file": store.DB_PATH}
    for pkg in ("streamlit", "altair", "pandas", "qrcode"):
        try:
            rows[pkg] = version(pkg)
        except Exception as exc:  # pragma: no cover
            rows[pkg] = f"missing ({exc})"
    try:
        ok, ms = store.selftest()
        rows["Database write test"] = f"{'OK' if ok else 'FAILED'} ({ms} ms)"
    except Exception as exc:
        rows["Database write test"] = f"ERROR: {exc!r}"
    rows["Host password set"] = "yes" if _secret("HOST_PASSWORD") else "no (default in use)"
    rows["Join URL"] = join_url()
    st.table({"Check": list(rows), "Result": [str(v) for v in rows.values()]})


if "diag" in st.query_params:
    diag_view()
elif IS_HOST_URL:
    host_view()
else:
    participant_view()
