# config.py — Thought Topology Interface Configuration

# ── Window ──────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
FPS_TARGET    = 30
WINDOW_TITLE  = "Topologies of Thoughts"

# ── Webcam ───────────────────────────────────────────────────────────────────
CAM_INDEX     = 0
CAM_WIDTH     = 640
CAM_HEIGHT    = 480

# ── Layout ───────────────────────────────────────────────────────────────────
GRAPH_PANEL_W = 820          # left panel width
UI_PANEL_X    = 820          # right panel x start

# ── Colors  (B, G, R)  for OpenCV ────────────────────────────────────────────
BG_COLOR           = (8,  8, 12)
NODE_COLOR         = (255, 255, 255)
NODE_HIGHLIGHT     = (180, 255, 120)
NODE_SELECTED      = (100, 220, 255)
EDGE_COLOR         = (80,  80,  90)
EDGE_HIGHLIGHT     = (160, 160, 180)
LABEL_COLOR        = (200, 200, 200)
LABEL_HIGHLIGHT    = (180, 255, 120)
ACCENT_GREEN       = (100, 220, 80)
ACCENT_BLUE        = (220, 180, 80)
UI_TEXT_COLOR      = (240, 240, 240)
UI_DIM_COLOR       = (130, 130, 140)
GLOW_COLOR         = (60,  60,  70)
CURSOR_COLOR       = (255, 255, 255)
PINCH_COLOR        = (100, 255, 180)
BRACKET_COLOR      = (100, 200, 100)

# ── Node Sizes ────────────────────────────────────────────────────────────────
NODE_RADIUS        = 6
NODE_RADIUS_CENTER = 10
NODE_HOVER_RADIUS  = 10
NODE_GLOW_RADIUS   = 20

# ── Animation ─────────────────────────────────────────────────────────────────
DRIFT_SPEED        = 0.0004   # ambient float speed
DRIFT_AMPLITUDE    = 18       # pixels of drift
LERP_SPEED         = 0.08     # layout transition smoothing
EDGE_ANIM_SPEED    = 0.6      # pulse along edges
PARTICLE_LIFE      = 40       # frames
PARTICLE_COUNT     = 6        # per burst

# ── Gesture Thresholds ────────────────────────────────────────────────────────
PINCH_THRESHOLD    = 0.055    # normalised distance
HOVER_RADIUS_PX    = 55       # pixels
DRAG_MIN_DIST      = 8        # pixels before drag starts
TWO_FINGER_ANGLE   = 35       # degrees between index & middle

# ── Graph Nodes ───────────────────────────────────────────────────────────────
NODES = [
    {"id": "core",           "label": "[CORE]",                  "cluster": 0},
    {"id": "genMedia",       "label": "[Generative Media\n& Notation]", "cluster": 1},
    {"id": "artLife",        "label": "[Artificial Life\n& Morphogenesis]", "cluster": 1},
    {"id": "infoTools",      "label": "[History of\nInformation Tools]", "cluster": 2},
    {"id": "cognition",      "label": "[Cognition,\nLanguage & AI]",  "cluster": 2},
    {"id": "interfaceDesign","label": "[Interface Design\n& Aesthetics]", "cluster": 3},
    {"id": "selfOrg",        "label": "self-organization,\nmorphogenesis,\nbiophysics, pattern\nformation", "cluster": 1},
    {"id": "ancestral",      "label": "interface that taps\ninto those\nancestral instincts", "cluster": 3},
    {"id": "robotics",       "label": "robotics learning\npath",    "cluster": 1},
    {"id": "perceptron",     "label": "the perceptron\ncontroversy", "cluster": 2},
    {"id": "infoTheory",     "label": "an information-\ntheoretic\nformulation of\nmathematics", "cluster": 2},
    {"id": "fiveTypes",      "label": "five elemental\ntypes of work", "cluster": 0},
    {"id": "boundaries",     "label": "Boundaries between\npossible experience\n& analysis", "cluster": 3},
    {"id": "machines",       "label": "machines and\nnotions",       "cluster": 3},
    {"id": "readLand",       "label": "reading articles\nlike landscape", "cluster": 2},
]

EDGES = [
    ("core","genMedia"), ("core","artLife"), ("core","infoTools"),
    ("core","cognition"), ("core","interfaceDesign"),
    ("core","selfOrg"), ("core","ancestral"), ("core","robotics"),
    ("core","perceptron"), ("core","infoTheory"), ("core","fiveTypes"),
    ("core","boundaries"), ("core","machines"), ("core","readLand"),
    ("genMedia","robotics"), ("artLife","selfOrg"),
    ("infoTools","perceptron"), ("infoTools","infoTheory"),
    ("cognition","perceptron"), ("cognition","readLand"),
    ("interfaceDesign","ancestral"), ("interfaceDesign","machines"),
]

TOPOLOGIES = ["centralized", "decentralized", "hierarchical", "random"]
TOPOLOGY_DESCRIPTIONS = {
    "centralized":   "one central thought\nconnected to all other nodes",
    "decentralized": "multiple hubs form\nindependent clusters",
    "hierarchical":  "thoughts flow from\ntop-down in layers",
    "random":        "emergent connections\nform chaotic webs",
}