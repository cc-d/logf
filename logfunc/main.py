import os
import re
import time
import inspect
import random
import string
import asyncio
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from .config import TRUNC_STR_LEN
from .utils import (
    get_evar,
    trunc_str,
    func_args_str,
    func_return_str,
    print_or_log,
    loglevel_int,
)
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Any])


def logf(
    level: Optional[Union[int, str]] = logging.DEBUG,
    log_args: bool = True,
    log_return: bool = True,
    max_str_len: Optional[int] = TRUNC_STR_LEN,
    log_exec_time: bool = True,
    single_msg: bool = False,
    use_print: bool = False,
    **kwargs
) -> Callable[..., Callable[..., Any]]:
    """
    A decorator that logs the execution time, function name, arguments, keyword arguments,
    and return value of a function using a specified log level.

    Args:
        level (Union[int, str]): The log level to use for logging.
            Defaults to logging.DEBUG.
        log_args (bool): Should the function arguments be logged?
            Defaults to True.
        log_return (bool): Should function return be logged?
            Defaults to True.
        max_str_len (Optional[int]): Maximum length of the logged arguments and return values.
            Defaults to 1000.
        log_exec_time (bool): Should the function execution time be measured?
            Defaults to True.
        single_msg (bool): Should both enter and exit log messages be combined into a single message?
            Default False
        use_print (bool): Should the log messages be printed instead of logged?
            Default False

    Returns:
        Callable[..., Callable[..., Any]]: The executed decorated function.
    """
    level = get_evar('LOGF_LEVEL', level)
    max_str_len = get_evar('LOGF_MAX_STR_LEN', max_str_len)
    single_msg = get_evar('LOGF_SINGLE_MSG', single_msg)
    use_print = get_evar('LOGF_USE_PRINT', use_print)

    # for backwards compatability, override log_exec_time using
    # the measure_time kwarg if present
    if 'measure_time' in kwargs:
        log_exec_time = kwargs['measure_time']

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
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
                    print_or_log(logmsg_enter, level, use_print)
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
                print_or_log(logmsg_exit, level, use_print)
                return result

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

                    print_or_log(logmsg_enter, level, use_print)

                # Execute the function
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
                print_or_log(logmsg_exit, level, use_print)

                return result

        return decorator

    return wrapper
