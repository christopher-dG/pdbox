import curses
import curses.textpad
import math
import os
import pdbox

UP = [curses.KEY_UP]
DOWN = [curses.KEY_DOWN]
LEFT = [curses.KEY_LEFT]
RIGHT = [curses.KEY_RIGHT]
SPACE = [32]
ENTER = [10]
B = [66, 98]
H = [72, 104]
I = [73, 105]
Q = [81, 113]
R = [82, 114]


class TUI:
    """A TUI client for pdbox."""
    def __init__(self, **kwargs):
        # Namespace to pass to pdbox functions.
        # TODO: Make this stuff properly configurable.
        self.kwargs = kwargs

        # Local file view.
        localwin = curses.initscr()
        localwin.resize(curses.LINES - 1, math.ceil(curses.COLS / 2))
        localwin.mvwin(1, 0)
        # keypad is already enabled by curses.wrapper.

        #  Remote file view.
        remotewin = curses.newwin(
            curses.LINES - 1,
            int(curses.COLS / 2),
            1,
            math.ceil(curses.COLS / 2),
        )
        remotewin.keypad(1)

        # Working directories.
        self.local = WorkingDirectory(
            pdbox.models.get_local(os.curdir),
            localwin,
            self.kwargs,
        )
        self.remote = WorkingDirectory(
            pdbox.models.get_remote("/"),
            remotewin,
            self.kwargs,
        )

        self.status = curses.newwin(1, curses.COLS, 0, 0)  # Status bar.
        self.status.keypad(1)

        self.selected = None  # Currently selected item(s).
        self.active = self.local  # Currently focused window.
        self.inactive = self.remote  # The other window.

        curses.curs_set(0)
        curses.wrapper(self.run)

    def run(self, _):
        """Run the TUI."""
        self.reload()
        while True:
            self.display()
            if not self.keypress():
                break

    def keypress(self):
        """Parse a keypress into a command."""
        try:
            c = self.status.getch()
        except KeyboardInterrupt:
            return None

        if c in Q:
            return None
        if c in UP:
            self.active.moveup()
        elif c in DOWN:
            self.active.movedown()
        elif c in LEFT:
            self.active = self.local
            self.inactive = self.remote
            self.remote.win.erase()
        elif c in RIGHT:
            self.active = self.remote
            self.inactive = self.local
            self.local.win.erase()
        elif c in SPACE:
            self.inactive.selected.clear()
            self.active.select()
        elif c in ENTER:
            self.active.cd()
        elif c in B:
            self.active.back()
        elif c in R:
            self.reload()
        elif c in H:
            self.help()
        elif c in I:
            self.command(self.getinput("pdbox>"))

        return True

    def help(self):
        pass  # TODO

    def command(self, cmd):
        if not cmd:
            return
        try:
            cmd, args = cmd.split(maxsplit=1)
        except ValueError:
            pass

        if cmd in ["search", "find"]:
            pass  # TODO: Search for args.
        elif cmd in ["copy", "cp"]:
            pass  # TODO: Copy inactive selection to active window.
        elif cmd in ["move", "mv"]:
            pass  # TODO: Move inactive selection to active window.
        elif cmd in ["delete", "del", "remove", "rm", "rmdir"]:
            pass  # TODO: Delete active selection.
        elif cmd in ["share", "link"]:
            pass  # TODO: Generate sharing link (put this in library).

    def getinput(self, prompt):
        # Shorten the content windows by one line to show the input bar.
        y, x = self.active.win.getmaxyx()  # Both will be the same height.
        self.local.win.resize(y - 1, x)
        self.remote.win.resize(y - 1, x)

        inputbar = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        textpad = curses.textpad.Textbox(inputbar)

        if not prompt.endswith(" "):
            prompt += " "
        inputbar.addstr(0, 1, prompt)
        self.refresh(inputbar)

        curses.curs_set(1)
        try:
            cmd = textpad.edit()[len(prompt) + 1:]
        except KeyboardInterrupt:
            cmd = ""
        curses.curs_set(0)

        y, x = self.active.win.getmaxyx()
        self.local.win.resize(y + 1, x)
        self.remote.win.resize(y + 1, x)

        # Erase the bottom border of the shortened windows.
        self.local.win.move(self.local.win.getmaxyx()[0] - 2, 0)
        self.local.win.deleteln()
        self.remote.win.move(self.remote.win.getmaxyx()[0] - 2, 0)
        self.remote.win.deleteln()

        self.refresh()
        return cmd.lower().strip()

    def borders(self):
        """Draw borders on the main windows."""
        self.local.win.border()
        self.remote.win.border()
        local = self.local.folder.path.replace(os.path.expanduser("~"), "~")
        self.local.win.addstr(
            0,
            4,
            " [ %s (%d) ] " % (local, self.local.length),
        )
        self.remote.win.addstr(
            0,
            4,
            " [ %s (%d) ] " % (self.remote.folder.uri, self.remote.length),
        )

    def refresh(self, *wins):
        """Refresh all windows."""
        self.borders()
        self.status.refresh()
        self.local.win.refresh()
        self.remote.win.refresh()
        for win in wins:
            win.refresh()

    def reload(self):
        """Reload the contents of the working directories."""
        self.local.reload()
        self.remote.reload()
        self.refresh()

    def nselected(self):
        self.status.erase()
        s = "%d selected" % len(self.active.selected)
        if self.active == self.local:
            self.status.addstr(0, 2, s)
        else:
            self.status.addstr(0, self.status.getmaxyx()[1] - 2 - len(s), s)

    def display(self):
        """Display the contents of the working directories on screen."""
        self.local.display()
        self.remote.display()
        self.active.highlight()
        # self.nselected()
        self.refresh()


class WorkingDirectory:
    """A working directory being displayed on screen."""
    def __init__(self, folder, win, kwargs):
        self.folder = folder  # RemoteFolder or LocalFolder.
        self.win = win  # ncurses window.
        self.contents = None  # None until TUI.reload is called.
        self.offset = 0  # Start index of what's on screen.
        self.length = 0  # Number of items in contents.
        self.selected = []  # Indices of currently selected items.
        # Current cursor position on the active window.
        # This number is 0-indexed with respect to the window coordinates,
        # but 1-indexed with respect to the folder contents (contents begin
        # on row 1).
        self.cursor = 1
        self.kwargs = kwargs

    def display(self):
        """Display the contents of this directory on screen."""
        ymax = self.win.getmaxyx()[0]
        if self.contents is None:
            self.win.addstr(
                2,
                2,
                "Getting folder contents failed, try refreshing",
            )
        elif not self.contents:
            self.win.addstr(2, 2, "No contents")
        else:
            for i, entry in enumerate(self.contents[self.offset:]):
                y = i + 1  # Start underneath the border.
                if y >= ymax - 1:  # Leave a border space at the bottom.
                    break
                if is_folder(entry):
                    display_str = "%s/" % entry.name
                else:
                    display_str = entry.name
                x = "x" if i + self.offset in self.selected else " "
                self.win.addstr(y, 2, "[%s] %s" % (x, display_str))

    def reload(self):
        """Reload the contents of this directory."""
        try:
            self.contents = self.folder.contents(**self.kwargs)
        except Exception as e:
            pdbox.debug(e, **self.kwargs)
            self.contents = None
            self.length = 0
        else:
            self.length = len(self.contents)
        finally:
            self.win.erase()
            self.offset = 0  # Reset to the top of the folder.
            self.cursor = 1

    def highlight(self):
        """
        Highlight the ith entry in the window. i is 1-indexed.
        We'll also redraw the two adjacent entries, since one of them might
        have been highlighted previously.
        """
        if not self.contents or self.cursor > len(self.contents):
            return
        self.win.addstr(
            self.cursor,
            2,
            self.win.instr(self.cursor, 2),
            curses.A_REVERSE,
        )

        if self.cursor > 1:
            self.win.addstr(
                self.cursor - 1,
                2,
                self.win.instr(self.cursor - 1, 2),
            )
        if self.cursor < self.win.getmaxyx()[0] - 2:
            self.win.addstr(
                self.cursor + 1,
                2,
                self.win.instr(self.cursor + 1, 2),
            )

    def moveup(self):
        """Move the cursor up one place, scrolling if necessary."""
        if self.cursor == 1 and not self.offset:
            pass  # Already at the top.
        elif self.cursor == 1:
            self.win.erase()
            self.offset -= 1  # At the top of the page, scroll up.
        else:
            self.cursor -= 1  # Anywhere else.

    def movedown(self):
        """Move the cursor down one place, scrolling if necessary."""
        ymax = self.win.getmaxyx()[0] - 1
        if self.cursor == ymax or self.offset + self.cursor == self.length:
            pass  # Already at the bottom.
        elif self.cursor == ymax - 1:
            self.win.erase()
            self.offset += 1  # At the bottom of the page, scroll down.
        else:
            self.cursor += 1  # Anywhere else.

    def select(self):
        """Mark the item under the cursor as selected."""
        i = self.offset + self.cursor - 1
        if i in self.selected:
            self.selected.remove(i)
        else:
            self.selected.append(i)

    def cd(self):
        """Change directory to the folder under the cursor."""
        entry = self.contents[self.cursor - 1]
        if is_folder(entry):
            self.folder = entry
            self.reload()
            self.selected.clear()

    def back(self):
        """Go to the parent directory."""
        self.selected.clear()
        if not is_folder(self.folder):
            return
        try:
            self.folder = type(self.folder)(self.folder.parent)
        except ValueError as e:
            pdbox.debug(e)  # TODO: Deal with this.
        else:
            self.reload()


def is_folder(item):
    """Determine whether item is a folder."""
    return (
        isinstance(item, pdbox.models.RemoteFolder) or
        isinstance(item, pdbox.models.LocalFolder)
    )
