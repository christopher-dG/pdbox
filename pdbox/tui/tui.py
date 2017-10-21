import argparse
import curses
import curses.textpad
import math
import os
import pdbox
import socket


class TUI:
    """A TUI client for pdbox."""
    def __init__(self, args):
        # Working directories.
        self.curlocal = pdbox.models.get_local(os.curdir)
        self.curremote = pdbox.models.get_remote("/")

        # Local file view.
        self.local = curses.initscr()
        self.local.resize(curses.LINES - 1, math.ceil(curses.COLS / 2))
        self.local.mvwin(1, 0)

        #  Remote file view.
        self.remote = curses.newwin(
            curses.LINES - 1,
            int(curses.COLS / 2),
            1,
            math.ceil(curses.COLS / 2),
        )

        # Status/context bar.
        self.status = curses.newwin(1, curses.COLS, 0, 0)

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

        curses.curs_set(0)
        curses.wrapper(self.run)

    def run(self, _):
        """Run the TUI."""
        while True:
            self.refresh()
            # TODO

    def getinput(self, prompt):
        # Shorten the middle windows by one line to show the input bar.
        y, x = self.local.getmaxyx()
        self.local.resize(y - 1, x)
        y, x = self.remote.getmaxyx()
        self.remote.resize(y - 1, x)

        inputbar = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        textpad = curses.textpad.Textbox(inputbar)

        if not prompt.endswith(" "):
            prompt += " "
        inputbar.addstr(0, 1, prompt)
        self.refresh(inputbar)

        cmd = textpad.edit()[len(prompt) + 1:]

        y, x = self.local.getmaxyx()
        self.local.resize(y + 1, x)
        y, x = self.remote.getmaxyx()
        self.remote.resize(y + 1, x)

        # Erase the bottom border of the shortened windows.
        self.local.move(self.local.getmaxyx()[0] - 2, 0)
        self.local.deleteln()
        self.remote.move(self.remote.getmaxyx()[0] - 2, 0)
        self.remote.deleteln()

        self.refresh()
        return cmd

    def borders(self):
        self.local.border()
        self.remote.border()
        self.local.addstr(0, 4, " [ %s ] " % socket.gethostname())
        self.remote.addstr(0, 4, " [ Dropbox ] ")

    def refresh(self, *wins):
        """Refresh all windows."""
        self.borders()
        self.status.refresh()
        self.local.refresh()
        self.remote.refresh()
        for win in wins:
            win.refresh()
