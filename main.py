#!/usr/bin/env python3
# main.py — Thought Topology Interface  •  entry point

import cv2
import sys
import time
import threading
import platform
import numpy as np

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS_TARGET,
    WINDOW_TITLE, CAM_INDEX, CAM_WIDTH, CAM_HEIGHT,
    GRAPH_PANEL_W
)
from hand_tracking      import HandTracker
from graph_engine       import GraphEngine
from gesture_controller import GestureController
from renderer           import Renderer


def open_camera(index):
    if platform.system() == "Windows":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    return cap


def main():
    print("[INFO] Opening camera ...")
    cap = open_camera(CAM_INDEX)

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check CAM_INDEX in config.py.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)

    tracker    = HandTracker(max_hands=1)
    graph      = GraphEngine()
    controller = GestureController(tracker, graph, w=WINDOW_WIDTH, h=WINDOW_HEIGHT)
    renderer   = Renderer(graph, controller)

    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT)

    frame_time  = 1.0 / FPS_TARGET
    prev_t      = time.time()
    fps_display = 0.0

    print("=" * 55)
    print("  THOUGHT TOPOLOGY INTERFACE")
    print("  Controls:")
    print("    index finger  → pointer / hover")
    print("    pinch         → select node")
    print("    pinch + drag  → move node")
    print("    open hand     → reset view")
    print("    two fingers   → switch topology")
    print("    Q / ESC       → quit")
    print("=" * 55)

    cam_frame   = None
    cam_lock    = threading.Lock()
    cam_running = True

    def cam_reader():
        nonlocal cam_frame, cam_running
        while cam_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            with cam_lock:
                cam_frame = frame

    t = threading.Thread(target=cam_reader, daemon=True)
    t.start()

    # Wait up to 5 seconds for the first frame
    print("[INFO] Waiting for camera frame ...")
    wait_start = time.time()
    while True:
        with cam_lock:
            got_frame = cam_frame is not None
        if got_frame:
            break
        if time.time() - wait_start > 5.0:
            print("[WARNING] Camera timed out — running without video background.")
            break
        time.sleep(0.05)

    if cam_frame is not None:
        print("[INFO] Camera ready!")
    else:
        print("[WARNING] No camera frame received. Check your webcam.")

    while True:
        loop_start = time.time()

        with cam_lock:
            frame = cam_frame.copy() if cam_frame is not None else None

        if frame is not None:
            tracker.process(frame)

        controller.update()
        graph.update()

        canvas = renderer.render(webcam_frame=frame)

        now = time.time()
        dt  = now - prev_t
        prev_t = now
        fps_display = 0.9 * fps_display + 0.1 * (1.0 / max(dt, 1e-6))
        cv2.putText(canvas, f"{fps_display:.0f} fps",
                    (WINDOW_WIDTH - 80, WINDOW_HEIGHT - 14),
                    cv2.FONT_HERSHEY_DUPLEX, 0.35, (40, 40, 50), 1, cv2.LINE_AA)

        cv2.imshow(WINDOW_TITLE, canvas)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        if key == ord('r'):
            graph.reset_view()
        if key == ord('t'):
            graph.next_topology()

        elapsed = time.time() - loop_start
        sleep   = frame_time - elapsed
        if sleep > 0:
            time.sleep(sleep)

    cam_running = False
    cap.release()
    cv2.destroyAllWindows()
    print("Bye!")


if __name__ == "__main__":
    main()