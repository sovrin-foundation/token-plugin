import logging
import builtins
import importlib
import sys


def mute_loggers(*, lvl=logging.WARNING, protected=[]):
    def filter(record):
        if record.levelno > lvl or record.name in protected:
            return 1
        else:
            return 0

    root_logger = logging.getLogger()
    old_handlers = _remove_current_handlers(root_logger)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(filter)
    logging.getLogger().addHandler(handler)

    # Unmute the loggers
    def unmute():
        map(root_logger.addHandler, old_handlers)
        root_logger.removeHandler(handler)

    return unmute


def mute_print():
    original_print = builtins.print
    _overload_print_function(lambda *args: 1)

    # Unumute print function
    return lambda: _overload_print_function(original_print)


def _overload_print_function(func):
    builtins.print = func
    importlib.reload(builtins)


def _remove_current_handlers(logger):
    current_handlers = list(logger.handlers)

    for h in current_handlers:
        logger.removeHandler(h)

    return current_handlers
