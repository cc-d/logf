from .version import __version__

from .main import logf

_def_logf = logf()


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
