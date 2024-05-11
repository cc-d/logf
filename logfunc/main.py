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

from .utils import (
    loglevel_int,
    handle_log,
    trunc_str,
    build_argstr,
    identifier as _get_id,
)
from .config import EVARS, MSG_FORMATS, Cfg

from .defaults import TRUNC_STR_LEN, EXEC_TIME_FMT

from . import msgs


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
    identifier: bool = True,
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
            Default: False
        identifier (bool): A unique identifier for enter/exits. Equivalent to
            evar LOGF_IDENTIFIER.
            Default: True
    Returns:
        The executed decorated function or coroutine result.
    """

    cfg = Cfg(
        level=level,
        max_str_len=max_str_len,
        log_exec_time=kwargs.get('measure_time', log_exec_time),
        single_msg=single_msg,
        log_stack_info=log_stack_info,
        use_print=use_print,
        log_args=log_args,
        log_return=log_return,
        use_logger=use_logger,
        identifier=identifier,
    )

    # if param use_logger is a string, convert it to a logger
    if cfg.use_logger is not None and not isinstance(cfg.use_logger, Logger):
        cfg.use_logger = getLogger(use_logger)

    def wrapper(func: Call[..., Any]) -> U[Call[..., Any], Co[Any, Any, Any]]:
        fname = func.__name__

        # ensure only last traceback is logged

        if _insp.iscoroutinefunction(func):

            @wraps(func)
            async def decorator(*args, **kwargs) -> Any:
                _id = _get_id() if cfg.identifier and not cfg.single else None

                _start = aio.get_event_loop().time() if cfg.log_time else None
                argstr = _enter(fname, args, kwargs, cfg, _id)
                result = await func(*args, **kwargs)

                _msg_exit(
                    result,
                    fname,
                    argstr,
                    _endtime(_start, aio.get_event_loop().time()),
                    cfg,
                    _id,
                )

                return result

        # handle sync funcs
        else:

            @wraps(func)
            def decorator(*args, **kwargs) -> Any:
                _id = _get_id() if cfg.identifier and not cfg.single else None
                _start = time.time() if cfg.log_time else None
                argstr = _enter(fname, args, kwargs, cfg, _id)
                result = func(*args, **kwargs)

                _msg_exit(
                    result,
                    fname,
                    _endtime(_start, time.time()),
                    argstr,
                    cfg,
                    _id,
                )
                return result

        return decorator

    return wrapper


def _msg_enter(
    func_name: str, args_str: str, cfg: Cfg, id: U[str, None]
) -> None:
    """Handles logging of the enter message for decorated functions."""
    if cfg.level is not None and cfg.logf_log_level is not None:
        if loglevel_int(cfg.level) < loglevel_int(cfg.logf_log_level):
            return

    logmsg = MSG_FORMATS.enter.format(func_name=func_name, args_str=args_str)

    if id is not None:

        logmsg = logmsg.replace('()', '()[%s]' % id, 1)

    if cfg.use_print:
        print(logmsg)
    else:
        handle_log(
            logmsg, cfg.level, cfg.use_logger, log_stack_info=cfg.log_stack
        )


def _msg_exit(
    result: Any,
    func_name: str,
    end_time: str,
    args_str: str,
    cfg: Cfg,
    id: U[str, None],
) -> None:
    """Handles logging of the exit message for decorated functions."""
    if cfg.level is not None and cfg.logf_log_level is not None:
        if loglevel_int(cfg.level) < loglevel_int(cfg.logf_log_level):
            return

    logmsg = msgs.exit_msg(
        cfg.single,
        func_name,
        end_time,
        args_str,
        trunc_str(result, cfg.max_str) if cfg.log_return else '',
    )
    if id is not None:
        logmsg = logmsg.replace('()', '()[%s]' % id, 1)

    if cfg.use_print:
        print(logmsg)
    else:
        handle_log(
            logmsg, cfg.level, cfg.use_logger, log_stack_info=cfg.log_stack
        )


def _endtime(start_time: U[float, None], end_time: U[float, None]) -> str:
    """Returns the time elapsed since the start time."""
    return (
        ''
        if start_time is None
        else (EXEC_TIME_FMT % (end_time - start_time)) + 's'
    )


def _enter(
    func_name: str, args: Tuple, kwargs: Dict, cfg: Cfg, id: U[str, None]
) -> str:
    """Handles the enter for decorated functions and returns argstr"""
    argstr = build_argstr(args, kwargs, cfg.max_str, cfg.log_args)
    if not cfg.single:
        _msg_enter(func_name, argstr, cfg, id)
    return argstr
