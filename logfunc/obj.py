from typing import (
    Any,
    Iterable as Iter,
    Generator as Gen,
    Union as U,
    Optional as Opt,
    List,
)


from random import choice, randint


def log_object(
    obj: Any, gen: bool = False, recursive_logf: bool = False
) -> U[Iter[Any], Any]:
    """Return all accessible objects from a given object.

    ~obj: Any object which will be recursively iterated over, with all
        sub-objects also being logged.

    ~gen: If True, returns a generator; if False, returns a tuple

    -> Union[tuple[Any, ...], Generator[Any, None, None]]: Extracted objects as tuple or generator
    """


class Node:
    children: List['Node']
    parents: List['Node']

    def __init__(self, n):
        self.n = n
        self.children = []
        self.parents = []

    def __repr__(self):
        return '<{} {} {}>'.format(
            self.parents if self.parents else '',
            self.n,
            self.children if self.children else '',
        )


class NodeWeb:
    nodes: List[Node]

    def __init__(self, nodes=100):
        self.nodes = []

        for i in range(nodes):
            node = Node(i)
            if i == 0:
                self.nodes = [Node(i)]
                continue

            n2 = choice(self.nodes)
            if i % 2 == 0:
                n2.children.append(node)
                node.parents.append(n2)
            else:
                n2.parents.append(node)
                node.children.append(n2)

            self.nodes.append(node)

    def __repr__(self):
        return f"<NodeWeb {' '.join(str(n) for n in self.nodes)}>"
