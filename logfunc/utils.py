import asyncio
import logging
import os
import re
import sys
import time
import traceback
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

from .config import TRUNC_STR_LEN


def get_evar(evar: str, curval: any) -> any:
    """Returns the appropriately typed value for a given env var for the @logf decorator.

    Args:
        evar (str): The environment variable name.
        curval (any): The current value that will be overriden if a valid evar is found.

    Returns:
        any: what to use for the value for the equivalent parameter LOGF_x evar is referring to.
    """
    val = os.environ.get(evar, None)
    if val is None:
        return curval

    if evar == 'LOGF_LEVEL':  # int/str
        try:
            curval = int(val)
        except ValueError:
            val = str(val).upper()
            if val in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                curval = val
    elif evar == 'LOGF_MAX_STR_LEN':  # int/none
        try:
            curval = int(val)
        except ValueError:
            if str(val).upper() == 'NONE':
                curval = None
    elif evar in ['LOGF_SINGLE_MSG', 'LOGF_USE_PRINT']:
        val = str(val).upper()
        if val == 'TRUE':
            curval = True
        elif val == 'FALSE':
            curval = False
    return curval


def trunc_str(
    tstr: Any, max_length: Optional[Union[int, None]] = TRUNC_STR_LEN
) -> str:
    """Truncates a string if its length exceeds the specified maximum length.
    If the string is truncated, it appends '...' to indicate the truncation. If
    no max_length is specified, the string is returned as-is. If a non-str is
    passed, it is cast to str before truncating.

    Args:
        tstr (Any): The object/str to truncate.
        max_length (Optional[int | None]): The maximum length of the truncated string.
            Defaults to 1000.

    Returns:
        str: The truncated string.
    """
    if not isinstance(tstr, str):
        tstr = str(tstr)

    if max_length is None or len(tstr) < max_length:
        return tstr
    else:
        return tstr[0:max_length] + '...'


def func_args_str(
    func: Union[Callable, str],
    args: tuple,
    kwargs: dict,
    log_args: bool = True,
    max_str_len: Optional[int] = TRUNC_STR_LEN,
) -> str:
    """
    Creates the log message for entering a function.

    Args:
        func (Callable): The function being logged or its name.
        args (tuple): The arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.
        log_args (bool): Should the arguments be logged? Defaults to True.
        max_str_len (Optional[int]): The maximum length of the logged arguments.
            Defaults to 1000.

    Returns:
        str: The enter log message.
    """
    if not isinstance(func, str):
        fname = func.__name__
        fname = 'async %s' % fname if iscoroutinefunction(func) else fname
    else:
        fname = func

    if log_args:
        argstr = ' | %s %s' % (
            trunc_str(args, max_length=max_str_len),
            trunc_str(kwargs, max_length=max_str_len),
        )
    else:
        argstr = ''

    return '%s()%s' % (fname, argstr)


def func_return_str(
    func: Callable,
    args: tuple,
    kwargs: dict,
    result: any,
    start_time: Optional[float] = None,
    log_args: bool = True,
    log_return: bool = True,
    single_msg: bool = False,
    max_str_len: Optional[int] = TRUNC_STR_LEN,
) -> str:
    """Creates the 2nd log message containing the return value of the function
    and/or the execution time of the function and/or the function args if single_msg
    is True

    Args:
        func (Callable | str): The function being logged or its name.
        args (tuple): The arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.
        result (any): The return value of the function.
        start_time (Optional[float]): The time the function started executing.
            Defaults to None.
        log_args (bool): Should the arguments be logged? Defaults to True.
        log_return (bool): Should the return value be logged? Defaults to True.
        single_msg (bool): Should the enter and exit log messages be combined into
            a single message? Defaults to False.
        max_str_len (Optional[int]): The maximum length of the logged arguments.

    Returns:
        str: The exit log message.
    """

    if not isinstance(func, str):
        if iscoroutinefunction(func):
            fname = 'async %s()' % func.__name__
            exec_time = (
                asyncio.get_event_loop().time() - start_time
                if start_time
                else None
            )
        else:
            fname = '%s()' % func.__name__
            exec_time = time.time() - start_time if start_time else None
    else:
        exec_time = time.time() - start_time if start_time else None
        fname = '%s()' % func

    logmsg = fname
    if exec_time is not None:
        logmsg = '{} {:.5f}s'.format(logmsg, exec_time)

    if single_msg and log_args:
        logmsg = '{} | {} {}'.format(logmsg, args, kwargs)

    if log_return:
        logmsg = '{} | {}'.format(logmsg, trunc_str(result, max_str_len))

    return logmsg


def loglevel_int(level: Optional[Union[int, str]] = logging.DEBUG) -> int:
    """
    Returns the logging level as an int.

    Args:
        level (Optional[Union[int, str]]): The logging level to use. Defaults to logging.DEBUG.

    Returns:
        int: The logging level as an int.
    """
    if isinstance(level, str):
        level_int = logging.getLevelName(level.upper())
    else:
        level_int = int(level)
    return level_int


def print_or_log(
    logmsg: str,
    level: Optional[Union[int, str]] = logging.DEBUG,
    use_print: bool = False,
    use_logger: Optional[logging.Logger] = None,
) -> None:
    """
    Prints or logs the log message.

    Args:
        logmsg (str): The log message to print or log.
        level (Optional[Union[int, str]]): The logging level to use.
            Defaults to logging.DEBUG.
        use_print (bool): Should the log message be printed instead of logged?
            Defaults to False.
        use_logger (Optional[logging.Logger]): The logger to use for logging.
            Defaults to None. If None, logging.log is used.
    """
    level_int = loglevel_int(level)
    env_level_str = os.environ.get('LOGF_LEVEL', 'DEBUG')
    env_level_int = loglevel_int(env_level_str)

    # if LOGF_PRINT_ALL is set to True
    # always print the log message regardless of the log level
    print_all = get_evar('LOGF_PRINT_ALL', False)

    if use_print:
        if level_int >= env_level_int or print_all:
            print(logmsg)
    else:
        if use_logger is None:
            logging.log(level_int, logmsg)
        else:
            use_logger.log(level_int, logmsg)


def parse_logmsg(msg: str) -> Dict[str, str]:
    pattern = (
        r'(?:(?P<loglevel>\w+):(?P<loggername>\w+):)?'
        r'(?P<funcname>\w+\(\))'
        r'(?: (?P<exectime>\d+\.\d+)s)?(?: \| '
        r'(?P<argstr>\(.*?\) \{.*?\}))?(?: \| (?P<result>.+))?'
    )

    rdict = {
        'loglevel': '',
        'loggername': '',
        'funcname': '',
        'exectime': '',
        'argstr': '',
        'result': '',
    }

    rmatch = re.match(pattern, msg)
    if not rmatch:
        return rdict

    for k, v in rmatch.groupdict().items():
        if v is not None:
            rdict[k] = v
    return rdict
