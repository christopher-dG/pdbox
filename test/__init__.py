import logging
import os
import pdbox


if "PDBOX_DEBUG" in os.environ:
    pdbox._logger.setLevel(logging.DEBUG)


class FakeArgs:
    """Helper class to simulate the Namespace passed around from argparse."""
    def __init__(self, **kwargs):
        self.src = kwargs["src"] if "src" in kwargs else ""
        self.dst = kwargs["dst"] if "dst" in kwargs else ""
        self.quiet = kwargs["quiet"] if "quiet" in kwargs else False
        self.only_show_errors = kwargs[  # I love PEP8.
            "only_show_errors"] if "only_show_errors" in kwargs else False
        self.dryrun = kwargs["dryrun"] if "dryrun" in kwargs else True
