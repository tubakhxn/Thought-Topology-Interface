# graph_engine.py — Node graph data, layouts, physics, particle system

import numpy as np
import math, random, time
from config import (
    NODES, EDGES, TOPOLOGIES, GRAPH_PANEL_W, WINDOW_HEIGHT,
    DRIFT_SPEED, DRIFT_AMPLITUDE, LERP_SPEED, PARTICLE_LIFE, PARTICLE_COUNT
)


# ── Particle ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y):
        angle  = random.uniform(0, 2 * math.pi)
        speed  = random.uniform(0.4, 1.8)
        self.x = x; self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life     = PARTICLE_LIFE
        self.max_life = PARTICLE_LIFE
        self.radius   = random.uniform(1.0, 2.5)

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vx  *= 0.95
        self.vy  *= 0.95
        self.life -= 1

    @property
    def alpha(self):
        return self.life / self.max_life

    @property
    def alive(self):
        return self.life > 0


# ── GraphEngine ───────────────────────────────────────────────────────────────
class GraphEngine:
    def __init__(self):
        self.nodes   = {n["id"]: dict(n) for n in NODES}
        self.edges   = list(EDGES)
        self.topo_idx     = 0
        self.topology     = TOPOLOGIES[0]

        self.target_pos   = {}   # layout target {id: (x,y)}
        self.current_pos  = {}   # smoothed current {id: (x,y)}
        self.drift_offset = {}   # per-node ambient drift phase

        self.selected_node = None
        self.hovered_node  = None
        self.dragging_node = None
        self.drag_offset   = (0, 0)

        self.particles     = []
        self.edge_phase    = 0.0   # for animated edge pulse
        self.t             = 0.0

        self._init_positions()

    # ── public API ────────────────────────────────────────────────────────────
    def next_topology(self):
        self.topo_idx  = (self.topo_idx + 1) % len(TOPOLOGIES)
        self.topology  = TOPOLOGIES[self.topo_idx]
        self._compute_layout()

    def set_topology(self, name):
        if name in TOPOLOGIES:
            self.topology = name
            self.topo_idx = TOPOLOGIES.index(name)
            self._compute_layout()

    def hover(self, cursor_px):
        best, best_d = None, 1e9
        for nid, (x, y) in self.current_pos.items():
            d = math.hypot(cursor_px[0] - x, cursor_px[1] - y)
            if d < best_d:
                best, best_d = nid, d
        from config import HOVER_RADIUS_PX
        self.hovered_node = best if best_d < HOVER_RADIUS_PX else None

    def select_hovered(self):
        if self.hovered_node:
            prev = self.selected_node
            self.selected_node = self.hovered_node
            if self.selected_node != prev:
                self._burst_particles(self.selected_node)
            return True
        return False

    def start_drag(self, cursor_px):
        if self.hovered_node:
            self.dragging_node = self.hovered_node
            cx, cy = self.current_pos[self.hovered_node]
            self.drag_offset = (cursor_px[0] - cx, cursor_px[1] - cy)

    def update_drag(self, cursor_px):
        if self.dragging_node:
            nx = cursor_px[0] - self.drag_offset[0]
            ny = cursor_px[1] - self.drag_offset[1]
            self.target_pos[self.dragging_node]  = (nx, ny)
            self.current_pos[self.dragging_node] = (nx, ny)

    def end_drag(self):
        self.dragging_node = None

    def reset_view(self):
        self.selected_node = None
        self._compute_layout()
        for nid in self.nodes:
            self._burst_particles(nid, count=2)

    def update(self, dt=1.0):
        self.t          += dt
        self.edge_phase += 0.02

        # smooth current → target
        for nid in self.nodes:
            if nid == self.dragging_node:
                continue
            tx, ty = self.target_pos[nid]
            cx, cy = self.current_pos[nid]
            # drift
            phase = self.drift_offset[nid]
            dx = math.sin(self.t * DRIFT_SPEED * 60 + phase)      * DRIFT_AMPLITUDE
            dy = math.cos(self.t * DRIFT_SPEED * 60 + phase + 1.3) * DRIFT_AMPLITUDE * 0.7
            dest_x = tx + dx
            dest_y = ty + dy
            self.current_pos[nid] = (
                cx + (dest_x - cx) * LERP_SPEED,
                cy + (dest_y - cy) * LERP_SPEED,
            )

        # particles
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

    def get_neighbours(self, nid):
        neighbours = set()
        for a, b in self.edges:
            if a == nid: neighbours.add(b)
            if b == nid: neighbours.add(a)
        return neighbours

    # ── layout computation ────────────────────────────────────────────────────
    def _init_positions(self):
        cx = GRAPH_PANEL_W // 2
        cy = WINDOW_HEIGHT // 2
        # Start all nodes at center so they animate out on first layout
        for nid in self.nodes:
            self.target_pos[nid]   = (cx, cy)
            self.current_pos[nid]  = (cx, cy)
            self.drift_offset[nid] = random.uniform(0, 2 * math.pi)
        self._compute_layout()

    def _compute_layout(self):
        cx = GRAPH_PANEL_W // 2
        cy = WINDOW_HEIGHT // 2
        ids = list(self.nodes.keys())
        non_core = [n for n in ids if n != "core"]

        if self.topology == "centralized":
            self.target_pos["core"] = (cx, cy)
            n = len(non_core)
            # Two rings for better spacing
            inner = [n for n in non_core if self.nodes[n]["cluster"] in (0, 2)]
            outer = [n for n in non_core if n not in inner]
            for i, nid in enumerate(inner):
                angle = 2 * math.pi * i / max(len(inner), 1) - math.pi / 2
                r = 160
                self.target_pos[nid] = (cx + math.cos(angle)*r, cy + math.sin(angle)*r)
            for i, nid in enumerate(outer):
                angle = 2 * math.pi * i / max(len(outer), 1) - math.pi / 3
                r = 270
                self.target_pos[nid] = (cx + math.cos(angle)*r, cy + math.sin(angle)*r)

        elif self.topology == "decentralized":
            clusters = {}
            for nid in ids:
                c = self.nodes[nid]["cluster"]
                clusters.setdefault(c, []).append(nid)
            hub_angles = [0, math.pi/2, math.pi, 3*math.pi/2]
            hub_r = 180
            for ci, (cid, members) in enumerate(clusters.items()):
                ha = hub_angles[ci % 4]
                hx = cx + math.cos(ha) * hub_r
                hy = cy + math.sin(ha) * hub_r
                for j, nid in enumerate(members):
                    a = 2 * math.pi * j / max(len(members), 1)
                    r = 90
                    self.target_pos[nid] = (hx + math.cos(a)*r, hy + math.sin(a)*r)

        elif self.topology == "hierarchical":
            levels = {"core": 0}
            visited = {"core"}
            queue = ["core"]
            while queue:
                cur = queue.pop(0)
                for nb in self.get_neighbours(cur):
                    if nb not in visited:
                        levels[nb] = levels[cur] + 1
                        visited.add(nb)
                        queue.append(nb)
            max_level = max(levels.values()) or 1
            level_members = {}
            for nid, lv in levels.items():
                level_members.setdefault(lv, []).append(nid)
            for lv, members in level_members.items():
                y = 80 + (WINDOW_HEIGHT - 120) * lv / max_level
                x_step = GRAPH_PANEL_W / (len(members) + 1)
                for j, nid in enumerate(members):
                    self.target_pos[nid] = (x_step * (j + 1), y)

        elif self.topology == "random":
            margin = 80
            for nid in ids:
                self.target_pos[nid] = (
                    random.randint(margin, GRAPH_PANEL_W - margin),
                    random.randint(margin, WINDOW_HEIGHT - margin),
                )

    def _burst_particles(self, nid, count=None):
        count = count or PARTICLE_COUNT
        if nid not in self.current_pos:
            return
        x, y = self.current_pos[nid]
        for _ in range(count):
            self.particles.append(Particle(x, y))