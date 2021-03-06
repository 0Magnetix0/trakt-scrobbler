import sys
import threading

from queue import Queue
import confuse
from trakt_scrobbler import config, logger
from trakt_scrobbler.backlog_cleaner import BacklogCleaner
from trakt_scrobbler.player_monitors import collect_monitors
from trakt_scrobbler.scrobbler import Scrobbler
from trakt_scrobbler.trakt_interface import get_access_token


def register_exception_handler():
    """Exception handler to log all errors from threads."""
    def error_logger(*exc_info):
        logger.exception('Unhandled exception', exc_info=exc_info)

    sys.excepthook = error_logger

    # from http://stackoverflow.com/a/31622038
    """
    Workaround for `sys.excepthook` thread bug from:
    http://bugs.python.org/issue1230540
    Call once from the main thread before creating any threads.
    """

    init_original = threading.Thread.__init__

    def init(self, *args, **kwargs):
        init_original(self, *args, **kwargs)
        run_original = self.run

        def run_with_except_hook(*args2, **kwargs2):
            try:
                run_original(*args2, **kwargs2)
            except Exception:
                sys.excepthook(*sys.exc_info())
                return

        self.run = run_with_except_hook

    threading.Thread.__init__ = init


def main():
    register_exception_handler()
    assert get_access_token()
    scrobble_queue = Queue()
    backlog_cleaner = BacklogCleaner()
    scrobbler = Scrobbler(scrobble_queue, backlog_cleaner)
    scrobbler.start()

    allowed_monitors = config['players']['monitored'].get(confuse.StrSeq(default=[]))
    all_monitors = collect_monitors()

    unknown = set(allowed_monitors).difference(Mon.name for Mon in all_monitors)
    if unknown:
        logger.warning(f"Unknown player(s): {', '.join(unknown)}")

    for Mon in all_monitors:
        if Mon.name not in allowed_monitors:
            continue
        mon = Mon(scrobble_queue)
        if not mon or not mon._initialized:
            logger.warning(f"Could not start monitor for {Mon.name}")
            continue
        mon.start()


if __name__ == '__main__':
    main()
