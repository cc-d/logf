import asyncio as aio
import inspect as _insp
import os
import random
import re
import string
import sys
import time
import threading
from traceback import format_exception
from datetime import datetime
from functools import wraps
from typing import (
    Any,
    Callable as Call,
    Optional as Opt,
    TypeVar,
    Union as U,
    Dict,
    Iterable,
    Coroutine as Co,
    List,
    Tuple,
)
from logging import getLogger, Logger

from .utils import loglevel_int, handle_log, trunc_str, build_argstr
from .config import Env, EVARS, MSG_FORMATS

from .defaults import TRUNC_STR_LEN

from . import msgs


# Thread-local storage to track depth of logf calls per thread
_local = threading.local()


def logf(
    level: Opt[U[int, str]] = None,
    log_args: bool = True,
    log_return: bool = True,
    max_str_len: U[int, None] = TRUNC_STR_LEN,
    log_exec_time: bool = True,
    single_msg: bool = False,
    use_print: bool = False,
    use_logger: Opt[U[Logger, str]] = None,
    log_stack_info: bool = False,
    log_exception: bool = True,
    single_exception: bool = True,
    **kwargs
) -> U[Call[..., Any], Co[Any, Any, Any]]:
    """A highly customizable function decorator meant for effortless
    leave-and-forget logging of function calls, both synchronous and
    asynchronous. Logs the function name, arguments, return value and
    execution time.
    Args:
        level (Optional[Union[int, str]]): The logging level to use.
            Defaults to DEBUG.
        log_args (bool): Should the function arguments be logged?
            Defaults to True.
        log_return (bool): Should function return be logged?
            Defaults to True.
        max_str_len (Optional[int]): The maximum length of the logged arguments
            Defaults to 500 otherwise LOGF_MAX_STR_LEN env var is used.
        log_exec_time (bool): Should the function execution time be measured?
            Defaults to True.
        single_msg (bool): Should both enter and exit log messages be combined
            into a single message? Default False
        use_print (bool): Should the log messages be printed instead of logged?
            Default False
        use_logger (Optional[Union[Logger, str]]): logger/logger name
            to use for  Defaults to None. If None, log is used.
        log_stack_info (bool): stack_info kwarg for log
            Can be overridden by the evar LOGF_STACK_INFO.
            Defaults to False
        log_exception (bool): Should exceptions be logged? Defaults to True.
        single_exception (bool): Should only the last exception be logged?
            Defaults to True.
    Returns:
        The executed decorated function or coroutine result.
    """

    _env = Env()
    # shorthands, maintaining backwards compatability
    max_str, log_time, single = max_str_len, log_exec_time, single_msg
    log_ex, single_ex = log_exception, single_exception
    log_stack = log_stack_info

    # for backwards compatability, override log_exec_time using
    # the measure_time kwarg if present
    if 'measure_time' in kwargs:
        log_time = kwargs['measure_time']

    for ev in EVARS:
        _ev = getattr(_env, ev)
        if _ev is not None:
            if ev == 'LOGF_MAX_STR_LEN':
                max_str = None if _ev.lower() == 'none' else int(_ev)
            elif ev == 'LOGF_SINGLE_MSG':
                single = _ev.lower() == 'true'
            elif ev == 'LOGF_USE_PRINT':
                use_print = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_ARGS':
                log_args = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_RETURN':
                log_return = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_EXEC_TIME':
                log_time = _ev.lower() == 'true'
            elif ev == 'LOGF_USE_LOGGER':
                use_logger = getLogger(_ev) if _ev else None
            elif ev == 'LOGF_STACK_INFO':
                log_stack = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_EXCEPTION':
                log_ex = _ev.lower() == 'true'
            elif ev == 'LOGF_SINGLE_EXCEPTION':
                single_ex = _ev.lower() == 'true'

    # if param use_logger is a string, convert it to a logger
    if use_logger is not None and not isinstance(use_logger, Logger):
        use_logger = getLogger(use_logger)

    def wrapper(func: Call[..., Any]) -> U[Call[..., Any], Co[Any, Any, Any]]:

        fname = func.__name__

        # ensure only last traceback is logged
        if log_ex and single_ex:
            if hasattr(_local, 'depth'):
                _local.depth += 1
            else:
                _local.depth = 1

        # this is used to create the enter args str
        args_enter = (
            max_str,
            log_args,
            single,
            use_print,
            use_logger,
            log_stack,
            level,
        )

        if _insp.iscoroutinefunction(func):

            @wraps(func)
            async def decorator(*args, **kwargs) -> Any:
                _start = aio.get_event_loop().time() if log_time else None
                argstr = _enter(*(fname, args, kwargs), *args_enter)
                if log_ex:
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as e:
                        _ex(e, fname, use_print, use_logger, log_ex)
                        raise e
                    finally:
                        _finally()
                else:
                    result = await func(*args, **kwargs)

                _msg_exit(
                    result,
                    single,
                    fname,
                    _endtime(_start, aio.get_event_loop().time()),
                    argstr,
                    use_print,
                    use_logger,
                    log_stack,
                    level,
                    max_str,
                    log_return,
                )

                return result

        # handle sync funcs
        else:

            @wraps(func)
            def decorator(*args, **kwargs) -> Any:
                _start = time.time() if log_time else None
                argstr = _enter(*(fname, args, kwargs), *args_enter)
                if log_ex:
                    try:

                        result = func(*args, **kwargs)
                    except Exception as e:
                        _ex(e, fname, use_print, use_logger, log_ex)
                        raise
                    finally:
                        _finally()
                else:
                    result = func(*args, **kwargs)

                _msg_exit(
                    result,
                    single,
                    fname,
                    _endtime(_start, time.time()),
                    argstr,
                    use_print,
                    use_logger,
                    log_stack,
                    level,
                    max_str,
                    log_return,
                )
                return result

        return decorator

    return wrapper


def _argstr(
    max_str: U[int, None],
    log_args: bool,
    single: bool,
    use_print: bool,
    use_logger: U[Logger, str, None],
    log_stack: bool,
    level: U[int, str, None],
    func_name: str,
    args: Tuple,
    kwargs: Dict,
) -> str:
    """Handles the enter for decorated functions and returns argstr"""
    argstr = build_argstr(args, kwargs, max_str, log_args)
    if not single:
        _msg_enter(func_name, argstr, use_print, use_logger, log_stack, level)
    return argstr


def _ex(
    e: Exception,
    func_name: str,
    use_print: bool,
    use_logger: U[Logger, str, None],
    log_ex: bool,
) -> None:
    """Handles logging of exceptions raised in decorated functions."""
    if hasattr(_local, 'depth') and _local.depth > 1:
        pass
    elif use_print:
        format_exception(e, value=e, tb=e.__traceback__)
    else:
        logmsg = MSG_FORMATS.error.format(
            func_name=func_name, exc_type=type(e).__name__, exc_val=e
        )
        handle_log(logmsg, 'ERROR', use_logger, log_ex)


def _msg_enter(
    func_name: str,
    args_str: str,
    use_print: bool,
    use_logger: U[Logger, str, None],
    log_stack: bool,
    level: U[int, str, None],
) -> None:
    """Handles logging of the enter message for decorated functions."""
    logmsg = MSG_FORMATS.enter.format(func_name=func_name, args_str=args_str)
    if use_print:
        print(logmsg)
    else:
        handle_log(logmsg, level, use_logger, log_stack_info=log_stack)


def _msg_exit(
    result: Any,
    single: bool,
    func_name: str,
    end_time: str,
    args_str: str,
    use_print: bool,
    use_logger: U[Logger, str, None],
    log_stack: bool,
    level: U[int, str, None],
    max_str: U[int, None],
    log_return: bool,
) -> None:
    """Handles logging of the exit message for decorated functions."""

    logmsg = msgs.exit_msg(
        single,
        func_name,
        end_time,
        args_str,
        trunc_str(result, max_str) if log_return else '',
    )
    if use_print:
        print(logmsg)
    else:
        handle_log(logmsg, level, use_logger, log_stack_info=log_stack)


def _finally():
    """DRY to handle conditional logging when multiple embedded logf calls"""
    if hasattr(_local, 'depth'):
        _local.depth -= 1
        if _local.depth <= 0:
            del _local.depth


def _endtime(start_time: U[float, None], end_time: U[float, None]) -> str:
    """Returns the time elapsed since the start time."""
    return '' if start_time is None else '%.5f' % (end_time - start_time)


def _enter(
    func_name: str,
    args: Tuple,
    kwargs: Dict,
    max_str: U[int, None],
    log_args: bool,
    single: bool,
    use_print: bool,
    use_logger: U[Logger, str, None],
    log_stack: bool,
    level: U[int, str, None],
) -> str:
    """Handles the enter for decorated functions and returns argstr"""
    argstr = build_argstr(args, kwargs, max_str, log_args)
    if not single:
        _msg_enter(func_name, argstr, use_print, use_logger, log_stack, level)
    return argstr
