import numpy as np
from numpy import ndarray
from scipy.sparse import coo_matrix, csr_matrix


def curvature_energy_pairwise(a: ndarray, b: ndarray, c: ndarray,
                              cosine_power: float = 3., cosine_threshold: float = 0.,
                              distance_prod_power_in_denominator: float = 1.) -> ndarray:
    d1 = b - a
    d2 = c - b
    r1 = np.linalg.norm(d1, axis=-1)
    r2 = np.linalg.norm(d2, axis=-1)
    rr = r1 * r2
    cosines = (d1 * d2).sum(axis=-1) / rr
    cosines[cosines < cosine_threshold] = 0
    return cosines ** cosine_power / rr ** distance_prod_power_in_denominator


def segment_adjacent_pairs(seg: ndarray) -> ndarray:
    if len(seg) == 0:
        return np.empty((0, 2), dtype=int)
    is_adjacent = seg[:, np.newaxis, 1] == seg[np.newaxis, :, 0]
    adj = coo_matrix(is_adjacent)
    i, j = adj.row, adj.col
    return np.stack([i, j], axis=1)


def curvature_energy_matrix(pos: ndarray, seg: ndarray, pairs: ndarray,
                            curvature_cosine_power: float = 3.,
                            cosine_threshold: float = 0., distance_prod_power_in_denominator: float = 1.) -> csr_matrix:
    s1, s2 = seg[pairs.T]
    a, b, c = pos[s1[:, 0]], pos[s1[:, 1]], pos[s2[:, 1]]
    w = curvature_energy_pairwise(a, b, c, cosine_power=curvature_cosine_power,
                                  cosine_threshold=cosine_threshold,
                                  distance_prod_power_in_denominator=distance_prod_power_in_denominator)
    m = coo_matrix((w, pairs.T), shape=(len(seg), len(seg)))
    return (m + m.transpose()).tocsr()
