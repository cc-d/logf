from typing import Any
from logfunc import logf


@logf()
def _get_objs(obj: Any):

    cur_objs = [obj]
    new_objs = [set(), []]
    while cur_objs:
        obj = cur_objs.pop(0)

        props = dir(obj)

        while props:
            try:
                new_obj = getattr(obj, props.pop(0))
                if new_obj:  # not in cur_objs:
                    if new_obj:  # not in new_objs:
                        new_objs[0].add(new_obj)
                        new_objs[1].append(new_obj)
                        continue
                raise Exception('REEEEEEEEEEEEEEEEEEEEE')
            except Exception as e:
                print('Error in new obj from prop')

    return new_objs


@logf()
def log_object(obj: Any):
    gen = _get_objs(obj)


class Node:
    def __init__(self, value=None, branches=5, depth=0, max_depth=10):
        self.value = value
        self.branches = []
        self.depth = depth
        self.max_depth = max_depth
        if depth < max_depth:
            for i in range(branches):
                self.branches.append(
                    Node(
                        value=f"{value}.{i}" if value else str(i),
                        branches=branches,
                        depth=depth + 1,
                        max_depth=max_depth,
                    )
                )

    def iterate(self):
        stack = [(self, "")]
        while stack:
            node, prefix = stack.pop()
            print(prefix + (node.value if node.value else "root"))
            for child in reversed(node.branches):
                stack.append(
                    (child, prefix + (node.value + "." if node.value else ""))
                )
        setattr(self, 'st', str(stack))
        print(self.st)


n = Node(depth=0, max_depth=7, branches=4)

import codecs

log_object(codecs)
