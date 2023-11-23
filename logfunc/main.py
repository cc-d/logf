import asyncio
import inspect
import logging
import os
import random
import re
import string
import sys
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from .config import TRUNC_STR_LEN
from .utils import (
    func_args_str,
    func_return_str,
    get_evar,
    loglevel_int,
    print_or_log,
    trunc_str,
)


def logf(
    level: Optional[Union[int, str]] = None,
    log_args: bool = True,
    log_return: bool = True,
    max_str_len: Optional[int] = TRUNC_STR_LEN,
    log_exec_time: bool = True,
    single_msg: bool = False,
    use_print: bool = False,
    use_logger: Optional[Union[logging.Logger, str]] = None,
    **kwargs
) -> Callable[..., Callable[..., Any]]:
    """A highly customizable function decorator meant for effortless
    leave-and-forget logging of function calls, both synchronous and
    asynchronous. Logs the function name, arguments, return value and
    execution time.

    Args:
        level (Optional[Union[int, str]]): The logging level to use.
            Defaults to logging.DEBUG.
        log_args (bool): Should the function arguments be logged?
            Defaults to True.
        log_return (bool): Should function return be logged?
            Defaults to True.
        max_str_len (Optional[int]): The maximum length of the logged arguments
            Defaults to 500 otherwise LOGF_MAX_STR_LEN env var is used.
        log_exec_time (bool): Should the function execution time be measured?
            Defaults to True.
        single_msg (bool): Should both enter and exit log messages be combined into a single message?
            Default False
        use_print (bool): Should the log messages be printed instead of logged?
            Default False
        use_logger (Optional[Union[logging.Logger, str]]): logger/logger name
            to use for logging. Defaults to None. If None, logging.log is used.

    Returns:
        Callable[..., Callable[..., Any]]: The executed decorated function.
    """
    max_str_len = get_evar('LOGF_MAX_STR_LEN', max_str_len)
    single_msg = get_evar('LOGF_SINGLE_MSG', single_msg)
    use_print = get_evar('LOGF_USE_PRINT', use_print)

    # for backwards compatability, override log_exec_time using
    # the measure_time kwarg if present
    if 'measure_time' in kwargs:
        log_exec_time = kwargs['measure_time']

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        # handle async funcs
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def decorator(*args, **kwargs) -> Any:
                start_time = (
                    asyncio.get_event_loop().time() if log_exec_time else None
                )
                if not single_msg:
                    logmsg_enter = func_args_str(
                        func, args, kwargs, log_args, max_str_len
                    )
                    print_or_log(logmsg_enter, level, use_print, use_logger)

                result = await func(*args, **kwargs)
                logmsg_exit = func_return_str(
                    func,
                    args,
                    kwargs,
                    result,
                    start_time,
                    log_args,
                    log_return,
                    single_msg,
                    max_str_len,
                )
                print_or_log(logmsg_exit, level, use_print, use_logger)
                return result

        # handle sync funcs
        else:

            @wraps(func)
            def decorator(*args, **kwargs) -> Any:
                # Start the timer if required and execute the function.
                start_time = time.time() if log_exec_time else None

                # if single_msg=True log both enter/exit in one message later
                if not single_msg:
                    # Log function arguments if required argstr used later if single msg
                    # otherwise, only the function name is logged on entry
                    logmsg_enter = func_args_str(
                        func, args, kwargs, log_args, max_str_len
                    )

                    print_or_log(logmsg_enter, level, use_print, use_logger)

                result = func(*args, **kwargs)
                logmsg_exit = func_return_str(
                    func,
                    args,
                    kwargs,
                    result,
                    start_time,
                    log_args,
                    log_return,
                    single_msg,
                    max_str_len,
                )

                # Log the return value and execution time if required
                print_or_log(logmsg_exit, level, use_print, use_logger)

                return result

        return decorator

    return wrapper
