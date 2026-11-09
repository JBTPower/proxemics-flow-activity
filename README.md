# Proxemics × Flow: live class activity

Joint group activity for *Theories in HCI* (PLUS Salzburg, WiSe 26), session of 14 December 2026.
Proxemics group (Lukas Alois Pöckl, Jeremy Benjamin Tschurtschenthaler) and Flow group (Pascal Schäfer, Patrick Fan-Ming Lee).

Students join on their phones via QR code; the projector shows the class's answers live.

| Round | Time | What students do | What the projector shows |
|---|---|---|---|
| Join | 2 min | Scan QR, nickname, pick table | QR code, names joining |
| 1 · Which theory? | 5 min | Tap Proxemics / Flow / Both for 6 situations | Stacked bars per situation, then "Reveal our take" |
| 2 · Too close for flow? | 5 min | Rate 6 interruptions at different distances (0–10) | Average disruption per event, coloured by Hall zone |
| 3 · Design sprint | 12 min | Per table: design a proxemic system that protects flow, tag dimensions + flow conditions + dark side | Live idea wall |
| 4 · Debate | 5 min | Agree/disagree with 3 statements | Diverging bars, then 30-second debate |
| Wrap-up | 3 min | Like ≤ 2 ideas, one-sentence exit ticket | Most-liked ideas + sentences |

All texts are in `content.py`; edit them there. Lines the Flow group should check are marked `# FLOW CHECK`.

## Run locally

Needs Python 3.11 or newer (Streamlit Cloud uses 3.14). With [uv](https://docs.astral.sh/uv/):

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then set HOST_PASSWORD
uv run --python 3.14 --with-requirements requirements.txt streamlit run app.py
```

Or in any Python ≥ 3.11 environment: `pip install -r requirements.txt` and `streamlit run app.py`.

- Student view: http://localhost:8501
- Host view (projector): http://localhost:8501/?host=1, then enter the password

Locally, other devices can only join if they are on the same network and the network allows it (uni Wi-Fi often does not). For class, deploy it.

## Deploy for class (Streamlit Community Cloud, free)

1. Push this folder to GitHub (done: `JBTPower/proxemics-flow-activity`). `secrets.toml` and `data/` are excluded by `.gitignore`.
2. Go to https://share.streamlit.io → **Create app** → *Deploy a public app from GitHub*.
3. Repository `JBTPower/proxemics-flow-activity`, branch `main`, main file `app.py`, App URL e.g. `proxemics-flow-activity`.
4. **Advanced settings:**
   - Python version: **3.12** (the app also runs on 3.14, but 3.12 is the safer choice on the cloud).
   - Secrets:
     ```toml
     HOST_PASSWORD = "your-password"
     APP_URL = "https://proxemics-flow-activity.streamlit.app"
     ```
5. **Deploy**, wait 2–3 minutes.
6. **Make it public:** if the GitHub repo is private, the app is private too and students see a login page. Open the app → **Share** → allow anyone with the link, or make the repo public (nothing secret is in it).
7. Open `https://<your-app>.streamlit.app/?host=1` on the presenter laptop.

**If a page stays blank:** open `https://<your-app>.streamlit.app/?diag=1`. It shows the Python and package versions and runs a database write test. Also check **Manage app** (bottom right) → logs.

## Runbook for the session

**Before class (day before)**
- Do a test run with both groups: 3–4 phones, click through all rounds.
- Host sidebar → *Results & reset* → type `RESET` → delete the test data.
- Check *Settings* → number of tables matches the room.

**10 minutes before**
- Open the host URL (free apps fall asleep after inactivity; opening wakes them up).
- Put the browser in full screen; collapse the sidebar if you only need the big QR in the lobby.

**During**
- Move through the rounds with the buttons at the top; every phone follows automatically.
- Start the suggested time with the timer button; `+1` adds a minute.
- Round 1: switch on *Reveal our take* after the votes.
- Round 3: use *Hide* if an idea is inappropriate.

**After**
- Host sidebar → *Download all results* (CSV zip). Useful for the handout and the individual statements.
- The data lives only while the app runs; a restart or redeploy empties it.

## Files

- `app.py`: student and host views
- `content.py`: all scenarios, statements and texts
- `store.py`: shared state (SQLite) for all participants
- `charts.py`: live charts (Altair), colours match the presentation

Privacy: the app stores only nicknames, table numbers and answers; no accounts, no tracking.
