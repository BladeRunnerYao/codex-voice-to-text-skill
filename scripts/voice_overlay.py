#!/usr/bin/env python3
from __future__ import annotations

import math
import queue
import sys
import threading
import time

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSScreenSaverWindowLevel,
    NSTimer,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorIgnoresCycle,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSObject


WIDTH = 460
HEIGHT = 74
BAR_COUNT = 44

levels: queue.Queue[float | None] = queue.Queue()


class WaveView(NSView):
    history = objc.ivar()
    phase = objc.ivar()

    def initWithFrame_(self, frame):
        self = objc.super(WaveView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.history = [0.08] * BAR_COUNT
        self.phase = 0
        return self

    def pushLevel_(self, value):
        self.history.append(max(0.0, min(1.0, float(value))))
        self.history = self.history[-BAR_COUNT:]
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        bg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.04, 0.06, 0.10, 0.90)
        active = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.22, 0.74, 0.97, 1.0)
        quiet = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.08, 0.32, 0.42, 1.0)
        bg.setFill()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(self.bounds(), 18, 18).fill()

        self.phase += 1
        pad_x = 24
        mid = HEIGHT / 2
        gap = 4
        bar_w = (WIDTH - pad_x * 2 - gap * (BAR_COUNT - 1)) / BAR_COUNT
        for i, raw in enumerate(self.history):
            pulse = 0.05 * math.sin((self.phase + i) * 0.35)
            value = max(0.06, raw * 2.9 + pulse)
            h = min(HEIGHT - 22, 8 + value * (HEIGHT - 24))
            x = pad_x + i * (bar_w + gap)
            y = mid - h / 2
            (active if raw > 0.025 else quiet).setFill()
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(x, y, max(2, bar_w), h), 2, 2
            )
            path.fill()


class Controller(NSObject):
    window = objc.ivar()
    view = objc.ivar()
    timer = objc.ivar()

    def applicationDidFinishLaunching_(self, notification):
        screen = NSScreen.mainScreen().visibleFrame()
        x = screen.origin.x + (screen.size.width - WIDTH) / 2
        y = screen.origin.y + 72
        frame = NSMakeRect(x, y, WIDTH, HEIGHT)

        self.window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(NSScreenSaverWindowLevel + 1)
        self.window.setIgnoresMouseEvents_(True)
        self.window.setHidesOnDeactivate_(False)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
            | NSWindowCollectionBehaviorStationary
        )

        self.view = WaveView.alloc().initWithFrame_(NSMakeRect(0, 0, WIDTH, HEIGHT))
        self.window.setContentView_(self.view)
        self.window.makeKeyAndOrderFront_(None)

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1 / 30, self, "tick:", None, True
        )

    def tick_(self, timer):
        closed = False
        while True:
            try:
                value = levels.get_nowait()
            except queue.Empty:
                break
            if value is None:
                closed = True
            else:
                self.view.pushLevel_(value)
        self.view.setNeedsDisplay_(True)
        if closed:
            NSApplication.sharedApplication().terminate_(None)


def stdin_reader() -> None:
    for line in sys.stdin:
        try:
            levels.put(float(line.strip()))
        except ValueError:
            pass
    levels.put(None)


def demo_feeder() -> None:
    deadline = time.monotonic() + 5
    i = 0
    while time.monotonic() < deadline:
        levels.put(0.03 + 0.22 * abs(math.sin(i / 5)))
        i += 1
        time.sleep(1 / 30)
    levels.put(None)


def main() -> None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = Controller.alloc().init()
    app.setDelegate_(controller)
    if "--demo" in sys.argv:
        threading.Thread(target=demo_feeder, daemon=True).start()
    else:
        threading.Thread(target=stdin_reader, daemon=True).start()
    app.run()


if __name__ == "__main__":
    main()
