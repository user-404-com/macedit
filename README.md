# macedit
MacEdit - a macOS-styled code editor written in Python (PyQt6)
================================================================

REQUIREMENTS
------------
- Python 3.9 or newer
- PyQt6  (pip install PyQt6)
- macOS is the main target. It also runs on Windows and Linux, with the
  menu bar shown inside the window and Ctrl in place of Cmd.

RUN
---
    pip install PyQt6
    python macedit.py                      (start empty)
    python macedit.py notes.py             (open a file)
    python macedit.py ~/Projects/myapp     (open a folder in the sidebar)

FEATURES
--------
Window
  - Frameless window with macOS traffic-light buttons
      red = close, yellow = minimise, green = zoom (Option+click = full screen)
  - Rounded corners, soft shadow, drag by title bar, resize from any edge
  - Double-click the title bar to zoom
  - Native macOS menu bar (global)
  - Dark and light themes (follows the system, toggle with the title-bar button)

Editing
  - Syntax highlighting: Python, JavaScript/TypeScript, C-family, JSON, HTML,
    CSS, Markdown, Shell (language can be changed in the status bar)
  - Line numbers, current-line highlight, bracket matching
  - Auto-closing brackets and quotes, smart indent, smart backspace
  - Multi-line indent / outdent, toggle comment, duplicate / delete / move lines
  - Find & Replace: match case, whole word, regex, live highlight of all matches
  - Command palette and Quick Open with fuzzy search
  - Zoom, word wrap, go to line
  - Tabs, folder sidebar, drag and drop, auto-save option
  - Session restore (open tabs, folder, theme, font size)
  - Encoding (UTF-8 / Latin-1) and line-ending (LF / CRLF) detection;
    the original line endings are kept when saving

KEYBOARD SHORTCUTS (use Ctrl instead of Cmd on Windows/Linux)
--------------------------------------------------------------
File
  Cmd+N            New file
  Cmd+O            Open file
  Cmd+Shift+O      Open folder
  Cmd+S            Save
  Cmd+Shift+S      Save as
  Cmd+Alt+S        Save all
  Cmd+W            Close tab
  Cmd+Q            Quit

Edit
  Cmd+Z / Cmd+Shift+Z   Undo / Redo
  Cmd+F            Find & Replace
  Cmd+G            Find next
  Cmd+Shift+G      Find previous
  Cmd+L            Go to line
  Cmd+/            Toggle comment
  Cmd+Shift+D      Duplicate line
  Cmd+Shift+K      Delete line
  Alt+Up / Alt+Down    Move line up / down
  Cmd+]  /  Cmd+[      Indent / outdent
  Tab / Shift+Tab      Indent / outdent selection

View
  Cmd+P            Quick Open (files in the open folder)
  Cmd+Shift+P      Command palette
  Cmd+B            Toggle sidebar
  Cmd+Shift+T      Toggle light / dark theme
  Alt+Z            Toggle word wrap
  Cmd+=  Cmd+-  Cmd+0   Zoom in / out / reset  (Cmd+scroll wheel also zooms)
  Ctrl+Cmd+F       Full screen  (F11 on Windows/Linux)
  Cmd+M            Minimise

PACKAGE AS A .app (optional)
----------------------------
    pip install pyinstaller
    pyinstaller --windowed --name MacEdit macedit.py
The app appears in the dist/ folder.

SETTINGS
--------
Settings are stored with QSettings under the name "MacEdit"
(on macOS: ~/Library/Preferences/com.MacEdit.MacEdit.plist).
Delete that file to reset the editor to its defaults.

TROUBLESHOOTING
---------------
- "No module named PyQt6": run  pip install PyQt6
- Fonts: the editor prefers SF Mono, then Menlo, Monaco, Consolas,
  DejaVu Sans Mono.
- Window will not resize or move on some Linux window managers: the editor
  relies on the system move/resize support in Qt 6.
- Very large files (over 30 MB) ask for confirmation before opening.
- Binary files are not opened.

KNOWN LIMITS
------------
- Syntax highlighting is regex based (fast, but not a full parser).
- Find positions can be off by a few characters in files that contain
  emoji or other characters outside the basic plane.
- No split view, minimap or integrated terminal yet.
