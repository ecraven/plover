#!/usr/bin/env python
# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.
#
# keyboardcontrol.py - capturing and injecting X keyboard events
#
# This code requires the X Window System with the 'record' extension
# and python-xlib 1.4 or greater.
#
# This code is based on the AutoKey and pyxhook programs, both of
# which use python-xlib.

"""Keyboard capture and control using evdev and uinput.

This module provides an interface for basic keyboard event capture and
emulation. Set the key_up and key_down functions of the
KeyboardCapture class to capture keyboard input. Call the send_string
and send_backspaces functions of the KeyboardEmulation class to
emulate keyboard input.

"""

import sys
import threading
from select import select
from evdev import UInput, InputDevice, list_devices, ecodes as e

keyboard_capture_instances = []

# CHAR_TO_CODE = { " ": e.KEY_SPACE, "a": e.KEY_A, "b": e.KEY_B, "c": e.KEY_C, "d": e.KEY_D, "e": e.KEY_E, "f": e.KEY_F, "g": e.KEY_G, "h": e.KEY_H, "i": e.KEY_I, "j": e.KEY_J, "k": e.KEY_K, "l": e.KEY_L, "m": e.KEY_M, "n": e.KEY_N, "o": e.KEY_O, "p": e.KEY_P, "q": e.KEY_Q, "r": e.KEY_R, "s": e.KEY_S, "t": e.KEY_T, "u": e.KEY_U, "v": e.KEY_V, "w": e.KEY_W, "x": e.KEY_X, "y": e.KEY_Y, "z": e.KEY_Z, "#": e.KEY_3,
# }

CHAR_TO_CODE = { " ": e.KEY_SPACE, "a": e.KEY_A, "b": e.KEY_N, "c": e.KEY_I, "d": e.KEY_H, "e": e.KEY_D, "f": e.KEY_Y, "g": e.KEY_U, "h": e.KEY_J, "i": e.KEY_G, "j": e.KEY_C, "k": e.KEY_V, "l": e.KEY_P, "m": e.KEY_M, "n": e.KEY_L, "o": e.KEY_S, "p": e.KEY_R, "q": e.KEY_X, "r": e.KEY_O, "s": e.KEY_SEMICOLON, "t": e.KEY_K, "u": e.KEY_F, "v": e.KEY_DOT, "w": e.KEY_COMMA, "x": e.KEY_B, "y": e.KEY_T, "z": e.KEY_SLASH, "#": e.KEY_3,
}

class KeyboardCapture(threading.Thread):
    """Listen to keyboard press and release events."""

    def __init__(self):
        """Prepare to listen for keyboard events."""

        self.devices = []
        for d in [InputDevice(dev) for dev in list_devices()]:
            caps = d.capabilities().get(1L)
            if caps and len(caps) > 26 and d.name != "py-evdev-uinput":
                self.devices.append(InputDevice(d.fn))
        threading.Thread.__init__(self)

        self._suppress_keyboard = False
        self.suppress_keyboard(True)

        # Assign default callback functions.
        self.key_down = lambda x: True
        self.key_up = lambda x: True

        
    def run(self):
        while self.alive:
            r,w,x = select(self.devices, [], [])
            for dev in r:
                for event in dev.read():
                    if event.type == e.EV_KEY:
                        keycode = event.code
                        key_event = KeyEvent(keycode)
                        if event.value == 1:
                            self.key_down(key_event)
                        elif event.value == 0:
                            self.key_up(key_event)
                
    def start(self):
        """Starts the thread after registering with a global list."""
        self.alive = True
        keyboard_capture_instances.append(self)
        threading.Thread.start(self)

    def cancel(self):
        """Stop listening for keyboard events."""
        self.alive = False
        if self in keyboard_capture_instances:
            keyboard_capture_instances.remove(self)

    def can_suppress_keyboard(self):
        return True

    def suppress_keyboard(self, suppress):
        if suppress and not self._suppress_keyboard:
            for dev in self.devices:
                dev.grab()
        if not suppress and self._suppress_keyboard:
            for dev in self.devices:
                dev.ungrab()
        self._suppress_keyboard = suppress

    def is_keyboard_suppressed(self):
        return self._suppress_keyboard

class KeyboardEmulation(object):
    """Emulate keyboard events."""

    def __init__(self):
        """Prepare to emulate keyboard events."""
        self.time = 0
        self.ui = UInput()
        
    def send_backspaces(self, number_of_backspaces):
        """Emulate the given number of backspaces.

        The emulated backspaces are not detected by KeyboardCapture.

        Argument:

        number_of_backspace -- The number of backspaces to emulate.

        """
        for x in xrange(number_of_backspaces):
            self._send_keycode(e.KEY_BACKSPACE)

    def send_string(self, s):
        """Emulate the given string.

        The emulated string is not detected by KeyboardCapture.

        Argument:

        s -- The string to emulate.

        """
        for char in s:
            keycode, modifiers = self._keysym_to_keycode_and_modifiers(char)
            if keycode is not None:
                self._send_keycode(keycode, modifiers)

    def send_key_combination(self, s):
        print "send key combination: " + s
        
    def _send_keycode(self, keycode, modifiers=0):
        """Emulate a key press and release.

        Arguments:

        keycode -- An integer in the inclusive range [8-255].

        modifiers -- An 8-bit bit mask indicating if the key pressed
        is modified by other keys, such as Shift, Capslock, Control,
        and Alt.

        """
        self.ui.write(e.EV_KEY, keycode, 1)
        self.ui.write(e.EV_KEY, keycode, 0)
        self.ui.write(e.EV_SYN, 0, 0)

    def _keysym_to_keycode_and_modifiers(self, keysym):
        """Return a keycode and modifier mask pair that result in the keysym.

        There is a one-to-many mapping from keysyms to keycode and
        modifiers pairs; this function returns one of the possibly
        many valid mappings, or the tuple (None, None) if no mapping
        exists.

        Arguments:

        keysym -- A key symbol.

        """
        return (CHAR_TO_CODE.get(keysym, None), None)

class KeyEvent(object):
    """A class to hold all the information about a key event."""

    def __init__(self, keycode):
        """Create an event instance.

        Arguments:

        keycode -- The keycode that identifies a physical key.
        """
        self.keycode = keycode

    def __str__(self):
        return ' '.join([('%s: %s' % (k, str(v)))
                                      for k, v in self.__dict__.items()])

if __name__ == '__main__':
    kc = KeyboardCapture()
    ke = KeyboardEmulation()

    import time

    def test(event):
        if not event.keycode:
            return
        print event
        time.sleep(0.1)
        keycode_events = ke.send_key_combination('Alt_L(Tab)')
        #ke.send_backspaces(5)
        #ke.send_string('Foo:~')

    #kc.key_down = test
    kc.key_up = test
    kc.start()
    print 'Press CTRL-c to quit.'
    try:
        while True:
            pass
    except KeyboardInterrupt:
        kc.cancel()
