"""Run with: python3 -m unittest discover -s tests -v.

GTK integration checks require PyGObject, GTK4, Libadwaita and a display.
Configuration checks also run without a display.
"""
import builtins
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "linsticky"))
from config import config_manager
from config.config_manager import ConfigManager

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
    builtins._ = lambda text: text
    from sticky.sticky_window import StickyWindow
    from views.settings_view import SettingsView


class TemporaryConfigTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config_path = Path(directory.name) / "config.json"
        paths = patch.multiple(config_manager, CONF_DIR=directory.name,
                               CONF_PATH=str(self.config_path))
        paths.start()
        self.addCleanup(paths.stop)


class OpacityConfigTests(TemporaryConfigTest):
    def test_existing_config_defaults_to_opaque(self):
        self.config_path.write_text('{"language": "en"}')
        self.assertEqual(ConfigManager.load()["note_opacity"], 1.0)

    def test_opacity_survives_save_and_reload(self):
        config = ConfigManager.load()
        config["note_opacity"] = 0.6
        ConfigManager.save(config)
        self.assertEqual(ConfigManager.load()["note_opacity"], 0.6)

    def test_invalid_and_out_of_range_opacity(self):
        for value, expected in [(None, 1.0), ("bad", 1.0), ([], 1.0),
                                (float("nan"), 1.0), (float("inf"), 1.0),
                                (-1, 0.2), (0, 0.2), (2, 1.0), ("0.5", 0.5)]:
            with self.subTest(value=value):
                self.config_path.write_text(json.dumps({"note_opacity": value}))
                self.assertEqual(ConfigManager.load()["note_opacity"], expected)


@unittest.skipUnless(HAS_DISPLAY, "GTK4/Libadwaita and a display are required")
class OpacityWindowTests(TemporaryConfigTest):
    def make_note(self, opacity=0.6):
        config = ConfigManager.get_defaults()
        config["note_opacity"] = opacity
        parent = SimpleNamespace(config=config, on_sticky_closed=lambda note_id: None)
        note = StickyWindow(db=None, main_window=parent)
        self.addCleanup(note._on_close_requested, note)
        return note

    def assert_opacity(self, note, expected):
        # GTK stores widget opacity with 8-bit precision.
        self.assertAlmostEqual(note.get_opacity(), expected, delta=1 / 255)

    def test_new_note_uses_saved_opacity(self):
        config = ConfigManager.load()
        config["note_opacity"] = 0.4
        ConfigManager.save(config)
        self.assert_opacity(self.make_note(ConfigManager.load()["note_opacity"]), 0.4)

    def test_hover_and_leave_only_affect_hovered_note(self):
        note = self.make_note()
        other_note = self.make_note()
        controller = note.motion_controller
        self.assertEqual(controller.get_propagation_phase(), Gtk.PropagationPhase.CAPTURE)
        with patch.object(controller, "contains_pointer", return_value=True):
            controller.notify("contains-pointer")
            self.assert_opacity(note, 1.0)
            self.assert_opacity(other_note, 0.6)
        controller.notify("contains-pointer")
        self.assert_opacity(note, 0.6)

    def test_settings_reload_preserves_hover_and_updates_leave_opacity(self):
        note = self.make_note()
        with patch.object(note.motion_controller, "contains_pointer", return_value=True):
            note.reload_config(dict(note.config, note_opacity=0.4))
            self.assert_opacity(note, 1.0)
        note.motion_controller.notify("contains-pointer")
        self.assert_opacity(note, 0.4)
        note.reload_config(dict(note.config, note_opacity=1.0))
        self.assert_opacity(note, 1.0)

    def test_settings_save_applies_without_restart_and_refreshes_control(self):
        note = self.make_note(1.0)
        settings = SettingsView(lambda: None,
                                lambda: note.reload_config(ConfigManager.load()))
        self.assertEqual(settings.opacity_spin.get_value(), 100)
        settings.opacity_spin.set_value(45)
        with patch.object(settings, "show_restart_dialog") as restart:
            settings.save_settings(None)
            restart.assert_not_called()
        self.assertEqual(ConfigManager.load()["note_opacity"], 0.45)
        self.assert_opacity(note, 0.45)
        settings.opacity_spin.set_value(100)
        settings.refresh_ui_from_config()
        self.assertEqual(settings.opacity_spin.get_value(), 45)


if __name__ == "__main__":
    unittest.main()
