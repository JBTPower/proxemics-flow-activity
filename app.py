"""Proxemics × Flow — live class activity (Theories in HCI, PLUS Salzburg, WiSe 26).

Participants:  open the app URL (QR code on the projector).
Host:          open the app URL with  ?host=1  and enter the host password.
Run locally:   streamlit run app.py
"""
import html
import io
import os
import time
import uuid

import streamlit as st

IS_HOST_URL = "host" in st.query_params
st.set_page_config(page_title="Proxemics × Flow", page_icon=":material/groups:",
                   layout="wide" if IS_HOST_URL else "centered",
                   initial_sidebar_state="expanded" if IS_HOST_URL else "collapsed")

import charts  # noqa: E402
import content as C  # noqa: E402
import store  # noqa: E402

ZONE_HEX = {"Intimate": "#E2553B", "Personal": "#F2A33A", "Social": "#2A9D8F", "Public": "#3D5A98"}

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
</style>
""")


def esc(s):
    return html.escape(str(s or ""))


def chips(values, cls=""):
    return "".join(f'<span class="chip {cls}">{esc(v)}</span>' for v in values if v)


def phase():
    p = store.get_state("phase", "lobby")
    return p if p in C.PHASES else "lobby"


def n_tables():
    return int(store.get_state("tables", "6"))


def table_scenario(table_no):
    return C.R3_SCENARIOS[(int(table_no) - 1) % len(C.R3_SCENARIOS)]


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
        return url.strip()  # keep a trailing slash: Streamlit Cloud's direct route ".../~/+/" needs it
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
            table = st.selectbox("Which table are you sitting at?", list(range(1, n_tables() + 1)),
                                 format_func=lambda t: f"Table {t}")
            if st.form_submit_button("Join", type="primary", width="stretch"):
                store.join(pid, name.strip() or f"Guest {pid[:3].upper()}", table)
                st.query_params["pid"] = pid
                st.rerun()
        theory_cards()
        return

    st.caption(f"You: **{me['name']}** · Table {me['table_no']}")
    watch_phase(current)
    meta = C.PHASE_META[current]
    st.subheader(meta["title"])
    st.markdown(f'<p class="muted">{esc(meta["task"])}</p>', unsafe_allow_html=True)

    {"lobby": p_lobby, "r1": p_r1, "r2": p_r2, "r3": p_r3, "r4": p_r4, "wrap": p_wrap}[current](pid, me)


@st.fragment(run_every="3s")
def watch_phase(seen):
    """Polls the shared round; reloads the page when the host moves on. Also shows the timer."""
    if phase() != seen:
        st.rerun()
    left = timer_left()
    if left is not None and left > 0:
        st.markdown(f'<div class="muted">⏱ {fmt_left(left)} left</div>', unsafe_allow_html=True)
    elif left == 0:
        st.markdown('<div class="muted">⏱ Time is up, finish your thought</div>', unsafe_allow_html=True)


def theory_cards():
    with st.expander("Both theories in 30 seconds", icon=":material/menu_book:"):
        cols = st.columns(2)
        for col, (name, card) in zip(cols, C.THEORY_CARDS.items()):
            with col:
                st.markdown(f"**{name}**  \n*{card['who']}*")
                st.markdown(f"**Focus:** {card['focus']}  \n**Unit:** {card['unit']}  \n"
                            f"**Key concepts:** {card['concepts']}  \n**In HCI:** {card['hci']}")


def p_lobby(pid, me):
    st.success("You're in. Look at the projector; the first round starts in a moment.", icon=":material/check_circle:")
    theory_cards()


def p_r1(pid, me):
    mine = store.my_answers("r1", pid)
    for i, sc in enumerate(C.R1_SCENARIOS, 1):
        with st.container(border=True):
            st.markdown(f"**{i}.** {sc['text']}")
            st.segmented_control(
                "Your answer", C.R1_OPTIONS, key=f"r1_{sc['id']}", default=mine.get(sc["id"]),
                label_visibility="collapsed", on_change=_save_seg, args=("r1", sc["id"], pid))
    done = len(store.my_answers("r1", pid))
    st.progress(done / len(C.R1_SCENARIOS), text=f"{done} of {len(C.R1_SCENARIOS)} answered · you can change answers any time")


def _save_seg(round_id, item, pid):
    val = st.session_state.get(f"{round_id}_{item}")
    if val:
        store.save_answer(round_id, item, pid, val)


def p_r2(pid, me):
    st.info(C.R2_CONTEXT, icon=":material/self_improvement:")
    mine = store.my_answers("r2", pid)
    with st.form("r2"):
        vals = {}
        for it in C.R2_ITEMS:
            vals[it["id"]] = st.slider(f"{it['text']} · {it['zone'].lower()} zone, {it['dist']}", 0, 10,
                                       int(mine.get(it["id"], 5)), key=f"r2_{it['id']}")
        if st.form_submit_button("Submit my ratings", type="primary", width="stretch"):
            for k, v in vals.items():
                store.save_answer("r2", k, pid, v)
            st.toast("Saved. Watch the projector!", icon=":material/check:")
    if mine:
        st.caption("✓ Your ratings are in. You can change and resubmit them.")


def p_r3(pid, me):
    sc = table_scenario(me["table_no"])
    st.markdown(f"#### Table {me['table_no']}: {sc['name']}")
    st.markdown(f'<p class="muted">{esc(sc["prompt"])}</p>', unsafe_allow_html=True)
    st.markdown("**Your mission:** a system that uses proxemic cues to protect or enable flow. "
                "Then ask yourselves how it could be misused.")
    existing = store.idea_for_table(me["table_no"]) or {}
    if existing.get("title"):
        when = time.strftime("%H:%M", time.localtime(existing["ts"]))
        st.caption(f"Saved by {existing['author']} at {when}. Anyone at your table can edit it.")
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
                store.save_idea(me["table_no"], sc["name"], title.strip(), body.strip(), dims, flow,
                                risk.strip(), me["name"])
                st.toast("Idea saved to the wall!", icon=":material/check:")


def p_r4(pid, me):
    mine = store.my_answers("r4", pid)
    with st.form("r4"):
        vals = {}
        for stt in C.R4_STATEMENTS:
            st.markdown(f"**“{stt['text']}”**")
            vals[stt["id"]] = st.select_slider(stt["short"], C.LIKERT, value=mine.get(stt["id"], "Neutral"),
                                               key=f"r4_{stt['id']}", label_visibility="collapsed")
        if st.form_submit_button("Submit", type="primary", width="stretch"):
            for k, v in vals.items():
                store.save_answer("r4", k, pid, v)
            st.toast("Saved. Be ready to defend your position!", icon=":material/check:")
    if mine:
        st.caption("✓ Your answers are in. You can change and resubmit them.")


def p_wrap(pid, me):
    df = store.ideas()
    liked = store.my_likes(pid)
    st.markdown(f"**Like up to {C.MAX_LIKES} ideas** from other tables ({len(liked)}/{C.MAX_LIKES} used)")
    for _, row in df.iterrows():
        if int(row["table_no"]) == int(me["table_no"]):
            continue
        with st.container(border=True):
            st.markdown(f"**{esc(row['title'])}** · <span class='muted'>Table {int(row['table_no'])}, "
                        f"{esc(row['scenario'])}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='muted'>{esc(row['body'])}</span>", unsafe_allow_html=True)
            on = int(row["table_no"]) in liked
            if st.button(("♥ Liked" if on else "♡ Like") + f" · {int(row['likes'])}", key=f"like_{row['table_no']}",
                         type="primary" if on else "secondary"):
                if not store.toggle_like(pid, int(row["table_no"]), C.MAX_LIKES):
                    st.toast(f"You can like at most {C.MAX_LIKES} ideas. Unlike one first.")
                st.rerun()
    if df.empty:
        st.caption("No ideas on the wall yet.")
    st.divider()
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
            st.caption("Default password in use. Set HOST_PASSWORD in .streamlit/secrets.toml before class.")
        return

    url = join_url()
    with st.sidebar:
        st.markdown(f'<div class="kicker">{esc(C.TITLE)} · host</div>', unsafe_allow_html=True)
        st.image(qr_png(url), width="stretch")
        st.code(url, language=None)
        sidebar_live()
        with st.expander("Settings"):
            new_url = st.text_input("Join URL shown in the QR code", value=url)
            tables = st.number_input("Number of tables", 1, 12, n_tables())
            if st.button("Save settings"):
                store.set_state("join_url", new_url.strip())
                store.set_state("tables", int(tables))
                st.rerun()
        with st.expander("Results & reset"):
            st.download_button("Download all results (CSV zip)", store.export_zip(),
                               file_name=f"proxemics_flow_results_{time.strftime('%Y%m%d_%H%M')}.zip",
                               mime="application/zip", width="stretch")
            confirm = st.text_input("Type RESET to delete all data")
            if st.button("Delete all data", disabled=confirm != "RESET"):
                store.reset_all()
                st.rerun()

    current = phase()
    labels = {p: C.PHASE_META[p]["label"] for p in C.PHASES}
    pick = st.segmented_control("Round", C.PHASES, format_func=labels.get, default=current, key="phase_ctl",
                                label_visibility="collapsed")
    if pick and pick != current:
        store.set_state("phase", pick)
        store.set_state("timer_end", 0)
        st.rerun()

    meta = C.PHASE_META[current]
    left_col, right_col = st.columns([4, 1.3], vertical_alignment="bottom")
    with left_col:
        st.markdown(f'<div class="kicker">{esc(C.SUBTITLE)}</div>', unsafe_allow_html=True)
        st.header(meta["title"], anchor=False)
        st.markdown(f'<p class="bigtask">{esc(meta["task"])}</p>', unsafe_allow_html=True)
    with right_col:
        timer_widget(meta["minutes"])

    {"lobby": h_lobby, "r1": h_r1, "r2": h_r2, "r3": h_r3, "r4": h_r4, "wrap": h_wrap}[current](url)


@st.fragment(run_every="3s")
def sidebar_live():
    df = store.participants()
    st.metric("People joined", len(df))


@st.fragment(run_every="1s")
def timer_widget(default_min):
    left = timer_left()
    if left is not None:
        cls = "timer low" if left <= 30 else "timer"
        st.markdown(f'<div class="{cls}">{fmt_left(left)}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button(f"{default_min} min", help="Start the suggested time for this round", width="stretch"):
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
    if len(df):
        st.markdown(chips(df["name"].tolist()[-60:]), unsafe_allow_html=True)


def h_r1(url):
    r1_live()
    if st.toggle("Reveal our take", key="reveal_r1"):
        for i, sc in enumerate(C.R1_SCENARIOS, 1):
            st.markdown(f"**{i} · {esc(sc['short'])} → {sc['answer']}**: <span class='muted'>{esc(sc['why'])}</span>",
                        unsafe_allow_html=True)


@st.fragment(run_every="3s")
def r1_live():
    df = store.answers("r1")
    st.caption(f"{df['pid'].nunique()} people answered")
    st.altair_chart(charts.r1_chart(df), width="stretch", theme=None)


def h_r2(url):
    r2_live()
    st.markdown(f"**Discuss:** {esc(C.R2_DISCUSS)}")


@st.fragment(run_every="3s")
def r2_live():
    df = store.answers("r2")
    st.caption(f"{df['pid'].nunique()} people answered")
    st.altair_chart(charts.r2_chart(df), width="stretch", theme=None)


def h_r3(url):
    with st.expander("Table settings", expanded=False):
        cols = st.columns(3)
        for t in range(1, n_tables() + 1):
            sc = table_scenario(t)
            cols[(t - 1) % 3].markdown(f"**Table {t}:** {esc(sc['name'])}")
    st.markdown(chips([f"Dimensions: {', '.join(C.DIMENSIONS)}"], "dim") +
                chips([f"Flow conditions: {', '.join(C.FLOW_CONDITIONS)}"], "flow"), unsafe_allow_html=True)
    idea_wall(moderate=True)


@st.fragment(run_every="3s")
def idea_wall(moderate=False, sort_by_likes=False):
    df = store.ideas()
    if df.empty:
        st.info("The idea wall fills up as soon as the first table saves its idea.")
        return
    if sort_by_likes:
        df = df.sort_values("likes", ascending=False)
    cols = st.columns(3)
    for k, (_, row) in enumerate(df.iterrows()):
        with cols[k % 3].container(border=True):
            st.markdown(f"<div class='kicker' style='color:#5F6178'>Table {int(row['table_no'])} · {esc(row['scenario'])}</div>"
                        f"<h4 style='margin:.2rem 0'>{esc(row['title'])}</h4>"
                        f"<p>{esc(row['body'])}</p>"
                        f"{chips([d for d in (row['dims'] or '').split('|')], 'dim')}"
                        f"{chips([f for f in (row['flow'] or '').split('|')], 'flow')}"
                        + (f"<p class='muted' style='margin-top:.5rem'><b>Dark side:</b> {esc(row['risk'])}</p>"
                           if row["risk"] else "")
                        + f"<p style='margin:0'><b>♥ {int(row['likes'])}</b></p>", unsafe_allow_html=True)
            if moderate and st.button("Hide", key=f"hide_{row['table_no']}", help="Remove from the wall"):
                store.hide_idea(int(row["table_no"]))
                st.rerun(scope="fragment")


def h_r4(url):
    for i, stt in enumerate(C.R4_STATEMENTS, 1):
        st.markdown(f"**{i}. {esc(stt['short'])}:** “{esc(stt['text'])}”")
    r4_live()
    st.markdown("**Debate:** one person from each end of the scale gets 30 seconds.")


@st.fragment(run_every="3s")
def r4_live():
    df = store.answers("r4")
    st.caption(f"{df['pid'].nunique()} people answered")
    st.altair_chart(charts.r4_chart(df), width="stretch", theme=None)


def h_wrap(url):
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.markdown("#### Most liked ideas")
        idea_wall(sort_by_likes=True)
    with c2:
        st.markdown(f"#### {esc(C.EXIT_PROMPT)}")
        exit_live()


@st.fragment(run_every="3s")
def exit_live():
    df = store.exits()
    if df.empty:
        st.caption("Waiting for the first sentences…")
    for _, row in df.head(25).iterrows():
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
