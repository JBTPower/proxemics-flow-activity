"""Shared state for all participants: one SQLite file per running app.

Streamlit gives every browser its own session, so anything the whole class shares
(current round, votes, ideas) lives here. On Streamlit Community Cloud the file
survives as long as the app is running, which is plenty for a 30-minute activity;
export the results (host sidebar) before you close the app.
"""
import io
import os
import sqlite3
import tempfile
import threading
import time
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

# The system temp folder is always local, writable disk (also on Streamlit Cloud, where the
# repo folder is a special mount). Override with the ACTIVITY_DB environment variable.
DB_PATH = os.environ.get("ACTIVITY_DB", str(Path(tempfile.gettempdir()) / "proxemics_flow_activity.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS participants (pid TEXT PRIMARY KEY, name TEXT, table_no INTEGER, joined REAL);
CREATE TABLE IF NOT EXISTS answers (round TEXT, item TEXT, pid TEXT, value TEXT, ts REAL,
                                    PRIMARY KEY (round, item, pid));
CREATE TABLE IF NOT EXISTS ideas (table_no INTEGER PRIMARY KEY, scenario TEXT, title TEXT, body TEXT,
                                  dims TEXT, flow TEXT, risk TEXT, author TEXT, ts REAL, hidden INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS likes (pid TEXT, table_no INTEGER, PRIMARY KEY (pid, table_no));
CREATE TABLE IF NOT EXISTS exits (pid TEXT PRIMARY KEY, text TEXT, ts REAL, hidden INTEGER DEFAULT 0);
"""


@st.cache_resource
def _db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    # default rollback journal (no WAL): WAL needs shared-memory support that some mounts lack
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn, threading.Lock()


def _exec(sql, params=()):
    conn, lock = _db()
    with lock:
        conn.execute(sql, params)
        conn.commit()


def _query(sql, params=()):
    conn, lock = _db()
    with lock:
        return pd.read_sql_query(sql, conn, params=params)


def _one(sql, params=()):
    conn, lock = _db()
    with lock:
        return conn.execute(sql, params).fetchone()


# ---------------------------------------------------------------- state
def get_state(key, default=None):
    row = _one("SELECT value FROM state WHERE key = ?", (key,))
    return row[0] if row else default


def set_state(key, value):
    _exec("INSERT INTO state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
          (key, str(value)))


# ---------------------------------------------------------------- participants
def join(pid, name, table_no):
    _exec("INSERT INTO participants (pid, name, table_no, joined) VALUES (?, ?, ?, ?) "
          "ON CONFLICT(pid) DO UPDATE SET name = excluded.name, table_no = excluded.table_no",
          (pid, name, int(table_no), time.time()))


def get_participant(pid):
    row = _one("SELECT name, table_no FROM participants WHERE pid = ?", (pid,))
    return dict(name=row[0], table_no=row[1]) if row else None


def participants():
    return _query("SELECT pid, name, table_no, joined FROM participants ORDER BY joined")


# ---------------------------------------------------------------- answers (rounds 1, 2, 4)
def save_answer(round_id, item, pid, value):
    _exec("INSERT INTO answers (round, item, pid, value, ts) VALUES (?, ?, ?, ?, ?) "
          "ON CONFLICT(round, item, pid) DO UPDATE SET value = excluded.value, ts = excluded.ts",
          (round_id, item, pid, str(value), time.time()))


def answers(round_id):
    return _query("SELECT item, pid, value FROM answers WHERE round = ?", (round_id,))


def my_answers(round_id, pid):
    df = _query("SELECT item, value FROM answers WHERE round = ? AND pid = ?", (round_id, pid))
    return dict(zip(df["item"], df["value"]))


# ---------------------------------------------------------------- ideas (round 3)
def save_idea(table_no, scenario, title, body, dims, flow, risk, author):
    _exec("INSERT INTO ideas (table_no, scenario, title, body, dims, flow, risk, author, ts, hidden) "
          "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0) ON CONFLICT(table_no) DO UPDATE SET "
          "scenario = excluded.scenario, title = excluded.title, body = excluded.body, dims = excluded.dims, "
          "flow = excluded.flow, risk = excluded.risk, author = excluded.author, ts = excluded.ts, hidden = 0",
          (int(table_no), scenario, title, body, "|".join(dims), "|".join(flow), risk, author, time.time()))


def ideas(include_hidden=False):
    sql = ("SELECT i.table_no, i.scenario, i.title, i.body, i.dims, i.flow, i.risk, i.author, i.ts, i.hidden, "
           "COUNT(l.pid) AS likes FROM ideas i LEFT JOIN likes l ON l.table_no = i.table_no "
           + ("" if include_hidden else "WHERE i.hidden = 0 ") +
           "GROUP BY i.table_no ORDER BY i.table_no")
    return _query(sql)


def idea_for_table(table_no):
    df = _query("SELECT * FROM ideas WHERE table_no = ?", (int(table_no),))
    return df.iloc[0].to_dict() if len(df) else None


def hide_idea(table_no):
    _exec("UPDATE ideas SET hidden = 1 WHERE table_no = ?", (int(table_no),))


def my_likes(pid):
    return set(_query("SELECT table_no FROM likes WHERE pid = ?", (pid,))["table_no"].tolist())


def toggle_like(pid, table_no, max_likes):
    mine = my_likes(pid)
    if table_no in mine:
        _exec("DELETE FROM likes WHERE pid = ? AND table_no = ?", (pid, int(table_no)))
        return True
    if len(mine) >= max_likes:
        return False
    _exec("INSERT OR IGNORE INTO likes (pid, table_no) VALUES (?, ?)", (pid, int(table_no)))
    return True


# ---------------------------------------------------------------- exit tickets
def save_exit(pid, text):
    _exec("INSERT INTO exits (pid, text, ts, hidden) VALUES (?, ?, ?, 0) "
          "ON CONFLICT(pid) DO UPDATE SET text = excluded.text, ts = excluded.ts", (pid, text, time.time()))


def exits(include_hidden=False):
    return _query("SELECT pid, text, ts, hidden FROM exits " + ("" if include_hidden else "WHERE hidden = 0 ") +
                  "ORDER BY ts DESC")


def hide_exit(pid):
    _exec("UPDATE exits SET hidden = 1 WHERE pid = ?", (pid,))


# ---------------------------------------------------------------- admin
def selftest():
    """Write and read back one value; used by the ?diag=1 page."""
    t0 = time.time()
    set_state("_selftest", t0)
    ok = get_state("_selftest") == str(t0)
    return ok, round((time.time() - t0) * 1000, 1)


def reset_all():
    conn, lock = _db()
    with lock:
        for t in ("state", "participants", "answers", "ideas", "likes", "exits"):
            conn.execute(f"DELETE FROM {t}")
        conn.commit()


def export_zip():
    """All results as CSV files in one zip (participants are exported without their random ids)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, sql in [("participants", "SELECT name, table_no, joined FROM participants"),
                          ("answers", "SELECT round, item, value, ts FROM answers"),
                          ("ideas", "SELECT * FROM ideas"),
                          ("likes", "SELECT table_no, COUNT(*) AS likes FROM likes GROUP BY table_no"),
                          ("exit_tickets", "SELECT text, ts FROM exits")]:
            z.writestr(f"{name}.csv", _query(sql).to_csv(index=False))
    return buf.getvalue()
