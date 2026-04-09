# renderer.py — Full OpenCV renderer with webcam background + hand skeleton

import cv2
import numpy as np
import math
from config import *
from graph_engine import GraphEngine
from gesture_controller import GestureController

def _alpha_blend(dst, overlay, alpha):
    cv2.addWeighted(overlay, alpha, dst, 1 - alpha, 0, dst)

def draw_glow_circle(canvas, cx, cy, radius, color, glow_radius, intensity=0.45):
    gl = np.zeros_like(canvas)
    cv2.circle(gl, (cx, cy), glow_radius, color, -1)
    gl = cv2.GaussianBlur(gl, (0, 0), max(1, glow_radius // 2))
    _alpha_blend(canvas, gl, intensity)
    cv2.circle(canvas, (cx, cy), radius, color, -1)

def draw_text_ml(canvas, text, x, y, color, scale=0.38, thickness=1, line_height=17):
    for i, line in enumerate(text.split("\n")):
        cv2.putText(canvas, line, (x, y + i * line_height),
                    cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness, cv2.LINE_AA)

def _mn(c, cx, cy, r=4, col=(220, 220, 220)):
    cv2.circle(c, (int(cx), int(cy)), r, col, -1)

def _me(c, x1, y1, x2, y2, col=(90, 90, 100)):
    cv2.line(c, (int(x1), int(y1)), (int(x2), int(y2)), col, 1, cv2.LINE_AA)

def _mini_centralized(c, ox, oy):
    _mn(c, ox, oy, 7, (255, 255, 255))
    for i in range(11):
        a = 2 * math.pi * i / 11
        nx, ny = ox + math.cos(a) * 40, oy + math.sin(a) * 40
        _me(c, ox, oy, nx, ny)
        _mn(c, nx, ny, 3)

def _mini_decentral(c, ox, oy):
    hubs = [(ox-32, oy-22), (ox+32, oy-22), (ox-32, oy+22), (ox+32, oy+22)]
    for hx, hy in hubs:
        _mn(c, hx, hy, 5, (200, 200, 200))
        for a in [i * 2 * math.pi / 3 for i in range(3)]:
            nx, ny = hx + math.cos(a) * 18, hy + math.sin(a) * 18
            _me(c, hx, hy, nx, ny); _mn(c, nx, ny, 2)

def _mini_hierarchical(c, ox, oy):
    rows = [[(ox, oy-36)], [(ox-28, oy), (ox+28, oy)],
            [(ox-44, oy+30), (ox-14, oy+30), (ox+14, oy+30), (ox+44, oy+30)]]
    sizes = [7, 5, 3]
    parents = [[], [0, 0], [0, 1, 1, 1]]
    for li, row in enumerate(rows):
        for j, (nx, ny) in enumerate(row):
            if li > 0:
                pi = min(parents[li][j], len(rows[li-1])-1)
                px, py = rows[li-1][pi]
                _me(c, px, py, nx, ny)
            _mn(c, nx, ny, sizes[li])

def _mini_random(c, ox, oy):
    import random; random.seed(7)
    pts = [(ox + random.randint(-44, 44), oy + random.randint(-34, 34)) for _ in range(9)]
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            if random.random() < 0.32:
                _me(c, *pts[i], *pts[j])
    for px, py in pts: _mn(c, px, py, 3)

MINI_DIAGRAMS = {
    "centralized":  _mini_centralized,
    "decentralized": _mini_decentral,
    "hierarchical": _mini_hierarchical,
    "random":       _mini_random,
}

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]


class Renderer:
    def __init__(self, graph: GraphEngine, controller: GestureController):
        self.graph = graph
        self.ctrl  = controller
        self.W = WINDOW_WIDTH
        self.H = WINDOW_HEIGHT
        self._edge_phase = 0.0
        self._t = 0

    def render(self, webcam_frame=None, cam_frame=None) -> np.ndarray:
        if webcam_frame is None:
          webcam_frame = cam_frame
        

        canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)
        if webcam_frame is not None:
            frame = cv2.flip(webcam_frame, 1)
            frame = cv2.convertScaleAbs(frame, alpha=0.75, beta=-10)
            frame = cv2.resize(frame, (self.W, self.H))
            canvas[:, :] = frame

        self._edge_phase += 0.018
        self._t += 1
        self._draw_grid(canvas, color=(40, 40, 40))
        self._draw_edges(canvas, color=(255, 255, 255))
        self._draw_particles(canvas)
        self._draw_nodes(canvas, label_color=(255, 255, 255), node_color=(255, 255, 255))
        self._draw_hand_skeleton(canvas)
        self._draw_right_panel(canvas)
        self._draw_cursor(canvas)
        self._draw_hud(canvas)

        return canvas

    def _draw_grid(self, c, color=(40, 40, 40)):
        for x in range(0, GRAPH_PANEL_W, 60):
            cv2.line(c, (x, 0), (x, self.H), color, 1)
        for y in range(0, self.H, 60):
            cv2.line(c, (0, y), (GRAPH_PANEL_W, y), color, 1)

    def _draw_hand_skeleton(self, c):
        tracker = self.ctrl.tracker
        if tracker.num_hands() == 0:
            return
        for hand_lms in tracker.landmarks_n:
            def to_px(lm):
                x = int((1.0 - lm["x"]) * GRAPH_PANEL_W)
                y = int(lm["y"] * self.H)
                return (x, y)
            pts = [to_px(lm) for lm in hand_lms]
            for a, b in HAND_CONNECTIONS:
                cv2.line(c, pts[a], pts[b], (60, 180, 80), 1, cv2.LINE_AA)
            for i, pt in enumerate(pts):
                r = 5 if i in (4, 8) else 3
                col = (100, 255, 140) if i in (4, 8) else (180, 255, 180)
                cv2.circle(c, pt, r, col, -1, cv2.LINE_AA)
            t4, t8 = pts[4], pts[8]
            pinching = self.ctrl.tracker.is_pinching(threshold=PINCH_THRESHOLD)
            line_col = (80, 255, 160) if pinching else (60, 120, 80)
            line_thick = 2 if pinching else 1
            cv2.line(c, t4, t8, line_col, line_thick, cv2.LINE_AA)
            dist_n = tracker.get_pinch_distance()
            label = "PINCH!" if pinching else f"d={dist_n:.3f}"
            mid = ((t4[0]+t8[0])//2, (t4[1]+t8[1])//2 - 12)
            col_txt = (80, 255, 140) if pinching else (80, 140, 80)
            cv2.putText(c, label, mid, cv2.FONT_HERSHEY_DUPLEX, 0.38, col_txt, 1, cv2.LINE_AA)

    def _draw_edges(self, c, color=(255, 255, 255)):
        sel  = self.graph.selected_node
        hovn = self.graph.hovered_node
        for a, b in self.graph.edges:
            ax, ay = (int(v) for v in self.graph.current_pos.get(a, (0, 0)))
            bx, by = (int(v) for v in self.graph.current_pos.get(b, (0, 0)))
            active = (a in (sel, hovn)) or (b in (sel, hovn))
            col    = color if not active else (0, 255, 0)
            thick  = 2 if active else 1
            cv2.line(c, (ax, ay), (bx, by), col, thick, cv2.LINE_AA)
            if active:
                ph = (self._edge_phase + hash((a, b)) * 0.37) % 1.0
                px = int(ax + (bx-ax)*ph); py = int(ay + (by-ay)*ph)
                cv2.circle(c, (px, py), 2, (180, 255, 180), -1)

    def _draw_particles(self, c):
        for p in self.graph.particles:
            x, y = int(p.x), int(p.y)
            if 0 <= x < self.W and 0 <= y < self.H:
                r   = max(1, int(p.radius))
                alp = p.alpha
                col = (int(160*alp), int(255*alp), int(140*alp))
                cv2.circle(c, (x, y), r, col[::-1], -1)

    def _draw_nodes(self, c, label_color=(255, 255, 255), node_color=(255, 255, 255)):
        sel  = self.graph.selected_node
        hovn = self.graph.hovered_node
        for nid, pos in self.graph.current_pos.items():
            cx, cy = int(pos[0]), int(pos[1])
            is_core = nid == "core"
            is_sel  = nid == sel
            is_hov  = nid == hovn
            dot_col = node_color
            glow_r = 24 if (is_sel or is_hov) else 13
            dot_r = (NODE_RADIUS_CENTER if is_core else NODE_RADIUS) + (2 if (is_sel or is_hov) else 0)
            draw_glow_circle(c, cx, cy, dot_r, dot_col[::-1], glow_r, 0.4 if (is_sel or is_hov) else 0.22)
            if is_sel:
                s = 26; bc = (0, 255, 0)
                for sx, sy, dx, dy in [(-s,-s,8,0),(-s,-s,0,8),(s,-s,-8,0),(s,-s,0,8),
                                        (-s,s,8,0),(-s,s,0,-8),(s,s,-8,0),(s,s,0,-8)]:
                    cv2.line(c,(cx+sx,cy+sy),(cx+sx+dx,cy+sy+dy),bc,1)
            label = self.graph.nodes[nid]["label"]
            draw_text_ml(c, label, cx + dot_r + 5, cy - 3, label_color, scale=0.33)

    def _draw_right_panel(self, c):
        px = UI_PANEL_X

        overlay = c.copy()
        cv2.rectangle(overlay, (px, 0), (self.W, self.H), (8, 8, 12), -1)
        cv2.addWeighted(overlay, 0.78, c, 0.22, 0, c)

        cv2.line(c, (px, 0), (px, self.H), (35, 35, 45), 1)

        cx = px + (self.W - px) // 2

        cv2.putText(c, "Topologies of", (px+22, 68),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (230, 230, 230), 1, cv2.LINE_AA)
        cv2.putText(c, "Thoughts", (px+22, 108),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (230, 230, 230), 1, cv2.LINE_AA)

        fn = MINI_DIAGRAMS.get(self.graph.topology, _mini_centralized)
        fn(c, cx, 240)

        cv2.putText(c, f"mode: {self.graph.topology}", (px+22, 318),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, (130, 210, 130), 1, cv2.LINE_AA)

        from config import TOPOLOGY_DESCRIPTIONS
        desc = TOPOLOGY_DESCRIPTIONS.get(self.graph.topology, "")
        draw_text_ml(c, desc, px+22, 352, (150, 150, 165), scale=0.38, line_height=19)

        ly = 468
        cv2.putText(c, "GESTURES", (px+22, ly),
                    cv2.FONT_HERSHEY_DUPLEX, 0.38, (70, 70, 80), 1, cv2.LINE_AA)
        gestures = [
            ("INDEX FINGER", "point / hover"),
            ("PINCH",        "select node"),
            ("PINCH+DRAG",   "move node"),
            ("OPEN HAND",    "reset view"),
            ("TWO FINGERS",  "switch topology"),
        ]
        for i, (g, d) in enumerate(gestures):
            gy = ly + 22 + i * 21
            cv2.putText(c, g, (px+22, gy), cv2.FONT_HERSHEY_DUPLEX, 0.34,
                        (90, 210, 90), 1, cv2.LINE_AA)
            cv2.putText(c, d, (px+148, gy), cv2.FONT_HERSHEY_DUPLEX, 0.34,
                        (105, 105, 115), 1, cv2.LINE_AA)

        if self.ctrl.tracker.num_hands() > 0:
            d = self.ctrl.tracker.get_pinch_distance()
            bar_x = px + 22; bar_y = 610; bar_w = self.W - px - 44
            cv2.putText(c, "PINCH DISTANCE", (bar_x, bar_y-10),
                        cv2.FONT_HERSHEY_DUPLEX, 0.33, (60,60,70), 1, cv2.LINE_AA)
            cv2.rectangle(c, (bar_x, bar_y), (bar_x+bar_w, bar_y+6), (30,30,38), -1)
            fill = int(min(d / 0.25, 1.0) * bar_w)
            bar_col = (60,200,80) if d < PINCH_THRESHOLD else (80,80,100)
            cv2.rectangle(c, (bar_x, bar_y), (bar_x+fill, bar_y+6), bar_col, -1)

        sel = self.graph.selected_node
        if sel:
            label = self.graph.nodes[sel]["label"].replace("\n", " ")
            cv2.putText(c, "SELECTED:", (px+22, 644),
                        cv2.FONT_HERSHEY_DUPLEX, 0.34, (60,60,70), 1, cv2.LINE_AA)
            draw_text_ml(c, label, px+22, 663, (90, 230, 140), scale=0.36, line_height=17)

    def _draw_cursor(self, c):
        cur = self.ctrl.cursor
        if cur is None:
            return
        x, y = int(cur[0]), int(cur[1])
        pinching = self.ctrl.state in ("pinch", "drag")
        col = PINCH_COLOR[::-1] if pinching else CURSOR_COLOR[::-1]
        r   = 7 if pinching else 5
        cv2.line(c, (x-16, y), (x-r-3, y), col, 1, cv2.LINE_AA)
        cv2.line(c, (x+r+3, y), (x+16, y), col, 1, cv2.LINE_AA)
        cv2.line(c, (x, y-16), (x, y-r-3), col, 1, cv2.LINE_AA)
        cv2.line(c, (x, y+r+3), (x, y+16), col, 1, cv2.LINE_AA)
        cv2.circle(c, (x, y), r, col, 1, cv2.LINE_AA)
        if pinching:
            cv2.circle(c, (x, y), 2, col, -1)

    def _draw_hud(self, c):
        hand_present = self.ctrl.tracker.num_hands() > 0
        state_col = (90, 210, 90) if hand_present else (55, 55, 65)
        hand_txt  = "HAND DETECTED" if hand_present else "NO HAND"
        cv2.putText(c, self.ctrl.label, (14, self.H-30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.4, state_col[::-1], 1, cv2.LINE_AA)
        cv2.putText(c, hand_txt, (14, self.H-12),
                    cv2.FONT_HERSHEY_DUPLEX, 0.36, state_col[::-1], 1, cv2.LINE_AA)
        cv2.putText(c, "THOUGHT TOPOLOGY v1.0", (14, 22),
                    cv2.FONT_HERSHEY_DUPLEX, 0.36, (38, 38, 48), 1, cv2.LINE_AA)