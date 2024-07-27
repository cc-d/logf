import asyncio as aio
import inspect as _insp

import time

from functools import wraps
from typing import (
    Any,
    Callable as Call,
    Optional as Opt,
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
    build_fname as b_fname,
)
from .config import EVARS, MSG_FORMATS, Cfg

from .defaults import TRUNC_STR_LEN, EXEC_TIME_FMT
from . import defaults as _def


from . import msgs


def logf(
    level: Opt[U[int, str]] = _def.LEVEL,
    log_args: bool = _def.LOG_ARGS,
    log_return: bool = _def.LOG_RETURN,
    max_str_len: U[int, None] = _def.MAX_STR_LEN,
    log_exec_time: bool = _def.LOG_EXEC_TIME,
    single_msg: bool = _def.SINGLE_MSG,
    use_print: bool = _def.USE_PRINT,
    use_logger: Opt[U[Logger, str]] = _def.USE_LOGGER,
    log_stack_info: bool = _def.LOG_STACK_INFO,
    identifier: bool = _def.IDENTIFIER,
    refresh: bool = _def.REFRESH,
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
        refresh=refresh,
    )

    # if param use_logger is a string, convert it to a logger
    if cfg.use_logger is not None and not isinstance(cfg.use_logger, Logger):
        cfg.use_logger = getLogger(use_logger)

    def wrapper(func: Call[..., Any]) -> U[Call[..., Any], Co[Any, Any, Any]]:
        fname = b_fname(func)
        if cfg.refresh:
            cfg.refresh_vars()

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


def _msg_enter(func_name: str, args_str: str, cfg: Cfg, id: str) -> None:
    """Handles logging of the enter message for decorated functions."""
    if cfg.level is not None and cfg.logf_log_level is not None:
        if loglevel_int(cfg.level) < loglevel_int(cfg.logf_log_level):
            return

    if id:
        id_func_name = '{} {}'.format(id, func_name)
    else:
        id_func_name = ' {}'.format(func_name)

    logmsg = MSG_FORMATS.enter.format(
        args_str=args_str, id_func_name=id_func_name
    )
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

    if (
        result is None
        and func_name.endswith('__init__')
        and not func_name.startswith('__init__')
    ):
        return
    if cfg.level is not None and cfg.logf_log_level is not None:
        if loglevel_int(cfg.level) < loglevel_int(cfg.logf_log_level):
            return

    if not end_time and cfg.log_time:
        end_time = '0.0s'

    logmsg = msgs.exit_msg(
        cfg.single,
        func_name,
        end_time,
        args_str,
        trunc_str(result, cfg.max_str) if cfg.log_return else '',
        func_id=id if cfg.identifier and id is not None else ' ',
    )

    if cfg.use_print:
        print(logmsg)
    else:
        handle_log(
            logmsg, cfg.level, cfg.use_logger, log_stack_info=cfg.log_stack
        )


def _endtime(start_time: U[float, None], end_time: U[float, None]) -> str:
    """Returns the time elapsed since the start time."""
    if start_time is None:
        return ''
    diff_str = EXEC_TIME_FMT % (end_time - start_time) + 's'
    for c in diff_str:
        if c not in {'0', '.', 's'}:
            return diff_str
    return ''


def _enter(
    func_name: str, args: Tuple, kwargs: Dict, cfg: Cfg, id: U[str, None]
) -> str:
    """Handles the enter for decorated functions and returns argstr"""
    _exclude_self = False

    if func_name.endswith('__init__') and not func_name.startswith('__init__'):
        if (
            len(args) > 0
            and isinstance(args[0], object)
            and func_name.split('.')[-2] in args[0].__class__.__name__
        ):
            _exclude_self = True

    argstr = build_argstr(
        args if not _exclude_self else args[1:], kwargs, cfg.max_str
    )

    if not cfg.single:
        _msg_enter(func_name, argstr, cfg, id)

    return argstr
