import logging
from random import choice

from typing import Any, Callable, Dict, Optional as Opt, Tuple, Union
from .config import EVARS, ID_CHARS, ID_LEN
from .msgs import MSG_FORMATS
from .defaults import TRUNC_STR_LEN


def build_argstr(
    args: Tuple, kwargs: Dict, max_length: Union[int, None]
) -> str:
    """formats the args and kwargs into a string for logging"""
    if args:
        argskwargs = '(%s) ' % ', '.join(
            [trunc_str(a, max_length) for a in args]
        )
    else:
        argskwargs = ''

    if kwargs:
        argskwargs += '{%s}' % ', '.join(
            [
                '%s=%s' % (k, trunc_str(kwargs.get(k), max_length))
                for k in kwargs
            ]
        )

    return argskwargs


def trunc_str(tstr: Any, max_length: Union[int, None]) -> str:
    """Truncates a string if its length exceeds the specified maximum length.
    If the string is truncated, it appends '...' to indicate the truncation. If
    no max_length is specified, the string is returned as-is. If a non-str is
    passed, it is cast to str before truncating.

    `tstr (Any): The object/str to truncate.
    ~max_length (Opt[int | None]): The maximum length of the truncated str
        Defaults to 1000.

    Returns:
        str: The truncated string.
    """
    if not isinstance(tstr, str):
        try:
            tstr = str(tstr)
        except Exception as e:
            tstr = '[LOGF STR ERROR: {}]'.format(e)

    if max_length is None or len(tstr) < max_length:
        return tstr
    else:
        return tstr[0:max_length] + '...'


def loglevel_int(level: Union[int, str] = logging.DEBUG) -> int:
    """Returns the logging level as an int.
    ~level (Union[int, str]]): The logging level to use.
        Defaults to logging.DEBUG.
    -> int: The logging level as an int.
    """
    if level is None:
        return logging.DEBUG
    elif isinstance(level, str):
        return logging.getLevelName(level.upper())
    return int(level)


def handle_log(
    logmsg: str,
    level: Opt[Union[int, str]] = None,
    use_logger: Opt[logging.Logger] = None,
    log_stack_info: bool = False,
) -> Union[Callable, None]:
    """Prints or logs the log message with improved logic for LOGF_USE_PRINT,
    LOGF_LEVEL, and LOGF_PRINT_ALL environment variables.
    `logmsg (str): The log message to print or log.
    ~level (Opt[Union[int, str]]): The logging level to use.
        Defaults to logging.INFO.
    ~use_logger (logging.Logger): The logger to use for logging.
        Defaults to None. If None, logging.log is used.
    ~log_stack_info (bool): stack_info kwarg for logging.log
        Defaults to False`
    -> Callable: The function used to print/log
    """
    level_int = loglevel_int(level) if level is not None else logging.DEBUG

    logfunc = logging.log if use_logger is None else use_logger.log
    logfunc(level_int, logmsg, stack_info=log_stack_info)

    return logfunc


def identifier(len=ID_LEN, chars=ID_CHARS) -> str:
    """Generates a random identifier string of a specified length.
    ~len: the length of the identifier
    ~chars: the characters to choose from
    -> str: the msg with the identifier inserted
    """

    return ''.join(choice(chars) for _ in range(len))


def build_fname(f: Callable) -> str:
    try:
        fname = f.__qualname__
    except:
        try:
            fname = f.__name__
        except:
            fname = 'NO_FUNC_NAME'
    if fname.find('<locals>.') != -1:
        if hasattr(f, '__qualname__'):
            fname = f.__qualname__.split('<locals>.')[-1]
        else:
            fname = f.__name__.split('<locals>.')[-1]
    return fname
