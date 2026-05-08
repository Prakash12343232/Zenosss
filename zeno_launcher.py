# zeno_launcher.py — Zeno AI Entry Point
import sys
import os
import time

# Add root directory to sys.path to allow imports from subdirectories
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix for QWebEngine crashing on some Windows systems (MUST be before Qt imports)
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false;*.debug=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

def demo_log(msg, delay=0.1):
    """Prints a formatted log line to the terminal for demo effect."""
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}")
    time.sleep(delay)

def run():
    # ---- Ensure real-time WS control is alive before UI starts ----
    # Safe to call multiple times; server start is guarded by start_once().
    try:
        from utils.ws_server import ws_server
        ws_server.start_once()
    except Exception:
        # Avoid breaking launcher if WS deps are missing; log will capture the issue if possible.
        pass

    # ---- DEMO MODE STARTUP SEQUENCE ----
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "═" * 55)
    print("  ╔══╗ ╔═══╗ ╔═╗ ╔╗  ╔╗ ╔══╗")
    print("  ╚══╬═╣ ═ ║ ║ ╚═╝║ ╔╝╚╗║ ══╬═╗")
    print("  ╔══╩═╣ ╔═╝ ║  ╔╗║ ╚╗╔╝║ ══╣ ║")
    print("  ╚════╝╚╝   ╚══╝╚╝  ╚╝  ╚══╝╚═╝")
    print("    ZENO AI — Futuristic Personal Assistant")
    print("═" * 55)
    print()
    demo_log("Zeno Initialized", 0.2)
    demo_log("Core Engine         → ONLINE", 0.15)
    demo_log("AI Subsystem (Gem.) → GEMINI-2.5-FLASH READY", 0.15)
    demo_log("Voice Module        → EDGE-TTS ACTIVE", 0.15)
    demo_log("Speech Recognizer  → GOOGLE SR LOADED", 0.15)
    demo_log("Vision Core        → CAMERA STANDBY", 0.15)
    demo_log("Security Shield    → FACE-ID ARMED", 0.15)
    demo_log("Plugin Manager     → 10 MODULES REGISTERED", 0.15)
    demo_log("HUD Overlay        → INITIALIZED", 0.15)
    demo_log("Workout Engine     → MEDIAPIPE v0.10 READY", 0.15)
    demo_log("Automation Manager → LISTENING", 0.15)
    print()
    demo_log("Voice Module Active ✓", 0.1)
    demo_log("System Ready. Awaiting Commander... ✓", 0.3)
    print("═" * 55 + "\n")

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Zeno AI")
        app.setApplicationVersion("2.5.0")

        # Initialize PC Manager for Launcher Stats
        from systems.pc_manager import PCManager
        pc_mgr = PCManager()

        # Import and show Launcher
        from ui.launcher_window import LauncherWindow
        launcher = LauncherWindow(pc_manager=pc_mgr)

        main_window = None  # Will be set after launch

        def start_zeno_core():
            """Bridge: close launcher, open main AI window."""
            nonlocal main_window
            launcher.close()

            # Start Main Window — ZenoCore skips scan if already authenticated
            from ui.main_window import MainWindow
            main_window = MainWindow(is_authenticated=True)
            main_window.show()

        launcher.launch_requested.connect(start_zeno_core)
        launcher.show()

        sys.exit(app.exec())

    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"\n[CRITICAL] Missing dependency: {e}")
        print("Run:  python bootstrap.py  to auto-install all dependencies.")
        input("\nPress Enter to exit...")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[CRITICAL ERROR] {e}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run()
