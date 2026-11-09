# Proxemics × Flow: live class activity

Joint group activity for *Theories in HCI* (PLUS Salzburg, WiSe 26), session of 14 December 2026.
Proxemics group (Lukas Alois Pöckl, Jeremy Benjamin Tschurtschenthaler) and Flow group (Pascal Schäfer, Patrick Fan-Ming Lee).

The class splits into **6 groups**, joins on their phones via QR code and goes through four steps with the hosts;
the hosts lead the wrap-up. No right or wrong answers: everything comes from what the class does.

| Step | Time | Groups do | Projector shows |
|---|---|---|---|
| Join | 2 min | Sit in 6 groups, scan QR, nickname, pick group | QR code, who joined per group |
| 1 · Feel it | 9 min | 4 short trials per group. Each trial the app assigns roles: **worker** (45 s number grid on paper), **intruder** (stands at the distance shown), **observers** (tick reactions). Roles rotate; each group gets the distances in a different order. | Per group: distance, worker, intruder, who has saved |
| 2 · See it | 5 min | Discuss the class results; one insight per group | Results by distance (numbers found, absorption, awareness, intruder comfort) + reactions seen |
| 3 · Design it | 8 min | Design a system that uses proxemic cues to protect flow in the group's setting | Live idea wall |
| 4 · Judge it | 3 min | Vote: best idea + idea most likely to become a dark pattern (not your own) | Votes (hidden until you switch them on) |
| Wrap-up | 3 min | One-sentence exit ticket | Winners, group insights, key numbers, sentences |

All texts are in `content.py`. Lines the Flow group should check are marked `# FLOW CHECK`.

**Print before class:** `materials/task_sheets_trials_1-4.pdf` (4 pages, one 6×6 grid per trial), **once per group** (6×) plus spares.
Regenerate with `python3 materials/make_task_sheets.py`.

## Addresses

- Students: https://proxemics-flow-activity.streamlit.app/
- Host (projector): https://proxemics-flow-activity.streamlit.app/?host=1 (password from the app's secrets)
- Diagnosis: https://proxemics-flow-activity.streamlit.app/?diag=1

## Runbook

**Before class**
- Test run with both groups (3–4 phones), then sidebar → *Results & reset* → type `RESET`.
- Print the task sheets (6 sets), put group numbers 1–6 on the tables.
- Check *Settings* → number of groups.

**During**
- *Join*: wait until the count matches the room.
- *1 · Feel it*: the app freezes the groups when you open this step (use *Refresh groups* if someone joins late).
  For each trial: choose *Trial 1–4* → people check their phones → start the **45 s** timer → workers enter how far they got,
  intruders their comfort, observers the reactions. Then the next trial.
- *2 · See it*: talk through the charts, groups type one insight.
- *3 · Design it*: walk around; use *Hide* for anything inappropriate.
- *4 · Judge it*: switch on *Show votes* once everyone has voted.
- *Wrap-up*: you lead.

**After**
- Sidebar → *Download all results* (CSV zip incl. `experiment_metrics.csv`, `experiment_reactions.csv`, `insights.csv`).

Safety: no touching; anyone may skip a distance (tick *skipped*; that trial is left out of the results).

## Run locally / deploy

Needs Python 3.11 or newer (Streamlit Cloud: choose 3.12). With [uv](https://docs.astral.sh/uv/):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then set HOST_PASSWORD
uv run --python 3.12 --with-requirements requirements.txt streamlit run app.py
```

Streamlit Community Cloud: repo `JBTPower/proxemics-flow-activity`, branch `main`, file `app.py`; secrets
`HOST_PASSWORD = "…"` and `APP_URL = "https://proxemics-flow-activity.streamlit.app/"`. Pushing to `main` updates the app.

Files: `app.py` (views), `content.py` (texts), `store.py` (shared SQLite state), `charts.py` (live charts), `materials/` (print sheets).
Privacy: only nicknames, group numbers and answers are stored; no accounts, no tracking.
