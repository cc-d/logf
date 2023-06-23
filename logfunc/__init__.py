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


def trunc_str(string: str, max_length: int) -> str:
    """
    Truncates a string if its length exceeds the specified maximum length.
    If the string is truncated, it appends '...' to indicate the truncation.

    Args:
        string (str): The string to truncate.
        max_length (int): The maximum length of the truncated string.

    Returns:
        str: The truncated string.
    """
    if len(string) > max_length:
        return string[:max_length - 3] + "..."
    return string


def logf(
    level: Optional[Union[int, str]] = logging.DEBUG,
    log_args: bool = True,
    log_return: bool = True,
    max_str_len: int = 1000,
    measure_time: bool = True
) -> Callable[[T], T]:
    """
    A decorator that logs the execution time, function name, arguments, keyword arguments,
    and return value of a function using a specified log level.

    Args:
        level (Union[int, str], optional): The log level to use for logging. Defaults to logging.DEBUG.
        log_args (bool, optional): Should the function arguments be logged? Defaults to True.
        log_return (bool, optional): Should function return be logged? Defaults to True.
        max_str_len (int, optional): Maximum length of the logged arguments and return values. Defaults to 1000.
        measure_time (bool, optional): Should the function execution time be measured? Defaults to True.

    Returns:
        Callable[[T], T]: The wrapped function.
    """
    if isinstance(level, str):
        level_int = logging.getLevelName(level.upper())
    else:
        level_int = int(level)

    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start the timer if required and execute the function.
            start_time = time.time() if measure_time else None

            # Log function arguments if required
            if log_args:
                arg_str = f"{func.__name__}() | {str(args)[:max_str_len]} {str(kwargs)[:max_str_len]}"
            else:
                arg_str = f"{func.__name__}()"

            logger.log(level_int, arg_str)

            # Execute the function
            result = func(*args, **kwargs)

            if measure_time:
                end_time = time.time()
                # Calculate the execution time and format the log message.
                exec_time = end_time - start_time
                exec_time_str = f"{exec_time:.5f}s"

            # Log the return value and execution time if required
            if log_return and measure_time:
                result_str = trunc_str(str(result), max_str_len)
                log_message = f"{func.__name__}() {exec_time_str} | {result_str}"
            elif log_return:
                result_str = trunc_str(str(result), max_str_len)
                log_message = f"{func.__name__}() | {result_str}"
            elif measure_time:
                log_message = f"{func.__name__}() {exec_time_str}"
            else:
                log_message = None

            if log_message is not None:
                # Log the message using the specified level.
                logger.log(level_int, log_message)

            return result
        return wrapper
    return decorator
