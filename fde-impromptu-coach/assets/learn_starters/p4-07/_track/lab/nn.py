"""A tiny neural-network library on top of your micrograd. YOU build it in project 4, step 7.

Neuron: weights and a bias, output tanh(w · x + b)
Layer:  several neurons that all look at the same inputs
MLP:    layers in a row (multi-layer perceptron)
"""
from __future__ import annotations

import random
from typing import List

from .micrograd import Value


class Neuron:
    def __init__(self, n_inputs: int):
        self.w = [Value(random.uniform(-1, 1), label=f"w{i}") for i in range(n_inputs)]
        self.b = Value(random.uniform(-1, 1), label="b")

    def __call__(self, x):
        # TODO: act = sum of w_i * x_i, plus b. Return act.tanh()
        # Tip: start from self.b and add each product: act = self.b; for wi, xi in zip(...): act = act + wi * xi
        raise NotImplementedError("Write Neuron.__call__")

    def parameters(self) -> List[Value]:
        return self.w + [self.b]


class Layer:
    def __init__(self, n_inputs: int, n_outputs: int):
        self.neurons = [Neuron(n_inputs) for _ in range(n_outputs)]

    def __call__(self, x):
        # TODO: run every neuron on x. Return the single Value if there is only one neuron, else the list.
        raise NotImplementedError("Write Layer.__call__")

    def parameters(self) -> List[Value]:
        # TODO: all parameters of all neurons, in one flat list
        raise NotImplementedError("Write Layer.parameters")


class MLP:
    def __init__(self, n_inputs: int, layer_sizes: List[int]):
        sizes = [n_inputs] + list(layer_sizes)
        self.layers = [Layer(sizes[i], sizes[i + 1]) for i in range(len(layer_sizes))]

    def __call__(self, x):
        # TODO: feed x through each layer in turn; the output of one is the input of the next
        raise NotImplementedError("Write MLP.__call__")

    def parameters(self) -> List[Value]:
        return [p for layer in self.layers for p in layer.parameters()]
