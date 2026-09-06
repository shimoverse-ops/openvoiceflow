"""OpenVoiceFlow — macOS GUI Onboarding Wizard.

A step-by-step setup experience:
  1. Welcome screen
  2. Choose LLM backend
  3. Enter API key (with link + instructions)
  4. Choose hotkey
  5. Test & Done

Uses tkinter (built into macOS Python — no extra dependencies).
"""

from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    tk = None

CONFIG_DIR = Path.home() / ".openvoiceflow"
CONFIG_PATH = CONFIG_DIR / "config.json"

# --- Color palette ---
BG = "#1a1a2e"
BG_CARD = "#16213e"
FG = "#e0e0e0"
FG_DIM = "#8888aa"
ACCENT = "#0f89ff"
ACCENT_HOVER = "#3da5ff"
SUCCESS = "#00c853"
WARN = "#ffab00"

# --- Backend definitions ---
BACKENDS = {
    "openrouter": {
        "name": "OpenRouter Gemma 4",
        "cost": "OpenRouter pricing/free tiers",
        "speed": "Fast",
        "privacy": "Cloud",
        "url": "https://openrouter.ai/keys",
        "instructions": [
            "1. Click the link below to open OpenRouter API Keys",
            "2. Sign in or create an OpenRouter account",
            "3. Create an API key",
            "4. Copy the key and paste it below",
        ],
        "recommended": True,
    },
    "groq": {
        "name": "Groq (Llama 3.3)",
        "cost": "Free tier (30 req/min)",
        "speed": "Fastest",
        "privacy": "Cloud",
        "url": "https://console.groq.com/keys",
        "instructions": [
            "1. Click the link below to open Groq Console",
            "2. Create a free account",
            "3. Go to API Keys → Create API Key",
            "4. Copy the key and paste it below",
        ],
        "recommended": False,
    },
    "openai": {
        "name": "OpenAI GPT-4o-mini",
        "cost": "~$5/year",
        "speed": "Fast",
        "privacy": "Cloud",
        "url": "https://platform.openai.com/api-keys",
        "instructions": [
            "1. Click the link below to open OpenAI Platform",
            "2. Sign in or create an account",
            "3. Go to API Keys → Create new secret key",
            "4. Copy the key and paste it below",
        ],
        "recommended": False,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "cost": "~$8/year",
        "speed": "Fast",
        "privacy": "Cloud",
        "url": "https://console.anthropic.com/",
        "instructions": [
            "1. Click the link below to open Anthropic Console",
            "2. Sign in or create an account",
            "3. Go to API Keys → Create Key",
            "4. Copy the key and paste it below",
        ],
        "recommended": False,
    },
    "ollama": {
        "name": "Ollama (Fully Local)",
        "cost": "No provider fee",
        "speed": "Moderate",
        "privacy": "100% Local — nothing leaves your Mac",
        "url": "https://ollama.com",
        "instructions": [
            "1. Click the link below to download Ollama",
            "2. Install and open Ollama",
            "3. Open Terminal and run: ollama pull llama3.2",
            "4. That's it — no API key needed!",
        ],
        "recommended": False,
        "no_key": True,
    },
}


class OnboardingWizard:
    """Step-by-step GUI setup wizard."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenVoiceFlow Setup")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Window size and centering
        w, h = 600, 520
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 3
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # State
        self.selected_backend = tk.StringVar(value="openrouter")
        self.api_key = tk.StringVar()
        self.selected_hotkey = tk.StringVar(value="right_cmd")
        self.config = {}
        # Which backend the prefilled key belongs to — so re-running the
        # wizard and picking a different backend can't silently save the
        # old backend's key under the new backend's field.
        self._prefill_key = ""
        self._prefill_backend = None

        # Load existing config
        self._load_existing_config()

        # Container
        self.container = tk.Frame(self.root, bg=BG)
        self.container.pack(fill="both", expand=True, padx=30, pady=20)

        # Start with welcome screen
        self.show_welcome()

    def _load_existing_config(self):
        """Load existing config if present."""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH) as f:
                    self.config = json.load(f)
                backend = self.config.get("llm_backend", "openrouter")
                if backend == "gemini":
                    backend = "openrouter"
                # "none" is a legal config value but has no wizard card —
                # selecting it verbatim left no radio checked and made
                # show_api_key/show_success crash with KeyError inside the
                # Tk callback (a Continue button that silently did nothing).
                if backend not in BACKENDS:
                    backend = "openrouter"
                self.selected_backend.set(backend)
                key_field = f"{backend}_api_key"
                if isinstance(self.config.get(key_field), str) and self.config[key_field]:
                    self.api_key.set(self.config[key_field])
                    self._prefill_key = self.config[key_field]
                    self._prefill_backend = backend
                if self.config.get("hotkey"):
                    self.selected_hotkey.set(self.config["hotkey"])
            except Exception:
                pass

    def _clear(self):
        """Clear the container."""
        for w in self.container.winfo_children():
            w.destroy()

    def _title(self, text, size=22):
        tk.Label(
            self.container, text=text, bg=BG, fg=FG,
            font=("SF Pro Display", size, "bold"),
        ).pack(pady=(0, 5))

    def _subtitle(self, text):
        tk.Label(
            self.container, text=text, bg=BG, fg=FG_DIM,
            font=("SF Pro Text", 13), wraplength=520,
        ).pack(pady=(0, 15))

    def _button(self, text, command, primary=True):
        btn = tk.Button(
            self.container, text=text, command=command,
            bg=ACCENT if primary else BG_CARD,
            fg="white", activebackground=ACCENT_HOVER,
            font=("SF Pro Text", 14, "bold" if primary else "normal"),
            relief="flat", cursor="hand2",
            padx=30, pady=10,
        )
        btn.pack(pady=8)
        return btn

    # ─── Step 1: Welcome ─────────────────────────

    def show_welcome(self):
        self._clear()

        tk.Label(
            self.container, text="🎙️", bg=BG,
            font=("Apple Color Emoji", 50),
        ).pack(pady=(20, 5))

        self._title("OpenVoiceFlow")
        self._subtitle(
            "Free for personal and qualifying noncommercial use on macOS.\n"
            "Hold a key → speak → release → clean text appears at your cursor."
        )

        tk.Label(
            self.container, bg=BG, fg=FG_DIM,
            font=("SF Pro Text", 12),
            text=(
                "✅  Local speech-to-text (your audio never leaves your Mac)\n"
                "✅  AI-powered cleanup (removes fillers, fixes grammar)\n"
                "✅  Works in any app — Slack, Gmail, Notion, everywhere\n"
                "✅  Costs ~$0-3/year vs $144/year for Wispr Flow"
            ),
            justify="left",
        ).pack(pady=15)

        self._button("Get Started →", self.show_backend_select)

    # ─── Step 2: Choose Backend ───────────────────

    def show_backend_select(self):
        self._clear()
        self._title("Choose Your AI Backend")
        self._subtitle("This powers the transcript cleanup. You can change it anytime.")

        # Scrollable frame for backend options
        for name, info in BACKENDS.items():
            frame = tk.Frame(self.container, bg=BG_CARD, cursor="hand2")
            frame.pack(fill="x", pady=3, ipady=8, ipadx=12)

            # Radio button
            rb = tk.Radiobutton(
                frame, variable=self.selected_backend, value=name,
                bg=BG_CARD, fg=FG, selectcolor=BG_CARD,
                activebackground=BG_CARD, activeforeground=FG,
                font=("SF Pro Text", 13, "bold"),
                text=f"  {info['name']}",
            )
            rb.pack(side="left", padx=(8, 0))

            # Badge
            badge_text = info["cost"]
            badge_color = SUCCESS if "Free" in info["cost"] or "$0" in info["cost"] else FG_DIM
            tk.Label(
                frame, text=badge_text, bg=BG_CARD, fg=badge_color,
                font=("SF Pro Text", 11),
            ).pack(side="right", padx=10)

            if info.get("recommended"):
                tk.Label(
                    frame, text="⭐ Recommended", bg=BG_CARD, fg=WARN,
                    font=("SF Pro Text", 10),
                ).pack(side="right", padx=5)

            # Make entire frame clickable
            frame.bind("<Button-1>", lambda e, n=name: self.selected_backend.set(n))

        tk.Frame(self.container, bg=BG, height=10).pack()
        self._button("Continue →", self.show_api_key)

    # ─── Step 3: API Key ─────────────────────────

    def show_api_key(self):
        self._clear()
        backend = self.selected_backend.get()
        info = BACKENDS[backend]

        # The key entry was prefilled from a different backend's stored key:
        # clear it. Leaving it in place looked configured (masked dots),
        # passed validation, and was then rightly refused by
        # save_and_finish's stale_prefill guard — yielding a "You're All
        # Set!" with no key actually saved.
        if (
            self._prefill_backend is not None
            and backend != self._prefill_backend
            and self.api_key.get() == self._prefill_key
        ):
            self.api_key.set("")

        if info.get("no_key"):
            self._show_ollama_setup(info)
            return

        self._title(f"Set Up {info['name']}")
        self._subtitle(f"Speed: {info['speed']}  •  Privacy: {info['privacy']}  •  Cost: {info['cost']}")

        # Instructions
        instr_frame = tk.Frame(self.container, bg=BG_CARD)
        instr_frame.pack(fill="x", pady=10, ipady=10, ipadx=15)

        for step in info["instructions"]:
            tk.Label(
                instr_frame, text=step, bg=BG_CARD, fg=FG,
                font=("SF Pro Text", 12), anchor="w",
            ).pack(anchor="w", padx=10, pady=1)

        # Link button
        link_btn = tk.Button(
            self.container, text=f"🔗  Open {info['url'].split('//')[1].split('/')[0]}",
            command=lambda: webbrowser.open(info["url"]),
            bg=BG_CARD, fg=ACCENT, activebackground=BG_CARD,
            font=("SF Pro Text", 12, "underline"),
            relief="flat", cursor="hand2",
        )
        link_btn.pack(pady=8)

        # API Key input
        tk.Label(
            self.container, text="Paste your API key:", bg=BG, fg=FG,
            font=("SF Pro Text", 12),
        ).pack(anchor="w", pady=(10, 3))

        key_entry = tk.Entry(
            self.container, textvariable=self.api_key,
            font=("SF Mono", 13), bg=BG_CARD, fg=FG,
            insertbackground=FG, relief="flat",
            show="•",
        )
        key_entry.pack(fill="x", ipady=8)
        key_entry.focus()

        # Show/hide toggle
        self._key_visible = False

        def toggle_visibility():
            self._key_visible = not self._key_visible
            key_entry.config(show="" if self._key_visible else "•")
            toggle_btn.config(text="🙈 Hide" if self._key_visible else "👁 Show")

        toggle_btn = tk.Button(
            self.container, text="👁 Show", command=toggle_visibility,
            bg=BG, fg=FG_DIM, relief="flat", font=("SF Pro Text", 10),
            cursor="hand2",
        )
        toggle_btn.pack(anchor="e")

        # Buttons
        btn_frame = tk.Frame(self.container, bg=BG)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="← Back", command=self.show_backend_select,
            bg=BG_CARD, fg=FG, relief="flat", font=("SF Pro Text", 13),
            padx=20, pady=8, cursor="hand2",
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Continue →", command=self.validate_and_continue,
            bg=ACCENT, fg="white", relief="flat", font=("SF Pro Text", 13, "bold"),
            padx=20, pady=8, cursor="hand2",
        ).pack(side="left", padx=5)

    def _show_ollama_setup(self, info):
        """Special setup screen for Ollama (no API key needed)."""
        self._title("Set Up Ollama")
        self._subtitle("Fully local — your data never leaves your Mac. No provider fee.")

        instr_frame = tk.Frame(self.container, bg=BG_CARD)
        instr_frame.pack(fill="x", pady=10, ipady=10, ipadx=15)

        for step in info["instructions"]:
            tk.Label(
                instr_frame, text=step, bg=BG_CARD, fg=FG,
                font=("SF Pro Text", 12), anchor="w",
            ).pack(anchor="w", padx=10, pady=2)

        link_btn = tk.Button(
            self.container, text="🔗  Download Ollama",
            command=lambda: webbrowser.open(info["url"]),
            bg=BG_CARD, fg=ACCENT, activebackground=BG_CARD,
            font=("SF Pro Text", 13, "underline"),
            relief="flat", cursor="hand2",
        )
        link_btn.pack(pady=15)

        btn_frame = tk.Frame(self.container, bg=BG)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="← Back", command=self.show_backend_select,
            bg=BG_CARD, fg=FG, relief="flat", font=("SF Pro Text", 13),
            padx=20, pady=8, cursor="hand2",
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Continue →", command=self.show_hotkey,
            bg=ACCENT, fg="white", relief="flat", font=("SF Pro Text", 13, "bold"),
            padx=20, pady=8, cursor="hand2",
        ).pack(side="left", padx=5)

    def validate_and_continue(self):
        """Validate API key and move to hotkey selection."""
        key = self.api_key.get().strip()
        if not key:
            messagebox.showwarning("API Key Required", "Please paste your API key to continue.")
            return
        if len(key) < 10:
            messagebox.showwarning("Invalid Key", "That doesn't look like a valid API key. Please try again.")
            return
        self.show_hotkey()

    # ─── Step 4: Hotkey ──────────────────────────

    def show_hotkey(self):
        self._clear()
        self._title("Choose Your Hotkey")
        self._subtitle("Hold this key to start dictating. Release to stop and paste.")

        # NB: fn / Globe is intentionally omitted — macOS doesn't expose that
        # key to apps, so it can't be used as a push-to-talk hotkey here.
        hotkeys = [
            ("right_cmd", "Right ⌘ Command", "Recommended — default hotkey"),
            ("right_alt", "Right ⌥ Option", "Good alternative"),
            ("left_alt", "Left ⌥ Option", "If right side is awkward"),
            ("right_ctrl", "Right ⌃ Control", "Another modifier option"),
            ("f5", "F5", "Traditional push-to-talk"),
            ("f6", "F6", "Alternative function key"),
        ]

        for value, label, desc in hotkeys:
            frame = tk.Frame(self.container, bg=BG_CARD, cursor="hand2")
            frame.pack(fill="x", pady=2, ipady=6, ipadx=12)

            rb = tk.Radiobutton(
                frame, variable=self.selected_hotkey, value=value,
                bg=BG_CARD, fg=FG, selectcolor=BG_CARD,
                activebackground=BG_CARD, activeforeground=FG,
                font=("SF Pro Text", 13, "bold"),
                text=f"  {label}",
            )
            rb.pack(side="left", padx=(8, 0))

            tk.Label(
                frame, text=desc, bg=BG_CARD, fg=FG_DIM,
                font=("SF Pro Text", 11),
            ).pack(side="right", padx=10)

            frame.bind("<Button-1>", lambda e, v=value: self.selected_hotkey.set(v))

        tk.Frame(self.container, bg=BG, height=15).pack()

        btn_frame = tk.Frame(self.container, bg=BG)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="← Back",
            command=self.show_api_key if self.selected_backend.get() != "ollama" else self.show_backend_select,
            bg=BG_CARD, fg=FG, relief="flat", font=("SF Pro Text", 13),
            padx=20, pady=8, cursor="hand2",
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Finish Setup ✓",
            command=self.save_and_finish,
            bg=SUCCESS, fg="white", relief="flat", font=("SF Pro Text", 14, "bold"),
            padx=25, pady=10, cursor="hand2",
        ).pack(side="left", padx=5)

    # ─── Save & Finish ───────────────────────────

    def save_and_finish(self):
        """Save config and show success screen."""
        backend = self.selected_backend.get()

        # Build config
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Preserve existing config (a corrupt file must not crash the
        # Finish button — fall back to a fresh config)
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH) as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, ValueError, OSError):
                self.config = {}

        self.config["llm_backend"] = backend
        self.config["hotkey"] = self.selected_hotkey.get()
        self.config.pop("gemini_api_key", None)

        # Save API key — but never a key prefilled from a *different*
        # backend (it would be saved under the wrong field and every
        # cleanup would 401), and never for keyless backends.
        key = self.api_key.get().strip()
        stale_prefill = (
            key == self._prefill_key and backend != self._prefill_backend
        )
        if key and backend not in ("ollama", "none") and not stale_prefill:
            key_field = f"{backend}_api_key"
            self.config[key_field] = key

        # Set defaults for missing fields
        # Backfill any missing keys from the canonical DEFAULTS rather than
        # hardcoding a parallel dict here (the v0.2 hardcoded copy was the
        # reason `log_transcripts` quietly stayed True for fresh wizard
        # users even after the DEFAULTS-level flip in v0.3).
        from .config import DEFAULTS as _CONFIG_DEFAULTS
        from .config import _migrate_streaming_default

        _migrate_streaming_default(self.config)
        for k, v in _CONFIG_DEFAULTS.items():
            if k not in self.config:
                self.config[k] = v

        from ._secure_io import secure_write_json
        try:
            secure_write_json(CONFIG_PATH, self.config)
        except OSError as exc:
            # Disk full / unwritable ~/.openvoiceflow — surface it instead
            # of letting the exception die inside the Tk callback (a Finish
            # button that silently does nothing).
            try:
                messagebox.showerror(
                    "OpenVoiceFlow Setup",
                    f"Could not save your settings:\n{exc}\n\n"
                    "Check that your home folder is writable and try again.",
                    parent=self.root,
                )
            except Exception:
                print(f"❌ Could not save config: {exc}", file=sys.stderr)
            return

        self.show_success()

    def show_success(self):
        """Show success screen."""
        self._clear()

        tk.Label(
            self.container, text="✅", bg=BG,
            font=("Apple Color Emoji", 50),
        ).pack(pady=(30, 5))

        self._title("You're All Set!")

        backend = self.selected_backend.get()
        hotkey = self.selected_hotkey.get()
        info = BACKENDS[backend]

        tk.Label(
            self.container, bg=BG, fg=FG,
            font=("SF Pro Text", 13),
            text=(
                f"Backend: {info['name']}\n"
                f"Hotkey: {hotkey}\n"
                f"Config: ~/.openvoiceflow/config.json"
            ),
            justify="center",
        ).pack(pady=15)

        tk.Label(
            self.container, bg=BG, fg=FG_DIM,
            font=("SF Pro Text", 12),
            text=(
                "How to use:\n"
                f"  Hold [{hotkey}] → Speak → Release → Text appears at cursor\n\n"
                "⚠️ Grant Accessibility permission when macOS prompts you"
            ),
            justify="center",
        ).pack(pady=10)

        # "Know Me" personalization step — strongly encouraged, skip is subtle
        self._button("Personalize OpenVoiceFlow ✨", self.launch_interview_then_close)

        # Small skip link for users who want to jump straight in
        skip_btn = tk.Button(
            self.container,
            text="Skip personalization",
            command=self.launch_and_close,
            bg=BG, fg=FG_DIM, activebackground=BG,
            font=("SF Pro Text", 11),
            relief="flat", cursor="hand2",
            borderwidth=0,
        )
        skip_btn.pack(pady=(2, 0))

    def launch_interview_then_close(self):
        """Close setup wizard and immediately open the Know Me interview."""
        self.root.destroy()
        # Run the personalization interview — it creates its own Tk window
        _launch_interview()

    def launch_and_close(self):
        """Close wizard and launch OpenVoiceFlow (no personalization)."""
        self.root.destroy()

    def run(self):
        """Start the wizard."""
        self.root.mainloop()
        return self.config


def _launch_interview() -> None:
    """Run the Know Me interview and surface any failure to the user.

    Previously wrapped in ``try/except: pass`` (SS6) which silently hid every
    error, so the flagship "Personalize OpenVoiceFlow ✨" button could
    no-op without the user knowing why. Now: print to stderr and, when
    tkinter is available, show an error dialog with a re-run hint.
    """
    import traceback

    try:
        from .interview import run_interview
        run_interview()
    except Exception as exc:
        print(f"❌ Personalization couldn't start: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if HAS_TKINTER:
            try:
                messagebox.showerror(
                    "Personalization couldn't start",
                    f"{exc}\n\n"
                    "You can re-run it any time with:\n"
                    "  openvoiceflow --profile",
                )
            except Exception:
                # If the error dialog itself fails, the stderr output above
                # is the user's diagnostic surface.
                pass


def run_onboarding():
    """Run the onboarding wizard and return the config."""
    if not HAS_TKINTER:
        print(
            "❌ tkinter not available. Configure from the terminal instead:\n"
            "   openvoiceflow --backend openrouter\n"
            "   openvoiceflow --set-key openrouter -   (key read from stdin)"
        )
        return None
    try:
        wizard = OnboardingWizard()
    except Exception as exc:
        # tk.Tk() raises TclError when no display is available (e.g. SSH)
        print(
            f"❌ Could not open the setup window ({exc}).\n"
            "   Configure from the terminal instead:\n"
            "   openvoiceflow --backend openrouter\n"
            "   openvoiceflow --set-key openrouter -   (key read from stdin)",
            file=sys.stderr,
        )
        return None
    return wizard.run()


def needs_onboarding() -> bool:
    """Check if onboarding is needed (no config or no API key)."""
    if not CONFIG_PATH.exists():
        return True
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        backend = config.get("llm_backend", "openrouter")
        if backend in ("ollama", "none"):
            return False
        key_field = f"{backend}_api_key"
        return not config.get(key_field)
    except Exception:
        return True


if __name__ == "__main__":
    config = run_onboarding()
    if config:
        print(f"✅ Setup complete! Config saved to {CONFIG_PATH}")
