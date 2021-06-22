from typing import List, Tuple

import numpy as np
import pandas as pd
from numpy import ndarray

from cross import cross_energy, cross_energy_gradient, cross_energy_matrix
from curvature import curvature_energy, curvature_energy_gradient, curvature_energy_matrix
from total import total_activation_energy, \
    total_activation_energy_gradient, total_activation_matrix


def gen_segments_layer(a: pd.Index, b: pd.Index) -> ndarray:
    return np.stack([x.ravel() for x in np.meshgrid(a, b, indexing='ij')], axis=1)


def gen_segments_all(df: pd.DataFrame) -> List[ndarray]:
    vert_i_by_layer = [g.index for _, g in df.groupby('layer')]
    return [gen_segments_layer(a, b) for a, b in zip(vert_i_by_layer, vert_i_by_layer[1:])]


def energy(*args, **kwargs):
    ee = energies(*args, **kwargs)

    def _energy(activation):
        return sum(ee(activation))

    return _energy


def energy_gradient(*args, **kwargs):
    egs = energy_gradients(*args, **kwargs)

    def _energy_gradient(activation):
        return sum(egs(activation))

    return _energy_gradient


def energies(pos: ndarray, segments: List[ndarray], alpha: float = 1., beta: float = 1.,
             curvature_cosine_power: float = 3, cosine_threshold: float = 0., drop_gradients_on_self: bool = True):
    curvature_matrix = curvature_energy_matrix(pos, segments, curvature_cosine_power, cosine_threshold)
    a, b, c = total_activation_matrix(pos, segments, drop_gradients_on_self)
    crossing_matrix = cross_energy_matrix(segments)

    def _energies(act: ndarray) -> Tuple[float, float, float]:
        ec = curvature_energy(curvature_matrix, act, act)
        ef = alpha * cross_energy(crossing_matrix, act)
        en = beta * total_activation_energy(a, b, c, act)
        return ec, en, ef

    return _energies


def energy_gradients(pos: ndarray, segments: List[ndarray], alpha: float = 1., beta: float = 1.,
                     curvature_cosine_power: float = 3, cosine_threshold: float = 0.,
                     drop_gradients_on_self: bool = True):
    curvature_matrix = curvature_energy_matrix(pos, segments, curvature_cosine_power, cosine_threshold)
    a, b, _ = total_activation_matrix(pos, segments, drop_gradients_on_self)
    crossing_matrix = cross_energy_matrix(segments)

    def _energy_gradients(act: ndarray) -> Tuple[ndarray, ndarray, ndarray]:
        g1, g2 = curvature_energy_gradient(curvature_matrix, act, act)
        ecg = g1 + g2
        efg = alpha * cross_energy_gradient(crossing_matrix, act)
        eng = beta * total_activation_energy_gradient(a, b, act)
        return ecg, eng, efg

    return _energy_gradients
