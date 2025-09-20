from typing import (
    Any,
    Iterable as Iter,
    Generator as Gen,
    Union as U,
    Optional as Opt,
)


def log_object(
    obj: Any, gen: bool = False, recursive_logf: bool = False
) -> U[Iter[Any], Any]:
    """Return all accessible objects from a given object.

    ~obj: Any object which will be recursively iterated over, with all
        sub-objects also being logged.

    ~gen: If True, returns a generator; if False, returns a tuple

    -> Union[tuple[Any, ...], Generator[Any, None, None]]: Extracted objects as tuple or generator
    """
    from logfunc import _def_logf

    def _get_objs(obj: Any, recursive_logf: bool = False):

        dir = _def_logf(dir)
        getattr = _def_logf(getattr)
        names = dir(obj)
        log_object(obj)
        while names:
            try:
                new_obj = getattr(obj, names.pop(0))

            except:
                continue

            try:
                setattr('__prop__obj__', new_obj)
            except Exception as e:
                pass

            if callable(_get_objs):
                new_obj = _def_logf(new_obj)
            yield new_obj

    objs = [log_object(f, ret=True) for f in _get_objs(obj)]

    if gen is False:
        return tuple(_get_objs(obj))
    return (_ for _ in _get_objs(obj))


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


log_object(n)

n = Node(depth=0, max_depth=7, branches=4)

print(1)
