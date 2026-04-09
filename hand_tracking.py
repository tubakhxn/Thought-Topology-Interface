# hand_tracking.py — MediaPipe hand landmark detection & gesture state

import mediapipe as mp
import numpy as np
import math

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class HandTracker:
    """Wraps MediaPipe Hands; emits normalised & pixel landmark positions."""

    def __init__(self, max_hands=1, detection_conf=0.7, tracking_conf=0.6):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )
        self.results      = None
        self.landmarks_px = []   # list of dicts per hand
        self.landmarks_n  = []   # normalised [0-1]

    # ── public ────────────────────────────────────────────────────────────────
    def process(self, bgr_frame):
        """Process one BGR frame.  Call once per tick."""
        import cv2
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.hands.process(rgb)
        self._extract(bgr_frame.shape[1], bgr_frame.shape[0])

    def get_index_tip(self, hand_idx=0, frame_w=1280, frame_h=720, cam_w=640, cam_h=480):
        """Return (x,y) of index fingertip in display coords, or None."""
        if hand_idx >= len(self.landmarks_n):
            return None
        lm = self.landmarks_n[hand_idx]
        # mirror x (webcam is mirrored in the display)
        nx = 1.0 - lm[8]["x"]
        ny = lm[8]["y"]
        # map to graph panel (left 820 px of the 1280 window)
        x = int(nx * frame_w)
        y = int(ny * frame_h)
        return (x, y)

    def get_pinch_distance(self, hand_idx=0):
        """Normalised distance between thumb tip and index tip."""
        if hand_idx >= len(self.landmarks_n):
            return 1.0
        lm = self.landmarks_n[hand_idx]
        t, i = lm[4], lm[8]
        return math.hypot(t["x"] - i["x"], t["y"] - i["y"])

    def is_pinching(self, hand_idx=0, threshold=0.055):
        return self.get_pinch_distance(hand_idx) < threshold

    def is_open_hand(self, hand_idx=0):
        """All four fingers extended → open hand."""
        if hand_idx >= len(self.landmarks_n):
            return False
        lm = self.landmarks_n[hand_idx]
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        extended = sum(1 for t, p in zip(tips, pips) if lm[t]["y"] < lm[p]["y"])
        return extended >= 4

    def is_two_fingers(self, hand_idx=0):
        """Index + middle extended, ring + pinky folded."""
        if hand_idx >= len(self.landmarks_n):
            return False
        lm = self.landmarks_n[hand_idx]
        def ext(tip, pip): return lm[tip]["y"] < lm[pip]["y"]
        return ext(8,6) and ext(12,10) and not ext(16,14) and not ext(20,18)

    def num_hands(self):
        return len(self.landmarks_n)

    # ── private ───────────────────────────────────────────────────────────────
    def _extract(self, w, h):
        self.landmarks_px = []
        self.landmarks_n  = []
        if not self.results or not self.results.multi_hand_landmarks:
            return
        for hand_lm in self.results.multi_hand_landmarks:
            px_list = []
            n_list  = []
            for lm in hand_lm.landmark:
                px_list.append({"x": int(lm.x * w), "y": int(lm.y * h), "z": lm.z})
                n_list.append( {"x": lm.x,           "y": lm.y,          "z": lm.z})
            self.landmarks_px.append(px_list)
            self.landmarks_n.append(n_list)