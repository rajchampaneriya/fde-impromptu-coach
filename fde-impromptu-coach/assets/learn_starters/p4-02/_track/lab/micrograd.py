"""micrograd: your tiny autograd engine. YOU build it in project 4, in steps,
following Andrej Karpathy's lecture "building micrograd".

    Project 4, step 2  Value object: __add__, __mul__
    Project 4, step 4  gradients: the _backward of +, *, tanh, then backward()
    Project 4, step 5  more operations: __pow__, exp, __truediv__ (and the += fix)

Your notebooks import this file. After editing it, re-run the notebook's first cell
(it reloads the module automatically).
"""
from __future__ import annotations

import math


class Value:
    """A number that remembers how it was made, so it can compute gradients."""

    def __init__(self, data, _children=(), _op="", label=""):
        self.data = float(data)
        self.grad = 0.0                     # d(final output) / d(this value); filled by backward()
        self._backward = lambda: None       # how to push my grad to my children
        self._prev = set(_children)         # the values I was made from
        self._op = _op                      # the operation that made me ("+", "*", "tanh", ...)
        self.label = label

    def __repr__(self):
        name = f"{self.label}: " if self.label else ""
        return f"Value({name}data={self.data:.4f}, grad={self.grad:.4f})"

    # ------------------------------------------------------------------ step 2
    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        # TODO (step 2): out = a new Value with data self.data + other.data,
        #               children (self, other) and op "+". Return it.
        # TODO (step 4): before returning, give `out` a _backward function:
        #               d(out)/d(self) = 1 and d(out)/d(other) = 1 (chain rule: multiply by out.grad)
        raise NotImplementedError("Step 2: write __add__")

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        # TODO (step 2): like __add__, but data self.data * other.data and op "*"
        # TODO (step 4): d(out)/d(self) = other.data and d(out)/d(other) = self.data
        raise NotImplementedError("Step 2: write __mul__")

    # ------------------------------------------------------------------ step 4
    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")
        # TODO (step 4): give `out` a _backward: d(tanh x)/dx = 1 - t**2
        return out

    def backward(self):
        """Fill .grad of every value that led to this one."""
        # TODO (step 4):
        # 1. build a list `order` of all values in topological order (children before parents)
        # 2. set self.grad = 1.0
        # 3. call v._backward() for every v in reversed(order)
        raise NotImplementedError("Step 4: write backward")

    # ------------------------------------------------------------------ step 5
    def __pow__(self, k):
        assert isinstance(k, (int, float)), "only number powers"
        # TODO (step 5): data self.data ** k, op f"**{k}", d(out)/d(self) = k * self.data ** (k - 1)
        raise NotImplementedError("Step 5: write __pow__")

    def exp(self):
        # TODO (step 5): data math.exp(self.data), op "exp", d(out)/d(self) = out.data
        raise NotImplementedError("Step 5: write exp")

    def __truediv__(self, other):
        # TODO (step 5): a / b is a * b**-1 (reuse what you have)
        raise NotImplementedError("Step 5: write __truediv__")

    # Small helpers (given): they reuse the operations above.
    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __radd__(self, other):          # lets you write 2 + Value(3)
        return self + other

    def __rmul__(self, other):          # lets you write 2 * Value(3)
        return self * other

    def __rsub__(self, other):
        return Value(other) - self

    def __rtruediv__(self, other):
        return Value(other) / self


def draw(root: Value) -> str:
    """The expression graph as indented text (no Graphviz needed)."""
    lines = []

    def walk(v: Value, depth: int) -> None:
        lines.append("    " * depth + f"{v.label or '·'} = {v.data:.4f}  (grad {v.grad:.4f})"
                     + (f"  ← {v._op}" if v._op else ""))
        for child in sorted(v._prev, key=lambda c: c.label):
            walk(child, depth + 1)

    walk(root, 0)
    return "\n".join(lines)
