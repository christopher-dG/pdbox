import argparse
import curses
import curses.textpad
import math
import os
import pdbox


class TUI:
    """A TUI client for pdbox."""
    def __init__(self, _):
        # Namespace to pass to pdbox functions.
        # TODO: Make this stuff properly configurable.
        self.args = argparse.Namespace(
            dryrun=False,
            quiet=False,
            follow_symlinks=True,
            only_show_errors=False,
            delete=False,
            chunksize=149.0,
            recursive=False,
            force=False,
        )

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
            self.args,
        )
        self.remote = WorkingDirectory(
            pdbox.models.get_remote("/"),
            remotewin,
            self.args,
        )

        self.status = curses.newwin(1, curses.COLS, 0, 0)  # Status bar.
        self.status.keypad(1)
        self.status.addstr("Nothing selected")

        self.selected = None  # Currently selected item(s).
        self.active = self.local  # Currently focused window.

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

        self.status.erase()

        if c == curses.KEY_UP:
            self.active.moveup()
        elif c == curses.KEY_DOWN:
            self.active.movedown()
        elif c == curses.KEY_LEFT:
            self.active = self.local
            self.remote.win.erase()
        elif c == curses.KEY_RIGHT:
            self.active = self.remote
            self.local.win.erase()
        elif c == 82 or c == 114:  # 'r'/'R'.
            self.reload()
        elif c == 32:  # Space bar.
            self.active.select()
        elif c == 10:  # Enter.
            self.active.cd()
        elif c == 66 or c == 98:  # 'b'/'B'.
            self.active.back()
        else:
            self.status.addstr(0, 2, "Unrecognized command: %d" % c)

        return 1

    def getinput(self, prompt):
        # Shorten the content windows by one line to show the input bar.
        y, x = self.active.getmaxyx()  # Both will always be the same height.
        self.local.win.resize(y - 1, x)
        self.remote.win.resize(y - 1, x)

        inputbar = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        textpad = curses.textpad.Textbox(inputbar)

        if not prompt.endswith(" "):
            prompt += " "
        inputbar.addstr(0, 1, prompt)
        self.refresh(inputbar)

        cmd = textpad.edit()[len(prompt) + 1:]

        y, x = self.active.getmaxyx()
        self.local.win.resize(y + 1, x)
        self.remote.win.resize(y + 1, x)

        # Erase the bottom border of the shortened windows.
        self.local.win.move(self.local.win.getmaxyx()[0] - 2, 0)
        self.local.win.deleteln()
        self.remote.win.move(self.remote.win.getmaxyx()[0] - 2, 0)
        self.remote.win.deleteln()

        self.refresh()
        return cmd

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

    def display(self):
        """Display the contents of the working directories on screen."""
        self.local.display()
        self.remote.display()
        self.active.highlight()
        self.refresh()


class WorkingDirectory:
    """A working directory being displayed on screen."""
    def __init__(self, folder, win, args):
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
        self.args = args

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
            self.contents = self.folder.contents(self.args)
        except Exception as e:
            pdbox.debug(e)
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

    def back(self):
        """Go to the parent directory."""
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
