import unittest
import traceback
from logfunc import logf


@logf()
def wf():
    raise ValueError("This is a test exception")


@logf()
def wf2():
    return wf()


@logf()
def wf3():
    return wf2()


@logf()
def wf4():
    return wf3()


@logf()
def wf5():
    return wf4()


import sys
import traceback


def filter_traceback():
    try:
        # Example: Simulate your function call here that raises an exception
        # This is a placeholder, replace with your actual function
        wf5()
    except:
        exc_type, exc_value, tb = sys.exc_info()

        # Convert the traceback to a list of tuples
        tb_tuples = traceback.extract_tb(tb)

        # Filter out entries where the filename contains 'logfunc' or the line contains 'result'
        filtered_tb_tuples = [
            frame
            for frame in tb_tuples
            if "logfunc" not in frame.filename and "result" not in frame.line
        ]

        # Convert filtered traceback to a string
        filtered_traceback_str = "".join(
            traceback.format_list(filtered_tb_tuples)
        )

        # Print the modified traceback
        print(f"{filtered_traceback_str}{exc_type.__name__}: {exc_value}")


filter_traceback()
