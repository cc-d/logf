#!/usr/bin/env python
import sys
import os

sys.path.append(os.path.dirname(__file__))

from logfunc import logf


@logf()
def rec_self_func(f=None, n=0, max=300, nologf=False):
    if n >= max:
        return f
    if nologf:
        return rec_self_func(f, n + 1, max)
    if f is None:
        f = logf(rec_self_func)
    else:
        f = f

    return logf(rec_self_func(f, n + 1, max))


from time import time


class con_time:
    def __init__(self, f, *args, **kwargs):
        self.t1 = time()
        f(*args, **kwargs)
        print(time() - self.t1, *args, **kwargs)


print(con_time(rec_self_func).t1, con_time(rec_self_func, False).t1)
