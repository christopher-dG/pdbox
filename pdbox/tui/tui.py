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

        #  Remote file view.
        remotewin = curses.newwin(
            curses.LINES - 1,
            int(curses.COLS / 2),
            1,
            math.ceil(curses.COLS / 2),
        )

        # Working directories.
        self.local = WorkingDirectory(
            pdbox.models.get_local(os.curdir),
            localwin,
        )
        self.remote = WorkingDirectory(
            pdbox.models.get_remote("/"),
            remotewin,
        )

        self.status = curses.newwin(1, curses.COLS, 0, 0)  # Status bar.
        self.status.addstr("Nothing selected")

        self.selected = None  # Currently selected item(s).
        self.active = self.local  # Currently focused window.

        # Current cursor position on the active window.
        # This number is 0-indexed with respect to the window coordinates,
        # but 1-indexed with respect to the folder contents (contents begin
        # on row 1).
        self.cursor = 1

        curses.curs_set(0)
        curses.wrapper(self.run)

    def run(self, _):
        """Run the TUI."""
        self.reload()
        while True:
            self.display()

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
        self.local.win.border()
        self.remote.win.border()
        self.local.win.addstr(0, 4, " [ %s ] " % self.local.folder.path)
        self.remote.win.addstr(0, 4, " [ %s ] " % self.remote.folder.uri)

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
        self.local.reload(self.args)
        try:
            self.remote.contents = self.remote.folder.contents(self.args)
        except ValueError:
            self.remote.contents = None
        self.local.contents = self.local.folder.contents(self.args)
        self.refresh()

    def display(self):
        """Display the contents of the working directories on screen."""
        self.local.display()
        self.remote.display()
        self.active.highlight(self.cursor)
        self.refresh()


class WorkingDirectory:
    """A working directory being displayed on screen."""
    def __init__(self, folder, win):
        self.folder = folder  # RemoteFolder or LocalFolder.
        self.win = win  # ncurses window.
        self.contents = None  # None until TUI.reload is called.
        self.offset = 0  # Start index of what's on screen.
        self.length = 0  # Number of items in contents.

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
            for i, entry in enumerate(self.contents):
                y = i + 1  # Start underneath the border.
                if y >= ymax - 1:  # Leave a border space at the bottom.
                    break
                if (  # Looks like a type hierarchy redesign is in order...
                        isinstance(entry, pdbox.models.RemoteFile) or
                        isinstance(entry, pdbox.models.LocalFile)
                ):
                    display_str = entry.name
                else:
                    display_str = "%s/" % entry.name
                self.win.addstr(y, 2, display_str)

    def reload(self, args):
        """Reload the contents of this directory."""
        try:
            self.contents = self.folder.contents(args)
        except:
            self.contents = None
            self.length = 0
        else:
            self.length = len(self.contents)
        finally:
            self.offset = 0  # Reset to the top of the folder.

    def highlight(self, i):
        """Highlight the ith entry in the window. i is 1-indexed."""
        if not self.contents or i > len(self.contents):
            return
        self.win.addstr(i, 2, self.win.instr(i, 2), curses.A_REVERSE)
