import asyncio
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
)
from logging import getLogger, Logger

from .utils import loglevel_int, handle_log, trunc_str, last_traceback
from .config import Env, EVARS, MSG_FORMATS

from .defaults import TRUNC_STR_LEN


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
    **kwargs,
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
        Callable[..., Callable[..., Any]]: The executed decorated function.
    """

    _env = Env()
    # for backwards compatability, override log_exec_time using
    # the measure_time kwarg if present
    if 'measure_time' in kwargs:
        log_exec_time = kwargs['measure_time']

    for ev in EVARS:
        _ev = getattr(_env, ev)
        if _ev is not None:
            if ev == 'LOGF_MAX_STR_LEN':
                max_str_len = None if _ev.lower() == 'none' else int(_ev)
            elif ev == 'LOGF_SINGLE_MSG':
                single_msg = _ev.lower() == 'true'
            elif ev == 'LOGF_USE_PRINT':
                use_print = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_ARGS':
                log_args = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_RETURN':
                log_return = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_EXEC_TIME':
                log_exec_time = _ev.lower() == 'true'
            elif ev == 'LOGF_USE_LOGGER':
                use_logger = getLogger(_ev) if _ev else None
            elif ev == 'LOGF_STACK_INFO':
                log_stack_info = _ev.lower() == 'true'
            elif ev == 'LOGF_LOG_EXCEPTION':
                log_exception = _ev.lower() == 'true'
            elif ev == 'LOGF_SINGLE_EXCEPTION':
                single_exception = _ev.lower() == 'true'

    # if param use_logger is a string, convert it to a logger
    if use_logger is not None and not isinstance(use_logger, Logger):
        use_logger = getLogger(use_logger)

    def wrapper(func: Call[..., Any]) -> U[Call[..., Any], Co[Any, Any, Any]]:

        # ensure only last traceback is logged

        # handle async funcs
        if log_exception and single_exception:
            if hasattr(_local, 'depth'):
                _local.depth += 1
            else:
                _local.depth = 1

        if _insp.iscoroutinefunction(func):

            @wraps(func)
            async def decorator(*args, **kwargs) -> Any:

                start_time = (
                    asyncio.get_event_loop().time() if log_exec_time else None
                )
                if log_args:
                    func_args = str(args)
                    func_kwargs = str(kwargs)
                    args_str = MSG_FORMATS.argstr.format(
                        func_args=func_args, func_kwargs=func_kwargs
                    )
                else:
                    args_str = ''

                if not single_msg:
                    logmsg = MSG_FORMATS.enter.format(
                        func_name=func.__name__, args_str=args_str
                    )

                    if use_print:
                        print(logmsg)
                    else:
                        handle_log(
                            logmsg,
                            level,
                            use_logger,
                            log_stack_info=log_stack_info,
                        )

                if log_exception:
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as e:
                        if hasattr(_local, 'depth') and _local.depth > 1:
                            pass
                        elif use_print:
                            format_exception(e, value=e, tb=e.__traceback__)
                        else:
                            logmsg = MSG_FORMATS.error.format(
                                func_name=func.__name__,
                                exc_type=type(e).__name__,
                                exc_val=e,
                            )
                            handle_log(
                                logmsg, 'ERROR', use_logger, log_exception
                            )
                        raise e
                    finally:
                        if hasattr(_local, 'depth'):
                            _local.depth -= 1
                            # print('finally', _local.depth)
                            if _local.depth == 0:
                                del _local.depth
                else:
                    result = await func(*args, **kwargs)

                if single_msg:
                    logmsg = MSG_FORMATS.single.format(
                        func_name=func.__name__,
                        exec_time=(
                            '%.5f'
                            % (asyncio.get_event_loop().time() - start_time)
                            if log_exec_time
                            else ''
                        ),
                        args_str=args_str,
                        result=(
                            trunc_str(result, max_str_len)
                            if log_return
                            else ''
                        ),
                    )
                else:
                    logmsg = MSG_FORMATS.exit.format(
                        func_name=func.__name__,
                        exec_time=(
                            '%.5f'
                            % (asyncio.get_event_loop().time() - start_time)
                            if log_exec_time
                            else ''
                        ),
                        result=(
                            trunc_str(result, max_str_len)
                            if log_return
                            else ''
                        ),
                    )

                if use_print:
                    print(logmsg)
                else:
                    handle_log(
                        logmsg,
                        level,
                        use_logger,
                        log_stack_info=log_stack_info,
                    )

                return result

        # handle sync funcs
        else:

            @wraps(func)
            def decorator(*args, **kwargs) -> Any:

                # Start the timer if required and execute the function.
                start_time = time.time() if log_exec_time else None
                if log_args:
                    func_args = str(args)
                    func_kwargs = str(kwargs)
                    args_str = MSG_FORMATS.argstr.format(
                        func_args=func_args, func_kwargs=func_kwargs
                    )
                else:
                    args_str = ''

                # Log the enter message if required
                if not single_msg:
                    logmsg = MSG_FORMATS.enter.format(
                        func_name=func.__name__, args_str=args_str
                    )
                    if use_print:
                        print(logmsg)
                    else:
                        handle_log(
                            logmsg,
                            level,
                            use_logger,
                            log_stack_info=log_stack_info,
                        )

                if log_exception:
                    try:

                        result = func(*args, **kwargs)
                    except Exception as e:
                        if hasattr(_local, 'depth') and _local.depth != 1:
                            pass
                        elif use_print:
                            format_exception(e, value=e, tb=e.__traceback__)
                        else:
                            logmsg = MSG_FORMATS.error.format(
                                func_name=func.__name__,
                                exc_type=type(e).__name__,
                                exc_val=e,
                            )
                            handle_log(
                                logmsg,
                                'ERROR',
                                use_logger,
                                log_exception=log_exception,
                            )

                        raise
                    finally:
                        if hasattr(_local, 'depth'):
                            _local.depth -= 1
                            # print('finally', _local.depth)
                            if _local.depth == 0:
                                del _local.depth
                else:
                    result = func(*args, **kwargs)

                if single_msg:
                    logmsg = MSG_FORMATS.single.format(
                        func_name=func.__name__,
                        exec_time=('%.5f' % (time.time() - start_time)),
                        args_str=args_str,
                        result=(
                            trunc_str(result, max_str_len)
                            if log_return
                            else ''
                        ),
                    )
                else:
                    logmsg = MSG_FORMATS.exit.format(
                        func_name=func.__name__,
                        exec_time=(
                            '%.5f' % (time.time() - start_time)
                            if log_exec_time
                            else ''
                        ),
                        result=(
                            trunc_str(result, max_str_len)
                            if log_return
                            else ''
                        ),
                    )

                if use_print:
                    print(logmsg)
                else:
                    handle_log(
                        logmsg,
                        level,
                        use_logger,
                        log_stack_info=log_stack_info,
                    )

                return result

        return decorator

    return wrapper
