import asyncio
import logging
import os
import re
import sys
import time
import traceback
import inspect as _insp
from typing import (
    Any,
    Callable,
    Dict,
    Optional as Opt,
    Tuple,
    TypeVar,
    Union,
    Iterable,
    Coroutine,
)
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
        if val in ['TRUE', 'FALSE']:
            curval = val == 'TRUE'

    return curval


def trunc_str(
    tstr: Any, max_length: Opt[Union[int, None]] = TRUNC_STR_LEN
) -> str:
    """Truncates a string if its length exceeds the specified maximum length.
    If the string is truncated, it appends '...' to indicate the truncation. If
    no max_length is specified, the string is returned as-is. If a non-str is
    passed, it is cast to str before truncating.

    Args:
        tstr (Any): The object/str to truncate.
        max_length (Opt[int | None]): The maximum length of the truncated str
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
    max_str_len: Opt[int] = TRUNC_STR_LEN,
) -> str:
    """
    Creates the log message for entering a function.

    Args:
        func (Callable): The function being logged or its name.
        args (tuple): The arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.
        log_args (bool): Should the arguments be logged? Defaults to True.
        max_str_len (Opt[int]): The maximum length of the logged arguments.
            Defaults to 1000.

    Returns:
        str: The enter log message.
    """
    if not isinstance(func, str):
        fname = func.__name__
        fname = (
            'async %s' % fname if _insp.iscoroutinefunction(func) else fname
        )
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
    func: Union[Callable, Coroutine],
    args: tuple,
    kwargs: dict,
    result: any,
    start_time: Opt[float] = None,
    log_args: bool = True,
    log_return: bool = True,
    single_msg: bool = False,
    max_str_len: Opt[int] = TRUNC_STR_LEN,
) -> str:
    """Creates the 2nd log message containing the return value of the function
    and/or the execution time of the function and/or the function args if single_msg
    is True

    Args:
        func (Callable | str): The function being logged or its name.
        args (tuple): The arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.
        result (any): The return value of the function.
        start_time (Opt[float]): The time the function started executing.
            Defaults to None.
        log_args (bool): Should the arguments be logged? Defaults to True.
        log_return (bool): Should the return value be logged? Defaults to True.
        single_msg (bool): Should the enter and exit log messages be combined into
            a single message? Defaults to False.
        max_str_len (Opt[int]): The maximum length of the logged arguments.

    Returns:
        str: The exit log message.
    """

    if not isinstance(func, str):
        fname = '%s()' % func.__name__
        if _insp.iscoroutinefunction(func):
            fname = 'async %s' % fname
            exec_time = (
                asyncio.get_event_loop().time() - start_time
                if start_time
                else None
            )
        else:
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


def loglevel_int(level: Union[int, str] = logging.DEBUG) -> int:
    """
    Returns the logging level as an int.

    Args:
        level (Union[int, str]]): The logging level to use.
            Defaults to logging.DEBUG.

    Returns:
        int: The logging level as an int.
    """
    if level is None:
        return logging.DEBUG
    elif isinstance(level, str):
        return logging.getLevelName(level.upper())
    return int(level)


def decide_logfunc(
    use_logger: Opt[Union[logging.Logger, str]] = None
) -> Callable:
    """Decides whether to use logging.log or logger.log based on the use_logger
    parameter.

    Args:
        use_logger (Opt[Union[logging.Logger, str]]): logger/logger name
            to use for logging. Defaults to None. If None, logging.log is used.

    Returns:
        Callable: The function to use for logging.
    """
    if use_logger is None:
        return logging.log
    elif isinstance(use_logger, str):
        return logging.getLogger(use_logger).log
    return use_logger.log


def print_or_log(
    logmsg: str,
    level: Opt[Union[int, str]] = logging.DEBUG,
    use_print: bool = False,
    use_logger: Opt[logging.Logger] = None,
    log_stack_info: bool = False,
) -> Union[Callable, None]:
    """Prints or logs the log message with improved logic for LOGF_USE_PRINT,
    LOGF_LEVEL, and LOGF_PRINT_ALL environment variables.
    Args:
        logmsg (str): The log message to print or log.
        level (Opt[Union[int, str]]): The logging level to use.
            Defaults to logging.INFO.
        use_print (bool): Should the log messages be printed instead of logged?
            Default False
        use_logger (logging.Logger): The logger to use for logging.
            Defaults to None. If None, logging.log is used.
        log_stack_info (bool): stack_info kwarg for logging.log
            Defaults to False
    Returns:
        Callable: The function used to print/log
    """
    level_int = loglevel_int(level)
    env_level_int = loglevel_int(get_evar('LOGF_LEVEL', 'DEBUG'))

    # if level is lower than env_level, don't print/log
    if env_level_int - level_int > 0:
        return None
    elif use_print:
        print(logmsg)
        return print

    use_log_func = decide_logfunc(use_logger)
    use_log_func(
        level_int, logmsg, stack_info=log_stack_info
    )
    return use_log_func


def parse_logmsg(msg: str) -> Dict[str, str]:
    """Parses a log message into a dictionary. Assuming the log message
    follows the default log message format of:
        name() | (args) {kwargs}
        name() 0.0001s | result
    """
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
