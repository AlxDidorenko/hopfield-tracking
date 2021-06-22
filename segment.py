from typing import List

import numpy as np
import pandas as pd
from numpy import ndarray


def gen_segments_layer(a: pd.Index, b: pd.Index) -> ndarray:
    return np.stack([x.ravel() for x in np.meshgrid(a, b, indexing='ij')], axis=1)


def gen_segments_all(df: pd.DataFrame) -> List[ndarray]:
    vert_i_by_layer = [g.index for _, g in df.groupby('layer')]
    return [gen_segments_layer(a, b) for a, b in zip(vert_i_by_layer, vert_i_by_layer[1:])]
