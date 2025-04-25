import pygame
import sys
import time
from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent,
    CGEventPost,
    CGEventCreateScrollWheelEvent,
    kCGEventMouseMoved,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventLeftMouseDragged,
    kCGHIDEventTap,
    kCGScrollEventUnitLine
)

import pyautogui

# ==== CONFIG ====
FPS           = 60       # loop at display refresh
MAX_SPEED     = 700.0    # px/sec for cursor movement
SCROLL_SPEED  = 20.0    # scroll lines/sec
DEAD_ZONE     = 0.10     # ignore tiny stick deflections
DOUBLE_CLICK_THRESHOLD = 0.3  # seconds
# =====================

pyautogui.FAILSAFE = False

pygame.init()
pygame.joystick.init()

clock = pygame.time.Clock()
x_accum = y_accum = 0.0
scroll_v_accum = scroll_h_accum = 0.0

cmd_down = False
opt_down = False
left_dragging = False
controls_enabled = True

button_to_key = {
    2: 'tab',
    3: 'enter',
    4: 'q',
    11: 'up',
    12: 'down',
    13: 'left',
    14: 'right',
}

mouse_pos = list(pyautogui.position())
# Declare last_click_time before using it
last_click_time = 0.0


def get_joystick():
    pygame.joystick.quit()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        return None
    joy = pygame.joystick.Joystick(0)
    joy.init()
    print(f"Using joystick: {joy.get_name()}")
    return joy

joy = get_joystick()


def quartz_move(dx, dy):
    global mouse_pos, left_dragging
    if dx == 0 and dy == 0:
        return
    mouse_pos[0] += dx
    mouse_pos[1] += dy
    event_type = kCGEventLeftMouseDragged if left_dragging else kCGEventMouseMoved
    try:
        evt = CGEventCreateMouseEvent(None, event_type, tuple(mouse_pos), 0)
        CGEventPost(kCGHIDEventTap, evt)
    except Exception as e:
        print(f"Mouse move error: {e}")


def quartz_scroll_v(lines):
    try:
        evt = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, int(lines))
        CGEventPost(kCGHIDEventTap, evt)
    except Exception as e:
        print(f"Vertical scroll error: {e}")


def quartz_scroll_h(lines):
    try:
        evt = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 2, int(lines))
        CGEventPost(kCGHIDEventTap, evt)
    except Exception as e:
        print(f"Horizontal scroll error: {e}")


def quartz_mouse_down():
    try:
        evt = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, tuple(mouse_pos), 0)
        CGEventPost(kCGHIDEventTap, evt)
    except Exception as e:
        print(f"Mouse down error: {e}")


def quartz_mouse_up():
    try:
        evt = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, tuple(mouse_pos), 0)
        CGEventPost(kCGHIDEventTap, evt)
    except Exception as e:
        print(f"Mouse up error: {e}")


def quartz_double_click():
    quartz_mouse_down()
    quartz_mouse_up()
    time.sleep(0.01)
    quartz_mouse_down()
    quartz_mouse_up()


try:
    while True:
        dt = clock.tick(FPS) / 1000.0

        if not pygame.joystick.get_count():
            joy = None
        if joy is None:
            joy = get_joystick()
            if joy is None:
                continue

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                raise KeyboardInterrupt

            if evt.type == pygame.JOYBUTTONDOWN:
                b = evt.button
                if b == 15:
                    controls_enabled = not controls_enabled
                    print(f"Controls {'enabled' if controls_enabled else 'disabled'}")
                    continue

                if not controls_enabled:
                    continue

                if b == 9:
                    cmd_down = True
                elif b == 10:
                    opt_down = True
                elif b == 0:
                    now = time.time()
                    if now - last_click_time < DOUBLE_CLICK_THRESHOLD:
                        quartz_double_click()
                    else:
                        left_dragging = True
                        quartz_mouse_down()
                    last_click_time = now
                elif b == 1:
                    pyautogui.click(button='right')
                elif b in button_to_key:
                    key = button_to_key[b]
                    if cmd_down and opt_down:
                        pyautogui.hotkey('command', 'option', key)
                    elif cmd_down:
                        pyautogui.hotkey('command', key)
                    elif opt_down:
                        pyautogui.hotkey('option', key)
                    else:
                        pyautogui.press(key)

            elif evt.type == pygame.JOYBUTTONUP:
                if evt.button == 9:
                    cmd_down = False
                elif evt.button == 10:
                    opt_down = False
                elif evt.button == 0:
                    left_dragging = False
                    quartz_mouse_up()

        if not controls_enabled or joy is None:
            continue

        try:
            raw_x = joy.get_axis(0)
            raw_y = joy.get_axis(1)
            raw_sv = joy.get_axis(3)
            raw_sh = joy.get_axis(2)
        except pygame.error:
            joy = None
            continue

        raw_x = 0.0 if abs(raw_x) < DEAD_ZONE else raw_x
        raw_y = 0.0 if abs(raw_y) < DEAD_ZONE else raw_y
        raw_sv = 0.0 if abs(raw_sv) < DEAD_ZONE else raw_sv
        raw_sh = 0.0 if abs(raw_sh) < DEAD_ZONE else raw_sh

        x_accum += raw_x * MAX_SPEED * dt
        y_accum += raw_y * MAX_SPEED * dt
        move_x = int(x_accum)
        move_y = int(y_accum)
        x_accum -= move_x
        y_accum -= move_y

        quartz_move(move_x, move_y)

        scroll_v_accum += raw_sv * SCROLL_SPEED * dt
        scroll_v = int(scroll_v_accum)
        scroll_v_accum -= scroll_v
        if scroll_v:
            quartz_scroll_v(scroll_v)

        scroll_h_accum += raw_sh * SCROLL_SPEED * dt
        scroll_h = int(scroll_h_accum)
        scroll_h_accum -= scroll_h
        if scroll_h:
            quartz_scroll_h(scroll_h)

except KeyboardInterrupt:
    pass

finally:
    pygame.quit()
    sys.exit()
