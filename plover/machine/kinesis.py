# Copyright (c) 2010 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: add options to remap keys
# TODO: look into programmatically pasting into other applications

"For use with a Kinesis Advantage keyboard used as stenotype machine."

# TODO: Change name to NKRO Keyboard.

from plover.machine.base import StenotypeBase
from plover.oslayer import keyboardcontrol
from evdev import ecodes as e

KEYCODE_TO_STENO_KEY = {e.KEY_Q: "S-",
                        e.KEY_A: "S-",
                        e.KEY_W: "T-",
                        e.KEY_S: "K-",
                        e.KEY_E: "P-",
                        e.KEY_D: "W-",
                        e.KEY_R: "H-",
                        e.KEY_F: "R-",
                        e.KEY_V: "A-", # key V, should be 22 backspace
                        e.KEY_B: "O-", # key B, should be 119 delete
                        e.KEY_BACKSPACE: "A-", # 22 backspace
                        e.KEY_DELETE: "O-", # 119 delete
                        e.KEY_T: "*",
                        e.KEY_Y: "*",
                        e.KEY_G: "*",
                        e.KEY_H: "*",
                        e.KEY_N: "-E", # key N, should be 36 enter
                        e.KEY_M: "-U", # key M, should be 65 space
                        e.KEY_ENTER: "-E", # enter
                        e.KEY_SPACE: "-U", # space
                        e.KEY_U: "-F",
                        e.KEY_J: "-R",
                        e.KEY_I: "-P",
                        e.KEY_K: "-B",
                        e.KEY_O: "-L",
                        e.KEY_L: "-G",
                        e.KEY_P: "-T",
                        e.KEY_SEMICOLON: "-S",
                        e.KEY_BACKSLASH: "-D",
                        e.KEY_APOSTROPHE: "-Z",
                        e.KEY_0: "#",
                        e.KEY_1: "#",
                        e.KEY_2: "#",
                        e.KEY_3: "#",
                        e.KEY_4: "#",
                        e.KEY_5: "#",
                        e.KEY_6: "#",
                        e.KEY_7: "#",
                        e.KEY_8: "#",
                        e.KEY_9: "#",
                        e.KEY_MINUS: "#",
                        e.KEY_EQUAL: "#",
}


class Stenotype(StenotypeBase):
    """Standard stenotype interface for a Kinesis Advantage keyboard.

    This class implements the three methods necessary for a standard
    stenotype interface: start_capture, stop_capture, and
    add_callback.

    """

    def __init__(self, params):
        """Monitor a Kinesis Advantage keyboard via X events."""
        StenotypeBase.__init__(self)
        self._keyboard_emulation = keyboardcontrol.KeyboardEmulation()
        self._keyboard_capture = keyboardcontrol.KeyboardCapture()
        self._keyboard_capture.key_down = self._key_down
        self._keyboard_capture.key_up = self._key_up
        self.suppress_keyboard(True)
        self._down_keys = set()
        self._released_keys = set()
        self.arpeggiate = params['arpeggiate']

    def start_capture(self):
        """Begin listening for output from the stenotype machine."""
        self._keyboard_capture.start()
        self._ready()

    def stop_capture(self):
        """Stop listening for output from the stenotype machine."""
        self._keyboard_capture.cancel()
        self._stopped()

    def suppress_keyboard(self, suppress):
        self._is_keyboard_suppressed = suppress
        self._keyboard_capture.suppress_keyboard(suppress)

    def _key_down(self, event):
        """Called when a key is pressed."""
        if (self._is_keyboard_suppressed
            and event.keycode is not None
            and not self._keyboard_capture.is_keyboard_suppressed()):
            self._keyboard_emulation.send_backspaces(1)
        if event.keycode in KEYCODE_TO_STENO_KEY:
            self._down_keys.add(event.keycode)

    def _post_suppress(self, suppress, steno_keys):
        """Backspace the last stroke since it matched a command.
        
        The suppress function is passed in to prevent threading issues with the 
        gui.
        """
        n = len(steno_keys)
        if self.arpeggiate:
            n += 1
        suppress(n)

    def _key_up(self, event):
        """Called when a key is released."""
        if event.keycode in KEYCODE_TO_STENO_KEY:            
            # Process the newly released key.
            self._released_keys.add(event.keycode)
            # Remove invalid released keys.
            self._released_keys = self._released_keys.intersection(self._down_keys)

        # A stroke is complete if all pressed keys have been released.
        # If we are in arpeggiate mode then only send stroke when spacebar is pressed.
        send_strokes = bool(self._down_keys and 
                            self._down_keys == self._released_keys)
        # if self.arpeggiate:
        #     send_strokes &= event.keystring == ' '
        if send_strokes:
            steno_keys = [KEYCODE_TO_STENO_KEY[k] for k in self._down_keys
                          if k in KEYCODE_TO_STENO_KEY]
            if steno_keys:
                self._down_keys.clear()
                self._released_keys.clear()
                self._notify(steno_keys)

    @staticmethod
    def get_option_info():
        bool_converter = lambda s: s == 'True'
        return {
            'arpeggiate': (False, bool_converter),
        }
