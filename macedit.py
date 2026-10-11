#!/usr/bin/env python3
"""
MacEdit - a macOS-styled code editor written in Python (PyQt6)

    pip install PyQt6
    python macedit.py [files or folder ...]

Highlights
  * Frameless window with real macOS traffic-light buttons (close / minimise / zoom),
    rounded corners, soft shadow, native resize + drag, double-click title to zoom
  * Native macOS global menu bar (embedded menu bar on Windows/Linux)
  * Dark / Light themes (follows the system by default), Xcode-like syntax colours
  * Tabs, file-explorer sidebar, drag & drop, session restore, auto-save
  * Syntax highlighting: Python, JS/TS, C-family, JSON, HTML, CSS, Markdown, Shell
  * Line numbers, current-line + bracket matching, auto-pairing, smart indent
  * Find & Replace (case / whole word / regex, live match highlight)
  * Command palette (Cmd+Shift+P) and Quick Open (Cmd+P) with fuzzy search
  * Toggle comment, duplicate / move / delete line, indent / outdent, go to line,
    zoom (Cmd +/-/0 or Cmd+wheel), word wrap, CRLF/LF + encoding detection
"""
import os
import re
import sys

from PyQt6.QtCore import (QDir, QEvent, QPoint, QPointF, QRect, QRectF, QSettings,
                          QSize, Qt, QTimer, pyqtSignal)
from PyQt6.QtGui import (QAction, QColor, QFont, QGuiApplication, QKeySequence,
                         QFileSystemModel, QPainter, QPen, QPolygonF,
                         QSyntaxHighlighter, QTextCharFormat, QTextCursor,
                         QTextFormat)
from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog, QFrame,
                             QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMenuBar, QMessageBox,
                             QPlainTextEdit, QPushButton, QSplitter, QStackedWidget,
                             QTabBar, QTabWidget, QTextEdit, QToolButton, QTreeView,
                             QVBoxLayout, QWidget)

APP = "MacEdit"
MAC = sys.platform == "darwin"
CMD = "\u2318" if MAC else "Ctrl+"
SHIFT = "\u21e7" if MAC else "Shift+"
INDENT = "    "
MARGIN = 8  # transparent margin around the window (shadow + resize border)

# --------------------------------------------------------------------------- #
#  Themes
# --------------------------------------------------------------------------- #
THEMES = {
    "dark": dict(
        bg="#1c1c1e", title="#2b2b2e", side="#242426", fg="#e5e5e7", muted="#98989d",
        accent="#0a84ff", border="#38383a", hover="rgba(255,255,255,24)",
        scroll="rgba(255,255,255,70)", sel="#3e5c8a", line="#2a2a2d", inactive="#4a4a4d",
        syntax=dict(keyword="#fc5fa3", builtin="#41a1c0", string="#fc6a5d", number="#d0bf69",
                    comment="#6c7986", func="#67b7a4", klass="#5dd8ff", decorator="#fd8f3f",
                    self="#d0a8ff"),
    ),
    "light": dict(
        bg="#ffffff", title="#ececed", side="#f4f4f5", fg="#1d1d1f", muted="#86868b",
        accent="#007aff", border="#d1d1d6", hover="rgba(0,0,0,18)",
        scroll="rgba(0,0,0,70)", sel="#b3d7ff", line="#f0f4fa", inactive="#cfcfd1",
        syntax=dict(keyword="#ad3da4", builtin="#3e8087", string="#d12f1b", number="#272ad8",
                    comment="#707f8c", func="#326d74", klass="#1c464a", decorator="#78492a",
                    self="#703daa"),
    ),
}

QSS = """
#container{background:@bg;border:1px solid @border;border-radius:@radpx;}
#titlebar{background:@title;border-top-left-radius:@radpx;border-top-right-radius:@radpx;
          border-bottom:1px solid @border;}
#titlelabel{color:@muted;font-size:13px;font-weight:600;}
#statusbar{background:@title;border-top:1px solid @border;
           border-bottom-left-radius:@radpx;border-bottom-right-radius:@radpx;}
#statusbar QLabel{color:@muted;font-size:11px;}
#statusbar QComboBox{background:transparent;color:@muted;border:none;padding:0 6px;font-size:11px;}
#statusbar QComboBox::drop-down{width:0;border:none;}
QComboBox QAbstractItemView{background:@title;color:@fg;selection-background-color:@accent;
                            border:1px solid @border;outline:0;}
#sidebar{background:@side;border-right:1px solid @border;}
#sidehead{color:@muted;font-size:11px;font-weight:700;padding:10px 12px 4px 12px;}
#welcome{background:@bg;}
#welcome QLabel{color:@muted;font-size:13px;}
#welcome #wtitle{color:@fg;font-size:34px;font-weight:700;}
QTreeView{background:@side;border:none;color:@fg;outline:0;font-size:13px;}
QTreeView::item{padding:3px 2px;border-radius:5px;}
QTreeView::item:selected{background:@accent;color:white;}
QTreeView::item:hover:!selected{background:@hover;}
QSplitter::handle{background:@border;}
QTabWidget::pane{border:none;}
QTabWidget::tab-bar{left:0;}
QTabBar{background:@title;qproperty-drawBase:0;}
QTabBar::tab{background:@title;color:@muted;padding:7px 8px 7px 14px;border-right:1px solid @border;
             min-width:90px;font-size:12px;}
QTabBar::tab:selected{background:@bg;color:@fg;}
QTabBar::tab:hover:!selected{background:@hover;}
QToolButton{color:@muted;border:none;border-radius:5px;padding:3px 7px;background:transparent;}
QToolButton:hover{background:@hover;}
QToolButton:checked{background:@accent;color:white;}
QLineEdit{background:@bg;color:@fg;border:1px solid @border;border-radius:6px;padding:4px 9px;
          selection-background-color:@accent;selection-color:white;}
QLineEdit:focus{border:1px solid @accent;}
QPushButton{background:@hover;color:@fg;border:1px solid @border;border-radius:6px;padding:4px 12px;}
QPushButton:hover{border:1px solid @accent;}
QPushButton:default{background:@accent;color:white;border:none;}
#findbar{background:@title;border-bottom:1px solid @border;}
#findbar QLabel{color:@muted;font-size:11px;}
#palette{background:@title;border:1px solid @border;border-radius:10px;}
#palette QLineEdit{font-size:15px;padding:7px 10px;}
QListWidget{background:transparent;border:none;color:@fg;outline:0;font-size:13px;}
QListWidget::item{padding:6px 10px;border-radius:6px;}
QListWidget::item:selected{background:@accent;color:white;}
QDialog,QMessageBox,QInputDialog{background:@title;}
QDialog QLabel,QMessageBox QLabel{color:@fg;}
QMenuBar{background:@title;color:@fg;}
QMenuBar::item:selected{background:@hover;}
QMenu{background:@title;color:@fg;border:1px solid @border;padding:4px;}
QMenu::item{padding:5px 22px;border-radius:4px;}
QMenu::item:selected{background:@accent;color:white;}
QScrollBar:vertical{background:transparent;width:12px;margin:0;}
QScrollBar::handle:vertical{background:@scroll;border-radius:3px;min-height:30px;margin:2px 2px 2px 3px;}
QScrollBar:horizontal{background:transparent;height:12px;margin:0;}
QScrollBar::handle:horizontal{background:@scroll;border-radius:3px;min-width:30px;margin:3px 2px 2px 2px;}
QScrollBar::add-line,QScrollBar::sub-line{height:0;width:0;}
QScrollBar::add-page,QScrollBar::sub-page{background:none;}
"""


def build_qss(theme, radius):
    tokens = {k: v for k, v in THEMES[theme].items() if isinstance(v, str)}
    tokens["rad"] = str(radius)
    out = QSS
    for k in sorted(tokens, key=len, reverse=True):
        out = out.replace("@" + k, tokens[k])
    return out


# --------------------------------------------------------------------------- #
#  Languages & syntax highlighting
# --------------------------------------------------------------------------- #
def kw(words):
    return r"\b(?:" + "|".join(words.split()) + r")\b"


PY_KW = ("and as assert async await break class continue def del elif else except finally for "
         "from global if import in is lambda nonlocal not or pass raise return try while with "
         "yield match case None True False")
PY_BUILTINS = ("print len range int str float list dict set tuple bool type isinstance super open "
               "enumerate zip map filter sorted reversed sum min max abs any all input id iter next "
               "repr round hasattr getattr setattr callable format vars dir object property "
               "staticmethod classmethod Exception ValueError TypeError KeyError IndexError "
               "RuntimeError OSError")
JS_KW = ("break case catch class const continue debugger default delete do else export extends "
         "finally for function if import in instanceof let new of return static super switch this "
         "throw try typeof var void while with yield async await true false null undefined from "
         "as type interface enum implements public private protected readonly")
C_KW = ("auto break case catch char class const continue default delete do double else enum extern "
        "false final float for fn func go goto if impl import in include inline int interface let "
        "long match mod mut namespace new nil null override package private protected pub public "
        "return self short signed sizeof static struct super switch template this throw throws "
        "trait true try typedef typeof union unsigned use using var virtual void volatile where "
        "while")
SH_KW = ("if then else elif fi for while do done case esac function in return export local echo cd "
         "exit source alias unset set read test")

NUM = r"\b(?:0[xX][0-9a-fA-F_]+|\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?)\b"
DQ = r'"(?:[^"\\\n]|\\.)*"'
SQ = r"'(?:[^'\\\n]|\\.)*'"
BQ = r"`(?:[^`\\]|\\.)*`"
CALL = r"\b[A-Za-z_]\w*(?=\()"
CLASSY = r"\b[A-Z][A-Za-z0-9_]*\b"

LANG_SPECS = {
    "Python": dict(
        rules=[(CALL, "func"), (kw(PY_KW), "keyword"), (kw(PY_BUILTINS), "builtin"),
               (r"\b(?:self|cls)\b", "self"), (NUM, "number"), (r"@\w[\w.]*", "decorator"),
               (r"(?<=def )\w+", "func"), (r"(?<=class )\w+", "klass"),
               (r"[rbfuRBFU]{0,2}" + DQ, "string"), (r"[rbfuRBFU]{0,2}" + SQ, "string"),
               (r"#.*", "comment")],
        multi=[(r'[rbfuRBFU]{0,2}"""', r'"""', "string"), (r"[rbfuRBFU]{0,2}'''", r"'''", "string")]),
    "JavaScript": dict(
        rules=[(CALL, "func"), (CLASSY, "klass"), (kw(JS_KW), "keyword"), (NUM, "number"),
               (DQ, "string"), (SQ, "string"), (BQ, "string"), (r"//.*", "comment")],
        multi=[(r"/\*", r"\*/", "comment")]),
    "C-Family": dict(
        rules=[(CALL, "func"), (CLASSY, "klass"), (kw(C_KW), "keyword"), (NUM, "number"),
               (r"^\s*#\s*\w+", "decorator"), (DQ, "string"), (SQ, "string"), (r"//.*", "comment")],
        multi=[(r"/\*", r"\*/", "comment")]),
    "JSON": dict(
        rules=[(r"-?\b\d+\.?\d*(?:[eE][+-]?\d+)?\b", "number"), (r"\b(?:true|false|null)\b", "keyword"),
               (DQ, "string"), (r'"(?:[^"\\]|\\.)*"(?=\s*:)', "func")], multi=[]),
    "HTML": dict(
        rules=[(r"&\w+;", "number"), (r"</?[A-Za-z][\w:-]*", "keyword"), (r"/?>", "keyword"),
               (r"\b[\w:-]+(?==)", "builtin"), (DQ, "string"), (SQ, "string")],
        multi=[(r"<!--", r"-->", "comment")]),
    "CSS": dict(
        rules=[(r"[.#][A-Za-z_-][\w-]*", "klass"), (r"[\w-]+(?=\s*:)", "builtin"), (r"@[\w-]+", "keyword"),
               (r"-?\d*\.?\d+(?:px|em|rem|%|vh|vw|s|ms|deg)?", "number"), (r"#[0-9a-fA-F]{3,8}\b", "number"),
               (DQ, "string"), (SQ, "string")],
        multi=[(r"/\*", r"\*/", "comment")]),
    "Markdown": dict(
        rules=[(r"^\s*(?:[-*+]|\d+\.)\s", "number"), (r"^>.*", "comment"), (r"\[[^\]\n]+\]\([^)\n]+\)", "func"),
               (r"\*\*[^*\n]+\*\*", "bold"), (r"(?<!\*)\*[^*\n]+\*(?!\*)", "italic"),
               (r"`[^`\n]+`", "string"), (r"^#{1,6}\s.*", "heading")],
        multi=[(r"^```", r"^```", "string")]),
    "Shell": dict(
        rules=[(kw(SH_KW), "keyword"), (r"\$\{?\w+\}?", "builtin"), (NUM, "number"),
               (DQ, "string"), (SQ, "string"), (r"(?:^|\s)#.*", "comment")], multi=[]),
    "Plain Text": dict(rules=[], multi=[]),
}
LANG_NAMES = list(LANG_SPECS)
COMMENT_PREFIX = {"Python": "#", "Shell": "#", "JavaScript": "//", "C-Family": "//"}
EXT = {
    ".py": "Python", ".pyw": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "JavaScript", ".tsx": "JavaScript", ".c": "C-Family", ".h": "C-Family", ".cpp": "C-Family",
    ".hpp": "C-Family", ".cc": "C-Family", ".java": "C-Family", ".swift": "C-Family", ".go": "C-Family",
    ".rs": "C-Family", ".kt": "C-Family", ".cs": "C-Family", ".json": "JSON", ".html": "HTML",
    ".htm": "HTML", ".xml": "HTML", ".svg": "HTML", ".css": "CSS", ".scss": "CSS", ".md": "Markdown",
    ".markdown": "Markdown", ".sh": "Shell", ".zsh": "Shell", ".bash": "Shell",
}
_COMPILED = {}


def compiled_spec(lang):
    if lang not in _COMPILED:
        spec = LANG_SPECS.get(lang, LANG_SPECS["Plain Text"])
        flags = re.M
        _COMPILED[lang] = (
            [(re.compile(p, flags), role) for p, role in spec["rules"]],
            [(re.compile(s, flags), re.compile(e, flags), role) for s, e, role in spec["multi"]],
        )
    return _COMPILED[lang]


def detect_language(path, text=""):
    if path:
        ext = os.path.splitext(path)[1].lower()
        if ext in EXT:
            return EXT[ext]
        if os.path.basename(path) in ("Makefile", "Dockerfile"):
            return "Shell"
    if text.startswith("#!"):
        first = text.split("\n", 1)[0]
        if "python" in first:
            return "Python"
        if "node" in first:
            return "JavaScript"
        if "sh" in first:
            return "Shell"
    return "Plain Text"


class Highlighter(QSyntaxHighlighter):
    def __init__(self, doc, lang, theme):
        super().__init__(doc)
        self.configure(lang, theme)

    def configure(self, lang, theme):
        self.lang, self.theme = lang, theme
        self.rules, self.multi = compiled_spec(lang)
        t = THEMES[theme]
        syn = t["syntax"]

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            return f

        self.fmt = {r: fmt(c) for r, c in syn.items()}
        self.fmt["comment"] = fmt(syn["comment"], italic=True)
        self.fmt["heading"] = fmt(syn["keyword"], bold=True)
        self.fmt["bold"] = fmt(t["fg"], bold=True)
        self.fmt["italic"] = fmt(t["fg"], italic=True)
        self.rehighlight()

    def highlightBlock(self, text):
        for rx, role in self.rules:
            f = self.fmt[role]
            for m in rx.finditer(text):
                if m.end() > m.start():
                    self.setFormat(m.start(), m.end() - m.start(), f)
        self._multiline(text)

    def _multiline(self, text):
        self.setCurrentBlockState(0)
        prev = self.previousBlockState()
        for i, (sx, ex, role) in enumerate(self.multi, 1):
            if prev > 0 and prev != i:
                continue
            f = self.fmt[role]
            if prev == i:
                start, off = 0, 0
            else:
                m = sx.search(text)
                if not m:
                    continue
                start, off = m.start(), m.end() - m.start()
            while True:
                em = ex.search(text, start + off)
                if em:
                    self.setFormat(start, em.end() - start, f)
                    m = sx.search(text, em.end())
                    if not m:
                        break
                    start, off = m.start(), m.end() - m.start()
                else:
                    self.setCurrentBlockState(i)
                    self.setFormat(start, len(text) - start, f)
                    break
            if self.currentBlockState() == i or prev > 0:
                break


# --------------------------------------------------------------------------- #
#  The code editor widget
# --------------------------------------------------------------------------- #
AUTO = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
CLOSERS = set(")]}\"'`")
QUOTES = set("\"'`")
OPEN_BR = {"(": ")", "[": "]", "{": "}"}
CLOSE_BR = {v: k for k, v in OPEN_BR.items()}


class LineNumberArea(QWidget):
    def __init__(self, ed):
        super().__init__(ed)
        self.ed = ed

    def sizeHint(self):
        return QSize(self.ed.line_number_width(), 0)

    def paintEvent(self, e):
        self.ed.paint_line_numbers(e)


class CodeEditor(QPlainTextEdit):
    zoomRequested = pyqtSignal(int)

    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.path = None
        self.untitled_name = "Untitled"
        self.lang = "Plain Text"
        self.encoding = "utf-8"
        self.eol = "\n"
        self.highlighter = None
        self.search_sel = []
        self.line_area = LineNumberArea(self)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursorWidth(2)
        self.document().setDocumentMargin(10)
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.update_extras)
        self.set_font_size(13)
        self.update_margin()
        self.apply_theme(theme)

    # ---- appearance ------------------------------------------------------ #
    def apply_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.setStyleSheet(
            "QPlainTextEdit{background:%s;color:%s;border:none;selection-background-color:%s;"
            "selection-color:%s;}" % (t["bg"], t["fg"], t["sel"], t["fg"]))
        if self.highlighter:
            self.highlighter.configure(self.lang, theme)
        self.update_extras()
        self.line_area.update()

    def set_font_size(self, size):
        f = QFont()
        f.setFamilies(["SF Mono", "Menlo", "Monaco", "Consolas", "DejaVu Sans Mono", "Courier New"])
        f.setStyleHint(QFont.StyleHint.Monospace)
        f.setFixedPitch(True)
        f.setPointSize(size)
        self.setFont(f)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.update_margin()

    def set_wrap(self, on):
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if on
                             else QPlainTextEdit.LineWrapMode.NoWrap)

    def set_language(self, lang):
        self.lang = lang
        if self.highlighter is None:
            self.highlighter = Highlighter(self.document(), lang, self.theme)
        else:
            self.highlighter.configure(lang, self.theme)

    def display_name(self):
        return os.path.basename(self.path) if self.path else self.untitled_name

    # ---- line numbers ---------------------------------------------------- #
    def line_number_width(self):
        digits = max(3, len(str(self.blockCount())))
        return 18 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_margin(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_margin()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def paint_line_numbers(self, e):
        t = THEMES[self.theme]
        p = QPainter(self.line_area)
        p.fillRect(e.rect(), QColor(t["bg"]))
        p.setFont(self.font())
        block = self.firstVisibleBlock()
        n = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        cur = self.textCursor().blockNumber()
        h = self.fontMetrics().height()
        while block.isValid() and top <= e.rect().bottom():
            if block.isVisible() and bottom >= e.rect().top():
                p.setPen(QColor(t["fg"] if n == cur else t["muted"]))
                p.drawText(0, top, self.line_area.width() - 10, h,
                           Qt.AlignmentFlag.AlignRight, str(n + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            n += 1

    # ---- extra selections: current line, brackets, search ---------------- #
    def set_search(self, ranges):
        sels = []
        for s, e in ranges[:1500]:
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(255, 204, 0, 90))
            c = QTextCursor(self.document())
            c.setPosition(s)
            c.setPosition(e, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = c
            sels.append(sel)
        self.search_sel = sels
        self.update_extras()

    def update_extras(self):
        t = THEMES[self.theme]
        sels = []
        s = QTextEdit.ExtraSelection()
        s.format.setBackground(QColor(t["line"]))
        s.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        s.cursor = self.textCursor()
        s.cursor.clearSelection()
        sels.append(s)
        sels += self.bracket_selections()
        sels += self.search_sel
        self.setExtraSelections(sels)
        self.line_area.update()

    def _char(self, pos):
        d = self.document()
        if pos < 0 or pos >= d.characterCount():
            return ""
        return d.characterAt(pos)

    def _scan(self, p, ch, other, step):
        depth, i, n = 0, p, self.document().characterCount()
        for _ in range(20000):
            if not 0 <= i < n:
                return -1
            c = self.document().characterAt(i)
            if c == ch:
                depth += 1
            elif c == other:
                depth -= 1
            if depth == 0:
                return i
            i += step
        return -1

    def bracket_selections(self):
        pos = self.textCursor().position()
        for p in (pos - 1, pos):
            ch = self._char(p)
            if ch in OPEN_BR:
                m = self._scan(p, ch, OPEN_BR[ch], 1)
            elif ch in CLOSE_BR:
                m = self._scan(p, ch, CLOSE_BR[ch], -1)
            else:
                continue
            if m >= 0:
                return [self._bracket_sel(p), self._bracket_sel(m)]
            break
        return []

    def _bracket_sel(self, p):
        sel = QTextEdit.ExtraSelection()
        col = QColor(THEMES[self.theme]["accent"])
        col.setAlpha(90)
        sel.format.setBackground(col)
        c = QTextCursor(self.document())
        c.setPosition(p)
        c.setPosition(p + 1, QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = c
        return sel

    # ---- key handling ---------------------------------------------------- #
    def keyPressEvent(self, e):
        k, mods, txt = e.key(), e.modifiers(), e.text()
        modded = bool(mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier |
                              Qt.KeyboardModifier.AltModifier))
        if not modded:
            c = self.textCursor()
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                return self._smart_newline()
            if k == Qt.Key.Key_Tab:
                return self._tab()
            if k == Qt.Key.Key_Backtab:
                return self.indent_lines(-1)
            if k == Qt.Key.Key_Backspace and not c.hasSelection() and self._smart_backspace(c):
                return
            if len(txt) == 1 and txt.isprintable() and self._auto_pair(txt, c):
                return
        super().keyPressEvent(e)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoomRequested.emit(1 if e.angleDelta().y() > 0 else -1)
            e.accept()
        else:
            super().wheelEvent(e)

    def _auto_pair(self, txt, c):
        pos = c.position()
        prev, nxt = self._char(pos - 1), self._char(pos)
        if txt in CLOSERS and nxt == txt and not c.hasSelection():
            c.movePosition(QTextCursor.MoveOperation.NextCharacter)
            self.setTextCursor(c)
            return True
        if txt not in AUTO:
            return False
        if c.hasSelection():
            sel = c.selectedText().replace("\u2029", "\n")
            c.insertText(txt + sel + AUTO[txt])
            return True
        if txt in QUOTES and (prev.isalnum() or prev == "\\" or nxt.isalnum()):
            return False
        if nxt and not (nxt.isspace() or nxt in ")]},;:."):
            return False
        c.insertText(txt + AUTO[txt])
        c.movePosition(QTextCursor.MoveOperation.PreviousCharacter)
        self.setTextCursor(c)
        return True

    def _smart_backspace(self, c):
        pos = c.position()
        prev, nxt = self._char(pos - 1), self._char(pos)
        if prev and AUTO.get(prev) == nxt:
            c.beginEditBlock()
            c.deleteChar()
            c.deletePreviousChar()
            c.endEditBlock()
            self.setTextCursor(c)
            return True
        col = c.positionInBlock()
        before = c.block().text()[:col]
        if col >= 4 and col % 4 == 0 and before == " " * col:
            c.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)
            c.removeSelectedText()
            self.setTextCursor(c)
            return True
        return False

    def _smart_newline(self):
        c = self.textCursor()
        c.beginEditBlock()
        if c.hasSelection():
            c.removeSelectedText()
        line, col = c.block().text(), c.positionInBlock()
        before, after = line[:col], line[col:]
        indent = re.match(r"[ \t]*", line).group()
        s = before.rstrip()
        extra = ""
        code = self.lang not in ("Plain Text", "Markdown")
        if code and (s.endswith(("{", "(", "[")) or (s.endswith(":") and self.lang == "Python")):
            extra = INDENT
        if (self.lang == "Python" and len(indent) >= 4 and
                re.match(r"\s*(return|pass|break|continue|raise)\b", s)):
            indent = indent[:-4]
        if code and s and s[-1] in OPEN_BR and after[:1] == OPEN_BR[s[-1]]:
            c.insertText("\n" + indent + extra + "\n" + indent)
            c.movePosition(QTextCursor.MoveOperation.Up)
            c.movePosition(QTextCursor.MoveOperation.EndOfLine)
        else:
            c.insertText("\n" + indent + extra)
        c.endEditBlock()
        self.setTextCursor(c)
        self.ensureCursorVisible()

    def _tab(self):
        c = self.textCursor()
        if c.hasSelection():
            return self.indent_lines(1)
        n = 4 - c.positionInBlock() % 4
        c.insertText(" " * n)

    # ---- line operations ------------------------------------------------- #
    def block_range(self):
        c, doc = self.textCursor(), self.document()
        b1, b2 = doc.findBlock(c.selectionStart()), doc.findBlock(c.selectionEnd())
        if c.hasSelection() and b2.position() == c.selectionEnd() and b2.blockNumber() > b1.blockNumber():
            b2 = b2.previous()
        return b1, b2

    def indent_lines(self, delta):
        b, last = self.block_range()
        c = self.textCursor()
        c.beginEditBlock()
        while b.isValid():
            cur = QTextCursor(b)
            if delta > 0:
                if b.text().strip() or b == last:
                    cur.insertText(INDENT)
            else:
                text = b.text()
                k = 1 if text.startswith("\t") else min(4, len(text) - len(text.lstrip(" ")))
                if k:
                    cur.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, k)
                    cur.removeSelectedText()
            if b.blockNumber() == last.blockNumber():
                break
            b = b.next()
        c.endEditBlock()

    def toggle_comment(self):
        prefix = COMMENT_PREFIX.get(self.lang)
        if not prefix:
            return
        b, last = self.block_range()
        blocks = []
        while b.isValid():
            blocks.append(b)
            if b.blockNumber() == last.blockNumber():
                break
            b = b.next()
        lines = [x for x in blocks if x.text().strip()]
        if not lines:
            return
        uncomment = all(x.text().lstrip().startswith(prefix) for x in lines)
        col = min(len(x.text()) - len(x.text().lstrip()) for x in lines)
        c = self.textCursor()
        c.beginEditBlock()
        for blk in lines:
            text = blk.text()
            cur = QTextCursor(blk)
            if uncomment:
                idx = text.index(prefix)
                n = len(prefix) + (1 if text[idx + len(prefix):idx + len(prefix) + 1] == " " else 0)
                cur.setPosition(blk.position() + idx)
                cur.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, n)
                cur.removeSelectedText()
            else:
                cur.setPosition(blk.position() + col)
                cur.insertText(prefix + " ")
        c.endEditBlock()

    def duplicate_line(self):
        c = self.textCursor()
        c.beginEditBlock()
        if c.hasSelection():
            text = c.selectedText().replace("\u2029", "\n")
            end = c.selectionEnd()
            c.setPosition(end)
            c.insertText(text)
        else:
            b = c.block()
            cur = QTextCursor(b)
            cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cur.insertText("\n" + b.text())
        c.endEditBlock()

    def delete_line(self):
        b1, b2 = self.block_range()
        c = self.textCursor()
        end = min(b2.position() + b2.length(), self.document().characterCount() - 1)
        c.beginEditBlock()
        c.setPosition(b1.position())
        c.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        c.removeSelectedText()
        c.endEditBlock()

    def move_lines(self, direction):
        b1, b2 = self.block_range()
        other = b1.previous() if direction < 0 else b2.next()
        if not other.isValid():
            return
        doc = self.document()
        cur = self.textCursor()
        anchor, pos = cur.anchor(), cur.position()
        start, end = b1.position(), b2.position() + len(b2.text())
        sel = QTextCursor(doc)
        sel.setPosition(start)
        sel.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        text = sel.selectedText().replace("\u2029", "\n")
        otext = other.text()
        edit = QTextCursor(doc)
        edit.beginEditBlock()
        if direction < 0:
            edit.setPosition(other.position())
            edit.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            edit.insertText(text + "\n" + otext)
            shift = -(len(otext) + 1)
        else:
            oend = other.position() + len(otext)
            edit.setPosition(start)
            edit.setPosition(oend, QTextCursor.MoveMode.KeepAnchor)
            edit.insertText(otext + "\n" + text)
            shift = len(otext) + 1
        edit.endEditBlock()
        nc = self.textCursor()
        nc.setPosition(anchor + shift)
        nc.setPosition(pos + shift, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(nc)


# --------------------------------------------------------------------------- #
#  macOS window chrome: traffic lights, icon buttons, title bar
# --------------------------------------------------------------------------- #
class TrafficLights(QWidget):
    close_clicked = pyqtSignal()
    min_clicked = pyqtSignal()
    zoom_clicked = pyqtSignal(bool)  # True when Option/Alt held (full screen)
    COLORS = ("#ff5f57", "#febc2e", "#28c840")

    def __init__(self):
        super().__init__()
        self.setFixedSize(76, 40)
        self.hover = False
        self.active = True
        self.down = -1
        self.inactive = QColor("#4a4a4d")

    def set_active(self, on):
        self.active = on
        self.update()

    def set_theme(self, theme):
        self.inactive = QColor(THEMES[theme]["inactive"])
        self.update()

    def _centers(self):
        return [QPointF(20 + i * 20, 20) for i in range(3)]

    def _hit(self, pos):
        for i, c in enumerate(self._centers()):
            if (pos.x() - c.x()) ** 2 + (pos.y() - c.y()) ** 2 <= 100:
                return i
        return -1

    def enterEvent(self, e):
        self.hover = True
        self.update()

    def leaveEvent(self, e):
        self.hover = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.down = self._hit(e.position())
            self.update()

    def mouseReleaseEvent(self, e):
        i = self._hit(e.position())
        if i == self.down and i >= 0:
            if i == 0:
                self.close_clicked.emit()
            elif i == 1:
                self.min_clicked.emit()
            else:
                self.zoom_clicked.emit(bool(e.modifiers() & Qt.KeyboardModifier.AltModifier))
        self.down = -1
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, c in enumerate(self._centers()):
            base = QColor(self.COLORS[i]) if (self.active or self.hover) else self.inactive
            if self.down == i:
                base = base.darker(135)
            p.setPen(QPen(base.darker(125), 1))
            p.setBrush(base)
            p.drawEllipse(c, 6.0, 6.0)
            if self.hover:
                self._glyph(p, i, c)

    def _glyph(self, p, i, c):
        x, y = c.x(), c.y()
        ink = QColor(0, 0, 0, 150)
        pen = QPen(ink, 1.3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        if i == 0:
            p.drawLine(QPointF(x - 2.2, y - 2.2), QPointF(x + 2.2, y + 2.2))
            p.drawLine(QPointF(x - 2.2, y + 2.2), QPointF(x + 2.2, y - 2.2))
        elif i == 1:
            p.drawLine(QPointF(x - 2.6, y), QPointF(x + 2.6, y))
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(ink)
            p.drawPolygon(QPolygonF([QPointF(x + 2.8, y - 2.8), QPointF(x - 0.6, y - 2.8),
                                     QPointF(x + 2.8, y + 0.6)]))
            p.drawPolygon(QPolygonF([QPointF(x - 2.8, y + 2.8), QPointF(x + 0.6, y + 2.8),
                                     QPointF(x - 2.8, y - 0.6)]))


class IconButton(QToolButton):
    def __init__(self, kind, tip):
        super().__init__()
        self.kind = kind
        self.col = QColor("#98989d")
        self.setToolTip(tip)
        self.setFixedSize(30, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(self.col, 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = self.width() / 2, self.height() / 2
        if self.kind == "sidebar":
            p.drawRoundedRect(QRectF(cx - 8, cy - 6, 16, 12), 2.5, 2.5)
            p.drawLine(QPointF(cx - 3, cy - 6), QPointF(cx - 3, cy + 6))
        elif self.kind == "search":
            p.drawEllipse(QPointF(cx - 1.5, cy - 1.5), 5, 5)
            p.drawLine(QPointF(cx + 2, cy + 2), QPointF(cx + 6.5, cy + 6.5))
        else:  # theme (half-filled circle)
            p.drawEllipse(QPointF(cx, cy), 6.5, 6.5)
            p.setBrush(self.col)
            p.drawChord(QRectF(cx - 6.5, cy - 6.5, 13, 13), 90 * 16, 180 * 16)


class TitleBar(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("titlebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(40)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        left = QWidget()
        left.setFixedWidth(170)
        ll = QHBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(4)
        self.lights = TrafficLights()
        self.btn_side = IconButton("sidebar", "Toggle Sidebar")
        ll.addWidget(self.lights)
        ll.addWidget(self.btn_side)
        ll.addStretch(1)

        self.label = QLabel(APP)
        self.label.setObjectName("titlelabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        right = QWidget()
        right.setFixedWidth(170)
        rl = QHBoxLayout(right)
        rl.setContentsMargins(0, 0, 10, 0)
        rl.setSpacing(2)
        rl.addStretch(1)
        self.btn_search = IconButton("search", "Command Palette")
        self.btn_theme = IconButton("theme", "Toggle Light/Dark")
        rl.addWidget(self.btn_search)
        rl.addWidget(self.btn_theme)

        lay.addWidget(left)
        lay.addWidget(self.label, 1)
        lay.addWidget(right)

        self.lights.close_clicked.connect(win.close)
        self.lights.min_clicked.connect(win.showMinimized)
        self.lights.zoom_clicked.connect(lambda full: win.toggle_full() if full else win.toggle_max())
        self.btn_side.clicked.connect(win.toggle_sidebar)
        self.btn_search.clicked.connect(win.command_palette)
        self.btn_theme.clicked.connect(win.toggle_theme)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.win.windowHandle():
            self.win.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, e):
        self.win.toggle_max()


# --------------------------------------------------------------------------- #
#  Find / Replace bar
# --------------------------------------------------------------------------- #
class FindBar(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName("findbar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(6)
        self.find = QLineEdit()
        self.find.setPlaceholderText("Find")
        self.find.setMinimumWidth(190)
        self.b_case = self._toggle("Aa", "Match case")
        self.b_word = self._toggle("ab", "Whole word")
        self.b_re = self._toggle(".*", "Regular expression")
        self.count = QLabel("")
        self.count.setMinimumWidth(80)
        prev, nxt = QToolButton(), QToolButton()
        prev.setText("\u2191")
        nxt.setText("\u2193")
        prev.clicked.connect(lambda: self.find_next(False))
        nxt.clicked.connect(lambda: self.find_next(True))
        self.repl = QLineEdit()
        self.repl.setPlaceholderText("Replace")
        self.repl.setMinimumWidth(150)
        b1, b2 = QPushButton("Replace"), QPushButton("All")
        b1.setAutoDefault(False)
        b2.setAutoDefault(False)
        b1.clicked.connect(self.replace_one)
        b2.clicked.connect(self.replace_all)
        close = QToolButton()
        close.setText("\u2715")
        close.clicked.connect(self.close_bar)
        for w in (self.find, self.b_case, self.b_word, self.b_re, self.count, prev, nxt,
                  self.repl, b1, b2):
            lay.addWidget(w)
        lay.addStretch(1)
        lay.addWidget(close)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.refresh)
        self.find.textChanged.connect(self.on_text)
        self.find.returnPressed.connect(lambda: self.find_next(True))
        self.repl.returnPressed.connect(self.replace_one)
        self.hide()

    def _toggle(self, text, tip):
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setCheckable(True)
        b.toggled.connect(lambda _: self.refresh())
        return b

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close_bar()
        else:
            super().keyPressEvent(e)

    def open_bar(self):
        ed = self.win.current_editor()
        if not ed:
            return
        sel = ed.textCursor().selectedText()
        if sel and "\u2029" not in sel:
            self.find.setText(sel)
        self.show()
        self.find.setFocus()
        self.find.selectAll()
        self.refresh()

    def close_bar(self):
        self.hide()
        for ed in self.win.editors():
            ed.set_search([])
        ed = self.win.current_editor()
        if ed:
            ed.setFocus()

    def schedule(self):
        if self.isVisible():
            self.timer.start()

    def pattern(self):
        t = self.find.text()
        if not t:
            self.find.setStyleSheet("")
            return None
        try:
            s = t if self.b_re.isChecked() else re.escape(t)
            if self.b_word.isChecked():
                s = r"\b(?:" + s + r")\b"
            rx = re.compile(s, (0 if self.b_case.isChecked() else re.I) | re.M)
            self.find.setStyleSheet("")
            return rx
        except re.error:
            self.find.setStyleSheet("border:1px solid #ff453a;")
            return None

    def matches(self, rx, ed):
        out = []
        for m in rx.finditer(ed.toPlainText()):
            if m.end() > m.start():
                out.append(m)
                if len(out) >= 5000:
                    break
        return out

    def refresh(self):
        ed = self.win.current_editor()
        if not ed or not self.isVisible():
            return
        rx = self.pattern()
        ms = self.matches(rx, ed) if rx else []
        ed.set_search([(m.start(), m.end()) for m in ms])
        if rx and not ms:
            self.count.setText("No results")
        elif ms:
            start = ed.textCursor().selectionStart()
            idx = next((i + 1 for i, m in enumerate(ms) if m.start() == start), 0)
            self.count.setText("%s of %d" % (idx, len(ms)) if idx else "%d found" % len(ms))
        else:
            self.count.setText("")

    def on_text(self):
        self.refresh()
        self.find_next(True, incremental=True)

    def find_next(self, forward=True, incremental=False):
        ed = self.win.current_editor()
        rx = self.pattern()
        if not ed or not rx:
            return
        ms = self.matches(rx, ed)
        if not ms:
            return
        c = ed.textCursor()
        if forward:
            pos = c.selectionStart() if incremental else c.selectionEnd()
            cand = [m for m in ms if m.start() >= pos]
            m = cand[0] if cand else ms[0]
        else:
            pos = c.selectionStart()
            cand = [m for m in ms if m.end() <= pos]
            m = cand[-1] if cand else ms[-1]
        c.setPosition(m.start())
        c.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
        ed.setTextCursor(c)
        ed.centerCursor()
        self.refresh()

    def _expand(self, m):
        r = self.repl.text()
        if self.b_re.isChecked():
            try:
                return m.expand(r)
            except (re.error, IndexError):
                return r
        return r

    def replace_one(self):
        ed, rx = self.win.current_editor(), self.pattern()
        if not ed or not rx:
            return
        c = ed.textCursor()
        if c.hasSelection():
            m = rx.fullmatch(c.selectedText().replace("\u2029", "\n"))
            if m:
                c.insertText(self._expand(m))
        self.find_next(True)

    def replace_all(self):
        ed, rx = self.win.current_editor(), self.pattern()
        if not ed or not rx:
            return
        text = ed.toPlainText()
        n = len(self.matches(rx, ed))
        new = rx.sub(lambda m: self._expand(m), text)
        if new != text:
            c = QTextCursor(ed.document())
            c.beginEditBlock()
            c.select(QTextCursor.SelectionType.Document)
            c.insertText(new)
            c.endEditBlock()
            self.win.flash("Replaced %d occurrence%s" % (n, "" if n == 1 else "s"))
        self.refresh()


# --------------------------------------------------------------------------- #
#  Command palette / quick open
# --------------------------------------------------------------------------- #
def fuzzy(q, s):
    q, sl = q.lower(), s.lower()
    if q in sl:
        return -100 + sl.index(q)
    i, first, last = 0, -1, -1
    for ch in q:
        j = sl.find(ch, i)
        if j < 0:
            return None
        first = j if first < 0 else first
        last, i = j, j + 1
    return (last - first) + first * 0.1


class Palette(QDialog):
    def __init__(self, win, items, placeholder):
        super().__init__(win, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.win, self.items, self.rows = win, items, []
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setObjectName("palette")
        outer.addWidget(frame)
        v = QVBoxLayout(frame)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(8)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.list = QListWidget()
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        v.addWidget(self.edit)
        v.addWidget(self.list)
        self.setFixedWidth(580)
        self.edit.textChanged.connect(self.filter)
        self.edit.returnPressed.connect(self.accept_current)
        self.list.itemClicked.connect(lambda _: self.accept_current())
        self.edit.installEventFilter(self)
        self.filter("")

    def filter(self, q):
        rows = []
        for label, hint, cb in self.items:
            s = fuzzy(q, label) if q else 0
            if s is not None:
                rows.append((s, label, hint, cb))
        rows.sort(key=lambda r: r[0])
        rows = rows[:50]
        self.rows = [r[3] for r in rows]
        self.list.clear()
        for _, label, hint, _cb in rows:
            self.list.addItem(QListWidgetItem(label + (("      " + hint) if hint else "")))
        if rows:
            self.list.setCurrentRow(0)
        self.list.setFixedHeight(max(34, min(len(rows), 10) * 32 + 6))
        self.adjustSize()

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.KeyPress:
            k = ev.key()
            if k in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                r = self.list.currentRow() + (1 if k == Qt.Key.Key_Down else -1)
                self.list.setCurrentRow(max(0, min(self.list.count() - 1, r)))
                return True
            if k == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(obj, ev)

    def accept_current(self):
        r = self.list.currentRow()
        if 0 <= r < len(self.rows):
            cb = self.rows[r]
            self.close()
            QTimer.singleShot(0, cb)

    def popup(self):
        g = self.win.mapToGlobal(QPoint(0, 0))
        self.move(g.x() + (self.win.width() - self.width()) // 2, g.y() + 60)
        self.show()
        self.edit.setFocus()


# --------------------------------------------------------------------------- #
#  Main window
# --------------------------------------------------------------------------- #
def system_theme():
    try:
        dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        return "dark" if dark else "light"
    except Exception:
        return "dark"


class MacEdit(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MacEdit", "MacEdit")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setWindowTitle(APP)
        self.setMinimumSize(680, 440)
        self.resize(int(self.settings.value("w", 1180)), int(self.settings.value("h", 760)))

        self.theme = str(self.settings.value("theme", system_theme()))
        self.wrap = self.settings.value("wrap", False, type=bool)
        self.autosave = self.settings.value("autosave", False, type=bool)
        self.font_size = self.settings.value("fontsize", 13, type=int)
        self.folder = None
        self.untitled = 0
        self.maxed = False
        self.cmds = []
        self.menubar = QMenuBar()

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(1200)
        self.autosave_timer.timeout.connect(self.autosave_now)

        self._build_ui()
        self._build_menus()
        self.apply_theme()
        self.restore_session()
        self.update_status()

    # ---- UI ------------------------------------------------------------- #
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        self.outer = outer
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setCursor(Qt.CursorShape.ArrowCursor)
        outer.addWidget(self.container)
        v = QVBoxLayout(self.container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.titlebar = TitleBar(self)
        v.addWidget(self.titlebar)
        if not MAC:
            v.addWidget(self.menubar)

        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.split.setHandleWidth(1)
        self.split.setChildrenCollapsible(False)

        # sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.sidebar.setMinimumWidth(160)
        sv = QVBoxLayout(self.sidebar)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.setSpacing(0)
        self.side_head = QLabel("EXPLORER")
        self.side_head.setObjectName("sidehead")
        sv.addWidget(self.side_head)
        self.side_stack = QStackedWidget()
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setContentsMargins(14, 14, 14, 14)
        btn = QPushButton("Open Folder\u2026")
        btn.clicked.connect(self.open_folder_dialog)
        el.addWidget(btn)
        el.addStretch(1)
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        for c in (1, 2, 3):
            self.tree.hideColumn(c)
        self.tree.setAnimated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.activated.connect(self.on_tree_activated)
        self.side_stack.addWidget(empty)
        self.side_stack.addWidget(self.tree)
        sv.addWidget(self.side_stack, 1)

        # main area
        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(0, 0, 0, 0)
        mv.setSpacing(0)
        self.findbar = FindBar(self)
        mv.addWidget(self.findbar)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._welcome())
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.stack.addWidget(self.tabs)
        mv.addWidget(self.stack, 1)

        self.split.addWidget(self.sidebar)
        self.split.addWidget(main)
        self.split.setStretchFactor(1, 1)
        self.split.setSizes([240, 940])
        v.addWidget(self.split, 1)

        # status bar
        sb = QWidget()
        sb.setObjectName("statusbar")
        sb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sb.setFixedHeight(26)
        h = QHBoxLayout(sb)
        h.setContentsMargins(12, 0, 8, 0)
        h.setSpacing(14)
        self.msg_label = QLabel("")
        self.pos_label = QLabel("")
        self.sel_label = QLabel("")
        self.indent_label = QLabel("Spaces: 4")
        self.enc_label = QLabel("")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(LANG_NAMES)
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_combo.activated.connect(self.on_lang_chosen)
        h.addWidget(self.msg_label)
        h.addStretch(1)
        for w in (self.sel_label, self.pos_label, self.indent_label, self.enc_label, self.lang_combo):
            h.addWidget(w)
        v.addWidget(sb)

    def _welcome(self):
        w = QWidget()
        w.setObjectName("welcome")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(APP)
        title.setObjectName("wtitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("A fast, native-feeling code editor")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rows = [("New File", CMD + "N"), ("Open File", CMD + "O"), ("Open Folder", CMD + SHIFT + "O"),
                ("Quick Open", CMD + "P"), ("Command Palette", CMD + SHIFT + "P")]
        hint = QLabel("<br>".join("%s &nbsp;&nbsp;<b>%s</b>" % r for r in rows))
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(22)
        lay.addWidget(hint)
        return w

    # ---- menus & commands ------------------------------------------------ #
    def _act(self, menu, text, slot, shortcut=None, checkable=False, checked=False, palette=True):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        if checkable:
            a.setCheckable(True)
            a.setChecked(checked)
            a.triggered.connect(slot)
        else:
            a.triggered.connect(lambda _=False, s=slot: s())
        menu.addAction(a)
        if palette:
            self.cmds.append(a)
        return a

    def _ed(self, fn):
        def run():
            ed = self.current_editor()
            if ed:
                fn(ed)
        return run

    def _build_menus(self):
        mb = self.menubar
        f = mb.addMenu("File")
        self._act(f, "New File", self.new_file, "Ctrl+N")
        self._act(f, "Open\u2026", self.open_dialog, "Ctrl+O")
        self._act(f, "Open Folder\u2026", self.open_folder_dialog, "Ctrl+Shift+O")
        f.addSeparator()
        self._act(f, "Save", self.save, "Ctrl+S")
        self._act(f, "Save As\u2026", self.save_as, "Ctrl+Shift+S")
        self._act(f, "Save All", self.save_all, "Ctrl+Alt+S")
        f.addSeparator()
        self._act(f, "Close Tab", self.close_tab, "Ctrl+W")
        self._act(f, "Quit " + APP, self.close, "Ctrl+Q", palette=False)

        e = mb.addMenu("Edit")
        self._act(e, "Undo", self._ed(lambda x: x.undo()), "Ctrl+Z")
        self._act(e, "Redo", self._ed(lambda x: x.redo()), "Ctrl+Shift+Z")
        e.addSeparator()
        self._act(e, "Cut", self._ed(lambda x: x.cut()), "Ctrl+X", palette=False)
        self._act(e, "Copy", self._ed(lambda x: x.copy()), "Ctrl+C", palette=False)
        self._act(e, "Paste", self._ed(lambda x: x.paste()), "Ctrl+V", palette=False)
        self._act(e, "Select All", self._ed(lambda x: x.selectAll()), "Ctrl+A")
        e.addSeparator()
        self._act(e, "Find & Replace", self.findbar.open_bar, "Ctrl+F")
        self._act(e, "Find Next", lambda: self.findbar.find_next(True), "Ctrl+G")
        self._act(e, "Find Previous", lambda: self.findbar.find_next(False), "Ctrl+Shift+G")
        self._act(e, "Go to Line\u2026", self.goto_line, "Ctrl+L")
        e.addSeparator()
        self._act(e, "Toggle Comment", self._ed(lambda x: x.toggle_comment()), "Ctrl+/")
        self._act(e, "Duplicate Line", self._ed(lambda x: x.duplicate_line()), "Ctrl+Shift+D")
        self._act(e, "Delete Line", self._ed(lambda x: x.delete_line()), "Ctrl+Shift+K")
        self._act(e, "Move Line Up", self._ed(lambda x: x.move_lines(-1)), "Alt+Up")
        self._act(e, "Move Line Down", self._ed(lambda x: x.move_lines(1)), "Alt+Down")
        self._act(e, "Indent", self._ed(lambda x: x.indent_lines(1)), "Ctrl+]")
        self._act(e, "Outdent", self._ed(lambda x: x.indent_lines(-1)), "Ctrl+[")

        v = mb.addMenu("View")
        self._act(v, "Command Palette\u2026", self.command_palette, "Ctrl+Shift+P", palette=False)
        self._act(v, "Quick Open\u2026", self.quick_open, "Ctrl+P")
        v.addSeparator()
        self._act(v, "Toggle Sidebar", self.toggle_sidebar, "Ctrl+B")
        self._act(v, "Toggle Light/Dark Theme", self.toggle_theme, "Ctrl+Shift+T")
        self.act_wrap = self._act(v, "Word Wrap", self.set_wrap, "Alt+Z", True, self.wrap)
        self.act_auto = self._act(v, "Auto Save", self.set_autosave, None, True, self.autosave)
        v.addSeparator()
        self._act(v, "Zoom In", lambda: self.zoom(1), "Ctrl+=")
        self._act(v, "Zoom Out", lambda: self.zoom(-1), "Ctrl+-")
        self._act(v, "Reset Zoom", lambda: self.zoom(0), "Ctrl+0")
        v.addSeparator()
        self._act(v, "Enter Full Screen", self.toggle_full, "Ctrl+Meta+F" if MAC else "F11")

        w = mb.addMenu("Window")
        self._act(w, "Minimize", self.showMinimized, "Ctrl+M")
        self._act(w, "Zoom", self.toggle_max)
        self._act(w, "Next Tab", lambda: self.cycle_tab(1), "Ctrl+Alt+Right")
        self._act(w, "Previous Tab", lambda: self.cycle_tab(-1), "Ctrl+Alt+Left")

    # ---- editor/tab management ------------------------------------------ #
    def current_editor(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    def editors(self):
        return [self.tabs.widget(i) for i in range(self.tabs.count())]

    def new_file(self):
        self.untitled += 1
        self._add_editor(None, "", "Untitled" if self.untitled == 1 else "Untitled %d" % self.untitled)

    def _add_editor(self, path, text, untitled_name="Untitled", encoding="utf-8", eol="\n"):
        ed = CodeEditor(self.theme)
        ed.path, ed.encoding, ed.eol = path, encoding, eol
        ed.untitled_name = untitled_name
        ed.set_wrap(self.wrap)
        ed.set_font_size(self.font_size)
        ed.setPlainText(text)
        ed.document().setModified(False)
        ed.set_language(detect_language(path, text))
        ed.cursorPositionChanged.connect(self.update_status)
        ed.selectionChanged.connect(self.update_status)
        ed.zoomRequested.connect(self.zoom)
        ed.document().modificationChanged.connect(lambda _m, e=ed: self.update_tab(e))
        ed.document().contentsChanged.connect(self.on_contents_changed)
        idx = self.tabs.addTab(ed, self._tab_label(ed))
        btn = QToolButton()
        btn.setText("\u2715")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(18, 18)
        btn.clicked.connect(lambda _=False, e=ed: self.close_editor(e))
        self.tabs.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, btn)
        self.tabs.setTabToolTip(idx, path or "")
        self.tabs.setCurrentIndex(idx)
        self.stack.setCurrentIndex(1)
        ed.setFocus()
        return ed

    def _tab_label(self, ed):
        return ("\u25cf " if ed.document().isModified() else "") + ed.display_name()

    def update_tab(self, ed):
        idx = self.tabs.indexOf(ed)
        if idx >= 0:
            self.tabs.setTabText(idx, self._tab_label(ed))
            self.tabs.setTabToolTip(idx, ed.path or "")
        self.update_title()

    def on_contents_changed(self):
        if self.autosave:
            self.autosave_timer.start()
        self.findbar.schedule()

    def on_tab_changed(self, _i):
        ed = self.current_editor()
        if ed:
            ed.setFocus()
        self.findbar.schedule()
        self.update_status()
        self.update_title()

    def cycle_tab(self, d):
        n = self.tabs.count()
        if n:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + d) % n)

    # ---- file operations -------------------------------------------------- #
    def open_dialog(self):
        start = self.folder or os.path.expanduser("~")
        paths, _ = QFileDialog.getOpenFileNames(self, "Open", start)
        for p in paths:
            self.open_path(p)

    def open_path(self, path):
        path = os.path.abspath(path)
        for ed in self.editors():
            if ed.path == path:
                self.tabs.setCurrentWidget(ed)
                return ed
        try:
            if os.path.getsize(path) > 30 * 1024 * 1024:
                if QMessageBox.question(self, APP, "This file is very large. Open anyway?") != \
                        QMessageBox.StandardButton.Yes:
                    return None
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as ex:
            QMessageBox.critical(self, APP, "Could not open file:\n%s" % ex)
            return None
        if b"\x00" in raw[:8192]:
            QMessageBox.information(self, APP, "\u201c%s\u201d looks like a binary file." % os.path.basename(path))
            return None
        enc = "utf-8"
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text, enc = raw.decode("latin-1"), "latin-1"
        eol = "\r\n" if "\r\n" in text else "\n"
        text = text.replace("\r\n", "\n")
        return self._add_editor(path, text, encoding=enc, eol=eol)

    def save(self):
        ed = self.current_editor()
        if ed:
            self.save_editor(ed)

    def save_as(self):
        ed = self.current_editor()
        if ed:
            self.save_editor(ed, True)

    def save_all(self):
        for ed in self.editors():
            if ed.document().isModified():
                self.save_editor(ed)

    def save_editor(self, ed, force_dialog=False):
        path = ed.path
        if not path or force_dialog:
            start = os.path.join(self.folder or os.path.expanduser("~"), ed.display_name())
            path, _ = QFileDialog.getSaveFileName(self, "Save", start)
            if not path:
                return False
        try:
            with open(path, "w", encoding=ed.encoding, newline="") as fh:
                fh.write(ed.toPlainText().replace("\n", ed.eol))
        except (OSError, UnicodeEncodeError) as ex:
            QMessageBox.critical(self, APP, "Could not save file:\n%s" % ex)
            return False
        was_untitled = ed.path is None
        ed.path = path
        if was_untitled or force_dialog:
            ed.set_language(detect_language(path, ed.toPlainText()))
        ed.document().setModified(False)
        self.update_tab(ed)
        self.update_status()
        self.flash("Saved " + os.path.basename(path))
        return True

    def autosave_now(self):
        for ed in self.editors():
            if ed.path and ed.document().isModified():
                self.save_editor(ed)

    def close_tab(self):
        ed = self.current_editor()
        if ed:
            self.close_editor(ed)

    def confirm_close(self, ed):
        box = QMessageBox(self)
        box.setText("Do you want to save the changes you made to \u201c%s\u201d?" % ed.display_name())
        box.setInformativeText("Your changes will be lost if you don\u2019t save them.")
        B = QMessageBox.StandardButton
        box.setStandardButtons(B.Save | B.Discard | B.Cancel)
        box.setDefaultButton(B.Save)
        r = box.exec()
        if r == B.Save:
            return self.save_editor(ed)
        return r == B.Discard

    def close_editor(self, ed):
        if ed.document().isModified() and not self.confirm_close(ed):
            return
        idx = self.tabs.indexOf(ed)
        self.tabs.removeTab(idx)
        ed.deleteLater()
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)
            self.findbar.hide()
        self.update_status()
        self.update_title()

    # ---- sidebar / folders ------------------------------------------------ #
    def open_folder_dialog(self):
        p = QFileDialog.getExistingDirectory(self, "Open Folder", self.folder or os.path.expanduser("~"))
        if p:
            self.set_folder(p)

    def set_folder(self, path):
        if not os.path.isdir(path):
            return
        self.folder = os.path.abspath(path)
        self.model.setRootPath(self.folder)
        self.tree.setRootIndex(self.model.index(self.folder))
        self.side_head.setText(os.path.basename(self.folder).upper() or self.folder)
        self.side_stack.setCurrentIndex(1)
        self.sidebar.show()
        self.update_title()

    def on_tree_activated(self, idx):
        p = self.model.filePath(idx)
        if os.path.isfile(p):
            self.open_path(p)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def quick_open(self):
        if not self.folder:
            self.flash("Open a folder first (%s%sO)" % (CMD, SHIFT))
            return
        skip = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", ".idea"}
        items = []
        for root, dirs, files in os.walk(self.folder):
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
            for fn in files:
                if fn.startswith("."):
                    continue
                full = os.path.join(root, fn)
                items.append((os.path.relpath(full, self.folder), "", lambda p=full: self.open_path(p)))
                if len(items) > 8000:
                    break
        Palette(self, items, "Go to file\u2026").popup()

    def command_palette(self):
        items = []
        for a in self.cmds:
            label = a.text().replace("&", "").replace("\u2026", "")
            hint = a.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
            items.append((label, hint, a.trigger))
        Palette(self, items, "Type a command\u2026").popup()

    # ---- view toggles ------------------------------------------------------ #
    def goto_line(self):
        ed = self.current_editor()
        if not ed:
            return
        cur = ed.textCursor().blockNumber() + 1
        n, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", cur, 1, ed.blockCount())
        if ok:
            c = ed.textCursor()
            c.setPosition(ed.document().findBlockByLineNumber(n - 1).position())
            ed.setTextCursor(c)
            ed.centerCursor()
            ed.setFocus()

    def set_wrap(self, on):
        self.wrap = bool(on)
        for ed in self.editors():
            ed.set_wrap(self.wrap)

    def set_autosave(self, on):
        self.autosave = bool(on)
        self.flash("Auto Save " + ("on" if on else "off"))

    def zoom(self, d):
        self.font_size = 13 if d == 0 else max(8, min(40, self.font_size + d))
        for ed in self.editors():
            ed.set_font_size(self.font_size)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(build_qss(self.theme, 0 if self.maxed else 10))
        for ed in self.editors():
            ed.apply_theme(self.theme)
        t = THEMES[self.theme]
        self.titlebar.lights.set_theme(self.theme)
        for b in (self.titlebar.btn_side, self.titlebar.btn_search, self.titlebar.btn_theme):
            b.col = QColor(t["muted"])
            b.update()
        self.update()

    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def toggle_full(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    # ---- status / title ----------------------------------------------------- #
    def flash(self, text):
        self.msg_label.setText(text)
        QTimer.singleShot(2500, lambda: self.msg_label.setText(""))

    def update_status(self):
        ed = self.current_editor()
        if not ed:
            for w in (self.pos_label, self.sel_label, self.enc_label):
                w.setText("")
            return
        c = ed.textCursor()
        self.pos_label.setText("Ln %d, Col %d" % (c.blockNumber() + 1, c.positionInBlock() + 1))
        n = len(c.selectedText())
        self.sel_label.setText("%d selected" % n if n else "")
        eol_name = "CRLF" if ed.eol == "\r\n" else "LF"
        self.enc_label.setText("%s  %s" % (ed.encoding.upper(), eol_name))
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentText(ed.lang)
        self.lang_combo.blockSignals(False)

    def on_lang_chosen(self, _i):
        ed = self.current_editor()
        if ed:
            ed.set_language(self.lang_combo.currentText())

    def update_title(self):
        ed = self.current_editor()
        if ed:
            t = ed.display_name() + (" \u2014 Edited" if ed.document().isModified() else "")
        else:
            t = APP
        self.titlebar.label.setText(t)
        self.setWindowTitle(t)

    # ---- window behaviour (frameless resize, shadow, state) ----------------- #
    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange:
            maxed = bool(self.windowState() & (Qt.WindowState.WindowMaximized | Qt.WindowState.WindowFullScreen))
            if maxed != self.maxed:
                self.maxed = maxed
                m = 0 if maxed else MARGIN
                self.outer.setContentsMargins(m, m, m, m)
                self.apply_theme()
        elif e.type() == QEvent.Type.ActivationChange:
            self.titlebar.lights.set_active(self.isActiveWindow())
        super().changeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 1))  # keeps the margin clickable on macOS
        if self.maxed:
            return
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(MARGIN):
            a = int(46 * ((i + 1) / MARGIN) ** 2)
            p.setPen(QPen(QColor(0, 0, 0, a), 1))
            r = QRectF(self.rect()).adjusted(i + .5, i + .5, -i - .5, -i - .5)
            p.drawRoundedRect(r, 10 + (MARGIN - i), 10 + (MARGIN - i))

    def _edges(self, pos):
        edges = Qt.Edge(0)
        if self.maxed:
            return edges
        if pos.x() < MARGIN:
            edges |= Qt.Edge.LeftEdge
        if pos.x() > self.width() - MARGIN:
            edges |= Qt.Edge.RightEdge
        if pos.y() < MARGIN:
            edges |= Qt.Edge.TopEdge
        if pos.y() > self.height() - MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    def mouseMoveEvent(self, e):
        ed = self._edges(e.position().toPoint())
        L, R, T, B = Qt.Edge.LeftEdge, Qt.Edge.RightEdge, Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        if ed == (L | T) or ed == (R | B):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif ed == (R | T) or ed == (L | B):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif ed & (L | R):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif ed & (T | B):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def mousePressEvent(self, e):
        ed = self._edges(e.position().toPoint())
        if e.button() == Qt.MouseButton.LeftButton and ed and self.windowHandle():
            self.windowHandle().startSystemResize(ed)

    def leaveEvent(self, e):
        self.unsetCursor()

    # ---- drag & drop ---------------------------------------------------------- #
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if os.path.isdir(p):
                self.set_folder(p)
            elif os.path.isfile(p):
                self.open_path(p)

    # ---- session ---------------------------------------------------------------- #
    def restore_session(self):
        folder = self.settings.value("folder", "")
        if folder and os.path.isdir(str(folder)):
            self.set_folder(str(folder))
        else:
            self.sidebar.hide()
        sess = self.settings.value("session", [], type=list)
        if isinstance(sess, str):
            sess = [sess]
        for p in sess:
            if os.path.isfile(p):
                self.open_path(p)
        idx = self.settings.value("current", 0, type=int)
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)

    def closeEvent(self, e):
        for ed in self.editors():
            if ed.document().isModified():
                self.tabs.setCurrentWidget(ed)
                if not self.confirm_close(ed):
                    e.ignore()
                    return
        s = self.settings
        s.setValue("theme", self.theme)
        s.setValue("wrap", self.wrap)
        s.setValue("autosave", self.autosave)
        s.setValue("fontsize", self.font_size)
        s.setValue("folder", self.folder or "")
        s.setValue("session", [ed.path for ed in self.editors() if ed.path])
        s.setValue("current", self.tabs.currentIndex())
        if not self.maxed:
            s.setValue("w", self.width())
            s.setValue("h", self.height())
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setStyle("Fusion")
    win = MacEdit()
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            win.set_folder(arg)
        elif os.path.isfile(arg):
            win.open_path(arg)
    win.show()
    win.raise_()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
