# gesture_controller.py — Maps hand tracking states → graph actions

import math, time
from config import DRAG_MIN_DIST, PINCH_THRESHOLD


class GestureController:
    """
    State machine that reads hand_tracker & graph_engine each frame
    and fires high-level commands.
    """

    STATE_IDLE      = "idle"
    STATE_HOVER     = "hover"
    STATE_PINCH     = "pinch"
    STATE_DRAG      = "drag"
    STATE_OPEN      = "open"
    STATE_TWO_FINGER= "two_finger"

    def __init__(self, tracker, graph, w=1280, h=720):
        self.tracker = tracker
        self.graph   = graph
        self.W = w; self.H = h

        self.state          = self.STATE_IDLE
        self.cursor         = None      # (x,y) in display space
        self.prev_cursor    = None
        self.pinch_start    = None      # cursor at pinch-down
        self.drag_initiated = False
        self.last_two_finger_t = 0
        self.cooldown_two   = 0.8       # seconds between topology switches

        # gesture smoothing
        self._smooth_cursor = None
        self._alpha         = 0.35

    # ── public ────────────────────────────────────────────────────────────────
    def update(self):
        t = self.tracker

        if t.num_hands() == 0:
            self._handle_no_hand()
            return

        raw_cur = t.get_index_tip(frame_w=self.W, frame_h=self.H)
        if raw_cur is None:
            self._handle_no_hand()
            return

        # smooth cursor
        if self._smooth_cursor is None:
            self._smooth_cursor = raw_cur
        sx = self._smooth_cursor[0] + (raw_cur[0] - self._smooth_cursor[0]) * self._alpha
        sy = self._smooth_cursor[1] + (raw_cur[1] - self._smooth_cursor[1]) * self._alpha
        self._smooth_cursor = (sx, sy)
        self.cursor         = (int(sx), int(sy))

        pinching   = t.is_pinching(threshold=PINCH_THRESHOLD)
        open_hand  = t.is_open_hand()
        two_finger = t.is_two_fingers()

        # ── two-finger = switch topology ─────────────────────────────────────
        if two_finger and (time.time() - self.last_two_finger_t > self.cooldown_two):
            self.last_two_finger_t = time.time()
            self.graph.next_topology()
            self.state = self.STATE_TWO_FINGER
            return

        # ── open hand = reset ─────────────────────────────────────────────────
        if open_hand and self.state not in (self.STATE_DRAG,):
            if self.state != self.STATE_OPEN:
                self.graph.reset_view()
                self.state = self.STATE_OPEN
            return

        # ── pinch ─────────────────────────────────────────────────────────────
        if pinching:
            if self.state == self.STATE_IDLE or self.state == self.STATE_HOVER:
                self.pinch_start = self.cursor
                self.graph.select_hovered()
                self.graph.start_drag(self.cursor)
                self.state = self.STATE_PINCH
            elif self.state == self.STATE_PINCH:
                if self.pinch_start:
                    d = math.hypot(self.cursor[0] - self.pinch_start[0],
                                   self.cursor[1] - self.pinch_start[1])
                    if d > DRAG_MIN_DIST:
                        self.state = self.STATE_DRAG
                self.graph.update_drag(self.cursor)
            elif self.state == self.STATE_DRAG:
                self.graph.update_drag(self.cursor)
        else:
            # release
            if self.state in (self.STATE_PINCH, self.STATE_DRAG):
                self.graph.end_drag()
            # hover
            self.graph.hover(self.cursor)
            self.state = self.STATE_HOVER if self.graph.hovered_node else self.STATE_IDLE

    @property
    def label(self):
        return self.state.replace("_", " ").upper()

    # ── private ───────────────────────────────────────────────────────────────
    def _handle_no_hand(self):
        if self.state in (self.STATE_PINCH, self.STATE_DRAG):
            self.graph.end_drag()
        self.cursor = None
        self._smooth_cursor = None
        self.state  = self.STATE_IDLE
        self.graph.hovered_node = None