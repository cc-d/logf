import os
import re
import time
import inspect
import random
import string
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Any])

TRUNC_STR_LEN = 1000


def trunc_str(string: str, max_length: Optional[int] = TRUNC_STR_LEN) -> str:
    """
    Truncates a string if its length exceeds the specified maximum length.
    If the string is truncated, it appends '...' to indicate the truncation. If
    no max_length is specified, the string is returned as-is.

    Args:
        string (str): The string to truncate.
        max_length (int): The maximum length of the truncated string. Defaults to 1000.

    Returns:
        str: The truncated string.
    """
    if max_length is None: # None was explictly passed as an arg, return str as-is
        return string

    if len(string) > max_length:
        return string[:max_length - 3] + '...'
    return string


def logf(
    level: Optional[Union[int, str]] = logging.DEBUG,
    log_args: bool = True,
    log_return: bool = True,
    max_str_len: Optional[int] = TRUNC_STR_LEN,
    log_exec_time: bool = True,
    **kwargs
) -> Callable[..., Callable[..., Any]]:
    """
    A decorator that logs the execution time, function name, arguments, keyword arguments,
    and return value of a function using a specified log level.

    Args:
        level (Union[int, str], optional): The log level to use for logging. Defaults to logging.DEBUG.
        log_args (bool, optional): Should the function arguments be logged? Defaults to True.
        log_return (bool, optional): Should function return be logged? Defaults to True.
        max_str_len (Optional[int]): Maximum length of the logged arguments and return values. Defaults to 1000.
        log_exec_time (bool, optional): Should the function execution time be measured? Defaults to True.

    Returns:
        Callable[..., Callable[..., Any]]: The decorated function.
    """
    if isinstance(level, str):
        level_int = logging.getLevelName(level.upper())
    else:
        level_int = int(level)

    # for backwards compatability, override log_exec_time using
    # the measure_time kwarg if present
    if 'measure_time' in kwargs:
        log_exec_time = kwargs['measure_time']

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start the timer if required and execute the function.
            start_time = time.time() if log_exec_time else None

            fname = f'{func.__name__}()' # shorthand reference

            # Log function arguments if required
            if log_args:
                argstr = f'{trunc_str(str(args), max_str_len)} {trunc_str(str(kwargs), max_str_len)}'
                logmsg_enter = f'{fname} | {argstr}'
            else:
                logmsg_enter = fname # only log function name on entry

            logger.log(level_int, logmsg_enter)

            # Execute the function
            result = func(*args, **kwargs)

            # include execution time if log_exec_time=True
            if log_exec_time:
                exec_time = time.time() - start_time
                logmsg_exit = f'{fname} {exec_time:.5f}s'
            else:
                logmsg_exit = fname # only use func name

            # if log_return=True include returned obj str in logmsg
            if log_return:
                logmsg_exit = f'{logmsg_exit} | {trunc_str(str(result), max_str_len)}'

            # Log the return value and execution time if required
            logger.log(level_int, logmsg_exit)

            return result
        return wrapper
    return decorator
