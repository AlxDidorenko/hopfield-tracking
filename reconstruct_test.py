import numpy as np
from numpy.testing import assert_array_almost_equal
from pytest import approx

from reconstruct import annealing_curve, update_layer_grad


def test_annealing_curve():
    assert_array_almost_equal(annealing_curve(10, 40, 3, 2), [40., 20, 10, 10, 10])


def test_update_layer_grad():
    act = np.array([.5, .5])
    grad = np.array([0., 1.])
    sigmoid_minus_one = 1 / (1 + np.exp(2.))
    assert sigmoid_minus_one == approx(0.5 * (1 + np.tanh(-1)))
    assert_array_almost_equal(update_layer_grad(act, grad, 1.), [.5, sigmoid_minus_one])
    assert_array_almost_equal(update_layer_grad(act, grad, 1., learning_rate=0.5), [.5, (0.5 + sigmoid_minus_one) / 2])
    assert_array_almost_equal(update_layer_grad(act, grad, 1., dropout_rate=1.), [.5, .5])
