"""All texts of the activity live here, so both groups can edit them without touching app logic.

Proxemics group: Lukas Alois Pöckl, Jeremy Benjamin Tschurtschenthaler
Flow group: Pascal Schäfer, Patrick Fan-Ming Lee
-> Flow group: please check every line marked  # FLOW CHECK

Structure: 6 groups · Join → 1 Feel it → 2 See it → 3 Design it → 4 Judge it → Wrap-up (hosts lead)
"""

TITLE = "Proxemics × Flow"
SUBTITLE = "Theories in HCI · WiSe 26 · joint group activity"
N_GROUPS = 6

# ---------------------------------------------------------------- phases
PHASES = ["lobby", "feel", "see", "design", "judge", "wrap"]
PHASE_META = {
    "lobby": dict(label="Join", minutes=2, title="Scan, join, pick your group",
                  task="Sit with your group (1–6). Scan the QR code, type a nickname and choose your group."),
    "feel": dict(label="1 · Feel it", minutes=9, title="Step 1 · Feel it: does closeness break concentration?",
                 task="Four short trials in your group. Your phone tells you your role and the distance for each trial."),
    "see": dict(label="2 · See it", minutes=5, title="Step 2 · See it: what the class just measured",
                task="Look at the results by distance. Agree on one insight as a group and type it in."),
    "design": dict(label="3 · Design it", minutes=8, title="Step 3 · Design it: protect the flow",
                   task="Design a system for your setting that uses proxemic cues to protect or enable flow. One person types."),
    "judge": dict(label="4 · Judge it", minutes=3, title="Step 4 · Judge it",
                  task="Vote for the best idea and for the idea most likely to turn into a dark pattern (not your own)."),
    "wrap": dict(label="Wrap-up", minutes=3, title="Wrap-up",
                 task="What we learned together. Finish the sentence on your phone."),
}

# ---------------------------------------------------------------- theory cards (lobby)
THEORY_CARDS = {
    "Proxemics": {
        "who": "Edward T. Hall (1963, 1966), anthropology",
        "focus": "How people use and read space between each other",
        "unit": "Relationships between people (and devices) in space",
        "concepts": "Four zones: intimate, personal, social, public · fixed / semi-fixed / informal space · culture",
        "hci": "Proxemic interaction: devices sense distance, orientation, movement, identity, location (Greenberg et al., 2011)",
    },
    "Flow": {  # FLOW CHECK
        "who": "Mihaly Csikszentmihalyi (1975, 1990), psychology",
        "focus": "Optimal experience: being fully absorbed in an activity",
        "unit": "One person's experience during an activity",
        "concepts": "Challenge–skill balance · clear goals · immediate feedback · deep concentration · loss of self-consciousness · altered sense of time",
        "hci": "Game design (GameFlow, Sweetser & Wyeth, 2005), web navigation (Hoffman & Novak, 1996), focus modes",
    },
}

# ---------------------------------------------------------------- step 1: the experiment
N_TRIALS = 4
TRIAL_SECONDS = 45
GRID_MAX = 36          # 6 x 6 number grid (Schulte table); tune in the test run
DISTANCES = {   # key: (label, Hall zone, instruction for the intruder)
    "public": ("Far away (4 m +)", "Public", "Go to the other side of the room and just stand there, facing the worker."),
    "social": ("Two big steps (~2 m)", "Social", "Stand about two big steps away and watch the worker."),
    "personal": ("Arm's length (~0.8 m)", "Personal", "Stand at arm's length next to the worker and watch the worker."),
    "intimate": ("Over the shoulder (~0.3 m)", "Intimate", "Stand right behind the worker's shoulder and look at the sheet. No touching."),
}
ZONE_ORDER = ["public", "social", "personal", "intimate"]   # far → near
# balanced orders (each distance appears in each trial position across groups)
GROUP_ORDERS = {
    1: ["public", "social", "personal", "intimate"],
    2: ["social", "personal", "intimate", "public"],
    3: ["personal", "intimate", "public", "social"],
    4: ["intimate", "public", "social", "personal"],
    5: ["intimate", "personal", "social", "public"],
    6: ["social", "public", "intimate", "personal"],
}
ROLE_TEXT = {
    "worker": ("Worker", "Take the sheet for this trial. When the timer starts, find the numbers 1, 2, 3 … in order and "
                         "cross them out. Stop when the time is up, then enter how far you got."),
    "intruder": ("Intruder", None),   # instruction comes from DISTANCES
    "observer": ("Observer", "Watch the worker during the trial and tick every reaction you see."),
}
TASK_NOTE = "Task: 6 × 6 number grid (Schulte table), printed sheet for trial 1–4."   # FLOW CHECK
REACTIONS = ["Turned head or body away", "Shielded the sheet with hand or arm", "Looked up at the intruder",
             "Laughed or commented", "Slowed down or stopped", "No visible reaction"]
OPT_OUT = "Anyone may skip a distance. Just tick 'skipped' – that trial is then left out of the results."
SEE_QUESTIONS = [
    "Did the distance matter, or rather that someone was watching?",
    "Which reactions did you see? Argyle & Dean (1965): when closeness is forced, we turn other cues down.",
    "What does this say about flow: is flow also a spatial and social condition?",   # FLOW CHECK
]
INSIGHT_PROMPT = "Our group's insight in one sentence"

# ---------------------------------------------------------------- step 3: design
SCENARIOS = [
    dict(name="Library study hall", prompt="People come to concentrate, but others walk past, sit down next to them and whisper."),
    dict(name="Open-plan office", prompt="Deep work at the desk, while colleagues stop by with 'quick questions'."),
    dict(name="Living room with a game console", prompt="One person is deep in a game; flatmates walk through, talk and watch."),
    dict(name="Lecture hall (200 students)", prompt="The lecturer wants focus; laptops, latecomers and neighbours compete for attention."),
    dict(name="Social VR world", prompt="You want to build something in VR, while other avatars come and go around you."),
    dict(name="Train commute", prompt="45 minutes to read or work, in a carriage full of strangers, calls and announcements."),
]
DESIGN_MISSION = ("Use what you just felt: design a system that uses proxemic cues to protect or enable flow. "
                  "Then ask: how could it be misused?")
DIMENSIONS = ["Distance", "Orientation", "Movement", "Identity", "Location"]
FLOW_CONDITIONS = ["Clear goals", "Immediate feedback", "Challenge–skill balance",  # FLOW CHECK
                   "Undisturbed concentration", "Sense of control"]

# ---------------------------------------------------------------- step 4 + wrap-up
JUDGE_BEST = "Best idea"
JUDGE_DARK = "Most likely to become a dark pattern"
EXIT_PROMPT = "In one sentence: how do proxemics and flow relate?"
