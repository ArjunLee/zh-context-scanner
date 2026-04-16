"""
File: keyboard.py
Description: Cross-platform keyboard input handling for TUI navigation
Author: Arjun Li
Created: 2026-04-15
"""

from __future__ import annotations

import os
import sys

# Key constants - centralized keyboard mapping
KEY_UP = "UP"
KEY_DOWN = "DOWN"
KEY_LEFT = "LEFT"
KEY_RIGHT = "RIGHT"
KEY_ENTER = "ENTER"
KEY_QUIT = "QUIT"
KEY_BACK = "BACK"
KEY_ESC = "ESC"
KEY_SPACE = "SPACE"
KEY_TAB = "TAB"
KEY_OTHER = "OTHER"


def read_key() -> str:
    """Read a single keypress, cross-platform."""
    if os.name == "nt":
        return _read_key_windows()
    return _read_key_posix()


def _read_key_windows() -> str:
    """Windows keyboard input using msvcrt."""
    import msvcrt

    ch = msvcrt.getwch()
    if ch in ("\r", "\n"):
        return KEY_ENTER
    if ch in ("q", "Q"):
        return KEY_QUIT
    if ch == "\x1b":
        return KEY_ESC
    if ch == "\x08":
        return KEY_BACK
    if ch == " ":
        return KEY_SPACE
    if ch == "\t":
        return KEY_TAB
    if ch in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        if code == "H":
            return KEY_UP
        if code == "P":
            return KEY_DOWN
        if code == "K":
            return KEY_LEFT
        if code == "M":
            return KEY_RIGHT
    if ch.isprintable():
        return ch
    return KEY_OTHER


def _read_key_posix() -> str:
    """POSIX keyboard input using termios."""
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch in ("\r", "\n"):
            return KEY_ENTER
        if ch in ("q", "Q"):
            return KEY_QUIT
        if ch in ("\x7f", "\x08"):
            return KEY_BACK
        if ch == " ":
            return KEY_SPACE
        if ch == "\t":
            return KEY_TAB
        if ch == "\x1b":
            if select.select([sys.stdin], [], [], 0.03)[0]:
                seq = sys.stdin.read(1)
                if seq == "[" and select.select([sys.stdin], [], [], 0.03)[0]:
                    code = sys.stdin.read(1)
                    if code == "A":
                        return KEY_UP
                    if code == "B":
                        return KEY_DOWN
                    if code == "C":
                        return KEY_RIGHT
                    if code == "D":
                        return KEY_LEFT
            return KEY_ESC
        if ch.isprintable():
            return ch
        return KEY_OTHER
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
