"""All texts of the activity live here, so both groups can edit them without touching app logic.

Proxemics group: Lukas Alois Pöckl, Jeremy Benjamin Tschurtschenthaler
Flow group: Pascal Schäfer, Patrick Fan-Ming Lee
-> Flow group: please check every line marked  # FLOW CHECK
"""

TITLE = "Proxemics × Flow"
SUBTITLE = "Theories in HCI · WiSe 26 · joint group activity"

# ---------------------------------------------------------------- phases
PHASES = ["lobby", "r1", "r2", "r3", "r4", "wrap"]
PHASE_META = {
    "lobby": dict(label="Join", minutes=2, title="Scan, join, pick your table",
                  task="Scan the QR code, type a nickname (optional) and choose the table you are sitting at."),
    "r1": dict(label="1 · Which theory?", minutes=5, title="Round 1 · Proxemics, Flow, or both?",
               task="Six everyday situations. For each one, tap the theory that explains it best."),
    "r2": dict(label="2 · Too close for flow?", minutes=5, title="Round 2 · How close is too close for flow?",
               task="Imagine you are deep in flow. How much would each event break it? 0 = no effect, 10 = flow is gone."),
    "r3": dict(label="3 · Design sprint", minutes=12, title="Round 3 · Design sprint: protect the flow",
               task="With your table: design a proxemic system for your setting that protects or enables flow. One person types, everyone thinks."),
    "r4": dict(label="4 · Debate", minutes=5, title="Round 4 · Where do you stand?",
               task="Three provocative statements. Place yourself, then we let both sides argue."),
    "wrap": dict(label="Wrap-up", minutes=3, title="Wrap-up · Best ideas and one last sentence",
                 task="Like up to two ideas from other tables and finish the sentence on your screen."),
}

# ---------------------------------------------------------------- theory cards
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

# ---------------------------------------------------------------- round 1
R1_OPTIONS = ["Proxemics", "Flow", "Both"]
R1_SCENARIOS = [
    dict(id="museum", short="Museum screen",
         text="A museum screen shows big text when you stand far away and more detail when you step closer.",
         answer="Proxemics", why="Distance is the input: like Vogel & Balakrishnan's (2004) public display phases."),
    dict(id="language", short="Language app",
         text="A language app makes the next exercise harder exactly when you start getting good.",
         answer="Flow", why="Challenge–skill balance keeps you between boredom and anxiety."),  # FLOW CHECK
    dict(id="headphones", short="Big headphones",
         text="In an open-plan office, big headphones tell colleagues: don't come over right now.",
         answer="Both", why="A proxemic signal (keep your distance) used to protect deep concentration."),
    dict(id="vr", short="VR boundary",
         text="In social VR, other avatars cannot come closer to you than about 1.2 m.",
         answer="Proxemics", why="Hall's personal zone, enforced by software (Meta's Personal Boundary, 2022)."),
    dict(id="game", short="'Ten more minutes'",
         text="You play a game for 'just ten minutes', and suddenly it is 1 a.m.",
         answer="Flow", why="Altered sense of time is a classic flow characteristic."),  # FLOW CHECK
    dict(id="studyhall", short="Quiet study screen",
         text="A screen in the study hall notices you are leaning in and focused, and holds all notifications until you lean back.",
         answer="Both", why="Orientation and posture sensing (proxemics) to protect undisturbed concentration (flow)."),
]

# ---------------------------------------------------------------- round 2
R2_CONTEXT = ("Imagine you are deep in flow: writing the last page of a paper, or in the final level of a game. "
              "How much would each of these break your flow?")
R2_ITEMS = [
    dict(id="shoulder", short="Leaning over your shoulder", text="Someone leans over your shoulder to look at your screen", zone="Intimate", dist="~0.3 m"),
    dict(id="phone", short="Phone buzzes by your hand", text="Your phone buzzes on the desk next to your hand", zone="Intimate", dist="~0.3 m"),
    dict(id="sitdown", short="Classmate sits down next to you", text="A classmate sits down right next to you and unpacks", zone="Personal", dist="~0.8 m"),
    dict(id="chat", short="Chat at the next table", text="Two people chat at the next table", zone="Social", dist="~3 m"),
    dict(id="screen", short="Video on a screen across the room", text="A big screen across the room starts a video with sound", zone="Public", dist="~8 m"),
    dict(id="announce", short="Announcement in the hall", text="An announcement echoes through the hall", zone="Public", dist="~15 m"),
]
R2_DISCUSS = ("Does distance predict disruption? What else matters: who it is (identity), whether they face you "
              "(orientation), whether they move, sound, or your own choice?")

# ---------------------------------------------------------------- round 3
R3_SCENARIOS = [
    dict(name="Library study hall", prompt="People come to concentrate, but others walk past, sit down next to them and whisper."),
    dict(name="Open-plan office", prompt="Deep work at the desk, while colleagues stop by with 'quick questions'."),
    dict(name="Living room with a game console", prompt="One person is deep in a game; flatmates walk through, talk and watch."),
    dict(name="Lecture hall (200 students)", prompt="The lecturer wants focus; laptops, latecomers and neighbours compete for attention."),
    dict(name="Social VR world", prompt="You want to build something in VR, while other avatars come and go around you."),
    dict(name="Train commute", prompt="45 minutes to read or work, in a carriage full of strangers, calls and announcements."),
]
DIMENSIONS = ["Distance", "Orientation", "Movement", "Identity", "Location"]
FLOW_CONDITIONS = ["Clear goals", "Immediate feedback", "Challenge–skill balance",  # FLOW CHECK
                   "Undisturbed concentration", "Sense of control"]

# ---------------------------------------------------------------- round 4
LIKERT = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]
R4_STATEMENTS = [
    dict(id="tracking", short="Protect flow by tracking",
         text="Technology should protect my flow, even if it has to track where I am and what I'm doing."),
    dict(id="fit", short="Theories don't fit",
         text="Flow is about the individual, proxemics is about the social: the two theories don't really fit together."),
    dict(id="manipulative", short="Flow design manipulates",
         text="Designing for flow can be just as manipulative as proxemic dark patterns."),
]

# ---------------------------------------------------------------- wrap-up
EXIT_PROMPT = "In one sentence: how do proxemics and flow relate?"
MAX_LIKES = 2
