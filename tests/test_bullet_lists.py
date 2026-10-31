"""Bullet editing regressions using the real GTK text buffer and key controller."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "linsticky"))

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import Adw, Gdk, Gtk
    Gtk.init()
    HAS_DISPLAY = Gdk.Display.get_default() is not None
except (ImportError, ValueError):
    HAS_DISPLAY = False

if HAS_DISPLAY:
    Adw.init()
    from config.config_manager import ConfigManager
    from sticky.sticky_window import StickyWindow


@unittest.skipUnless(HAS_DISPLAY, "GTK4/Libadwaita and a display are required")
class BulletListTests(unittest.TestCase):
    def setUp(self):
        self.parent = SimpleNamespace(
            config=ConfigManager.get_defaults(),
            update_card_text=Mock(),
            update_card_color_live=Mock(),
            on_sticky_closed=Mock(),
        )
        self.note = StickyWindow(db=None, main_window=self.parent)
        self.addCleanup(self.note._on_close_requested, self.note)
        self.buffer = self.note.buffer
        controllers = self.note.text_view.observe_controllers()
        self.controller = next(
            controller for controller in controllers
            if isinstance(controller, Gtk.EventControllerKey)
        )

    def set_text(self, text, offset=None):
        self.buffer.set_text(text)
        self.buffer.place_cursor(self.buffer.get_iter_at_offset(
            len(text) if offset is None else offset))

    def text(self):
        return self.buffer.get_text(*self.buffer.get_bounds(), True)

    def enter(self, key=None, state=0):
        return self.controller.emit("key-pressed", key or Gdk.KEY_Return, 0,
                                    Gdk.ModifierType(state))

    def test_toolbar_bullet_continues_after_typing(self):
        self.assertEqual(self.controller.get_propagation_phase(), Gtk.PropagationPhase.CAPTURE)
        self.note.toggle_bullet_list()
        self.buffer.insert_at_cursor("First item")
        self.assertTrue(self.enter())
        self.assertEqual(self.text(), " • First item\n • ")
        self.buffer.insert_at_cursor("Second item")
        self.assertEqual(self.text(), " • First item\n • Second item")
        self.assertEqual(self.parent.update_card_text.call_args.args[1],
                         self.note._get_buffer_segments())

    def test_keypad_enter_and_caps_lock_continue_bullets(self):
        for key, state in [(Gdk.KEY_KP_Enter, 0),
                           (Gdk.KEY_Return, Gdk.ModifierType.LOCK_MASK)]:
            with self.subTest(key=key, state=state):
                self.set_text(" • Item")
                self.assertTrue(self.enter(key, state))
                self.assertEqual(self.text(), " • Item\n • ")

    def test_empty_item_ends_list_without_adding_another_line(self):
        for suffix in ["", " \t"]:
            with self.subTest(suffix=suffix):
                self.set_text(" • First\n • " + suffix)
                self.assertTrue(self.enter())
                self.assertEqual(self.text(), " • First\n")
                self.assertFalse(self.enter())

    def test_empty_item_before_another_line_preserves_that_line(self):
        self.set_text(" • \nNext", 3)
        self.assertTrue(self.enter())
        self.assertEqual(self.text(), "\nNext")

    def test_enter_splits_item_at_cursor(self):
        self.set_text(" • First second\n • Third", len(" • First"))
        self.assertTrue(self.enter())
        self.assertEqual(self.text(), " • First\n •  second\n • Third")
        self.assertEqual(self.buffer.props.cursor_position, len(" • First\n • "))

    def test_enter_at_start_of_item_keeps_remaining_text(self):
        self.set_text(" • Item", 3)
        self.assertTrue(self.enter())
        self.assertEqual(self.text(), " • \n • Item")

    def test_plain_text_and_cursor_inside_marker_use_default_enter(self):
        for text, offset in [("Plain text", 10), ("Text • item", 11),
                             (" • Item", 0), (" • Item", 1), (" • Item", 2)]:
            with self.subTest(text=text, offset=offset):
                self.set_text(text, offset)
                self.assertFalse(self.enter())
                self.assertEqual(self.text(), text)

    def test_modified_enter_uses_default_behavior(self):
        for state in [Gdk.ModifierType.SHIFT_MASK, Gdk.ModifierType.CONTROL_MASK,
                      Gdk.ModifierType.ALT_MASK, Gdk.ModifierType.SUPER_MASK]:
            with self.subTest(state=state):
                self.set_text(" • Item")
                self.assertFalse(self.enter(state=state))
                self.assertEqual(self.text(), " • Item")

    def test_enter_replaces_selection_in_either_direction(self):
        for reverse in [False, True]:
            with self.subTest(reverse=reverse):
                self.set_text(" • First selected last")
                bounds = [self.buffer.get_iter_at_offset(len(" • First")),
                          self.buffer.get_iter_at_offset(len(" • First selected"))]
                self.buffer.select_range(*(bounds[::-1] if reverse else bounds))
                self.assertTrue(self.enter())
                self.assertEqual(self.text(), " • First\n •  last")

    def test_continuation_and_exit_each_undo_as_one_action(self):
        for text in [" • Item", " • Item\n • "]:
            with self.subTest(text=text):
                self.set_text(text)
                self.buffer.set_enable_undo(True)
                self.assertTrue(self.enter())
                changed = self.text()
                self.buffer.undo()
                self.assertEqual(self.text(), text)
                self.buffer.redo()
                self.assertEqual(self.text(), changed)
                self.buffer.set_enable_undo(False)

    def test_existing_formatting_and_saved_bullets_survive(self):
        self.set_text(" • First second")
        self.buffer.apply_tag_by_name("bold", *self.buffer.get_bounds())
        self.buffer.place_cursor(self.buffer.get_iter_at_offset(len(" • First")))
        self.assertTrue(self.enter())
        expected = self.note._get_buffer_segments()
        self.assertTrue(all("bold" in segment["tags"] for segment in expected))
        self.note.db = Mock()
        self.note.note_id = 1
        self.note.db.get.return_value = dict(
            content=json.dumps(expected).encode().hex(), color="#FFF59D",
            x=300, y=300, w=300, h=380)
        self.note.load_from_db()
        self.assertEqual(self.note._get_buffer_segments(), expected)
        self.buffer.place_cursor(self.buffer.get_end_iter())
        self.assertTrue(self.enter())
        self.assertEqual(self.text(), " • First\n •  second\n • ")


if __name__ == "__main__":
    unittest.main()
