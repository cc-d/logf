from typing import (
    Any,
    Iterable as Iter,
    Generator as Gen,
    Union as U,
    Optional as Opt,
    List,
    Callable as Call,
)

from random import choice, randint


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
        return f"<NodeWeb {' '.join(repr(n) for n in self.nodes)}>"
