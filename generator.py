import math
from typing import Generator, Tuple

import numpy as np
import pandas as pd
from numpy import ndarray
from numpy.random import default_rng


class SimpleEventGenerator:
    def __init__(self, halfwidth_degrees: float = 15, n_layers: int = 8, layers_thickness=0.5,
                 field_strength=1., yz_deviation=0.005, noisiness=1., seed=None, box_size=None):
        self.halfwidth = math.radians(halfwidth_degrees)
        self.rng = default_rng(seed)
        self.n_layers = n_layers
        self.layers_thickness = layers_thickness
        self.field_strength = field_strength
        self.yz_deviation = yz_deviation
        self.noisiness = noisiness
        self.layer_i = np.arange(n_layers)
        self.layer_x = self.layers_thickness + self.layers_thickness * self.layer_i
        if box_size is None:
            self.size_y = self.size_z = self.layer_x[-1] * np.sin(self.halfwidth)
        else:
            self.size_y = self.size_z = box_size

    def gen_directions_in_cone(self, n: int = 1) -> ndarray:
        x = self.rng.uniform(math.cos(self.halfwidth), 1., n)
        alpha = self.rng.uniform(0.0, 2 * math.pi, n)
        r = np.sqrt(1. - x ** 2)
        y = r * np.cos(alpha)
        z = r * np.sin(alpha)
        return np.stack([x, y, z], axis=1)

    def run_straight_track(self, m: np.ndarray) -> ndarray:
        track_vector = m / m[0]  # scale track vector to put x-component at 1
        hits = track_vector[None, :] * self.layer_x[:, None]  # [layer, coordinate]
        return hits

    def run_curved_track(self, m: np.ndarray, q: float) -> ndarray:
        m_yz = np.linalg.norm(m[1:])
        r = m_yz / abs(self.field_strength * q)
        # to_center = np.array([[0, 1], [0, -1]]).dot(momentum[1:]) / m
        center = np.array([[0, -1], [1, 0]]).dot(m[1:]) / (self.field_strength * q)  # r * to_center
        # TC = 2*pi*r/v_xy  TL = h/v_z
        arc_per_dist = self.layers_thickness * self.field_strength * q / m[0]
        angles = np.arctan2(-center[1], -center[0]) + arc_per_dist * self.layer_x
        hits = np.stack([self.layer_x, center[0] + r * np.cos(angles), center[1] + r * np.sin(angles)], axis=-1)
        return hits

    def run_track(self, momentum: np.ndarray, charge: float) -> Tuple[ndarray, ndarray, ndarray]:
        if self.field_strength != 0 and charge != 0:
            hits = self.run_curved_track(momentum, charge)
        else:
            hits = self.run_straight_track(momentum)
        hits[:, 1:] += self.rng.normal(0, self.yz_deviation, hits[:, 1:].shape)  # inaccuracy in y and z
        ii = self.layer_i[:-1]
        seg = np.stack([ii, ii + 1], axis=1)
        return hits, self.layer_i, seg

    def gen_event(self, momenta: np.ndarray, charges: np.ndarray) -> Tuple[pd.DataFrame, ndarray]:
        xlist = []
        ylist = []
        zlist = []
        segmentlist = []
        tracklist = []
        chargelist = []
        layerlist = []
        n = 0
        for i, (m, q) in enumerate(zip(momenta, charges)):
            h, layers, s = self.run_track(m, q)
            x, y, z = h.transpose()
            xlist.append(x)
            ylist.append(y)
            zlist.append(z)
            k = len(layers)
            layerlist.append(layers)
            tracklist.append(np.full(k, i))
            chargelist.append(np.full(k, q))
            s += n
            segmentlist.append(s)
            n += k

        noise_count = self.rng.poisson(self.noisiness)
        noise_layer = self.rng.integers(0, self.n_layers, noise_count)
        layerlist.append(noise_layer)
        tracklist.append(np.full(noise_count, -1))
        chargelist.append(np.full(noise_count, np.nan))
        xlist.append(self.layer_x[noise_layer])
        ylist.append(self.rng.uniform(-self.size_y, self.size_y, noise_count))
        zlist.append(self.rng.uniform(-self.size_z, self.size_z, noise_count))

        xx = np.concatenate(xlist)
        yy = np.concatenate(ylist)
        zz = np.concatenate(zlist)
        layers = np.concatenate(layerlist)
        tracks = np.concatenate(tracklist)
        charges = np.concatenate(chargelist)
        seg = np.concatenate(segmentlist)

        return pd.DataFrame({'x': xx, 'y': yy, 'z': zz, 'layer': layers, 'track': tracks, 'charge': charges}), seg

    def gen_many_events(self, n: int = 1000, event_size: int = 10, momentum_scale=.2) \
            -> Generator[pd.DataFrame, None, None]:
        for _ in range(n):
            yield self.gen_event(
                self.rng.gamma(shape=5., scale=momentum_scale, size=event_size)[:, np.newaxis]
                * self.gen_directions_in_cone(event_size),
                charges=self.rng.choice([1, -1], event_size)
            )
