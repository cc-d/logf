#!/usr/bin/env python
import sys
import os

sys.path.append(os.path.dirname(__file__))

from logfunc import logf



MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 400

@logf()
def rec_self_func(f=None, n=0, max=MAX, nologf=False):
    if n >= max:
        return f
    if nologf:
        return rec_self_func(f, n + 1, max)
    if f is None:
        f = rec_self_func
    else:
        f = f

    return rec_self_func(f, n + 1, max)


from time import time


@logf()
class con_time:
    def __init__(self, f, *args, **kwargs):
        self.t1 = time()
        f(*args, **kwargs)
        print(time() - self.t1, *args, **kwargs)


print(con_time(rec_self_func).t1, con_time(rec_self_func, False).t1)

import asyncio
@logf()
def wrap():
    @logf()
    async def asynctest():
        return 'abcdefg' * 22

    return asyncio.run(asyncio.wait_for(asynctest(), timeout=1))


wrap()