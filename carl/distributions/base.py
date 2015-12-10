# -*- coding: utf-8 -*-
#
# Carl is free software; you can redistribute it and/or modify it
# under the terms of the Revised BSD License; see LICENSE file for
# more details.

import theano
import theano.tensor as T

from sklearn.base import BaseEstimator
from sklearn.utils import check_random_state

from theano.gof import graph
from theano.tensor.shared_randomstreams import RandomStreams
from theano.tensor.sharedvar import SharedVariable

# ???: define the bounds of the parameters

def check_parameter(name, value):
    parameters = set()
    constants = set()
    observeds = set()

    if isinstance(value, SharedVariable):
        parameters.add(value)
    elif isinstance(value, T.TensorConstant):
        constants.add(value)
    elif isinstance(value, T.TensorVariable):
        inputs = graph.inputs([value])

        for var in inputs:
            if isinstance(var, SharedVariable):
                parameters.add(var)
            elif isinstance(var, T.TensorConstant):
                constants.add(var)
            elif isinstance(var, T.TensorVariable):
                if not var.name:
                    raise ValueError("Observed variables must be named.")
                observeds.add(var)
    else:
        value = theano.shared(value, name=name)
        parameters.add(value)

    return value, parameters, constants, observeds


def check_random_state(random_state):
    if isinstance(random_state, RandomStreams):
        return random_state
    else:
        return RandomStreams(seed=random_state)


class DistributionMixin(BaseEstimator):
    X = T.dmatrix(name="X")  # Input expression is shared by all distributions

    def __init__(self, random_state=None, **parameters):
        # Settings
        self.random_state = random_state

        # Validate parameters of the distribution
        self.parameters_ = set()        # base parameters
        self.constants_ = set()         # base constants
        self.observeds_ = set()         # base observeds

        # XXX: check that no two variables in observeds_ have the same name

        for name, value in parameters.items():
            v, p, c, o = check_parameter(name, value)
            setattr(self, name, v)

            for p_i in p:
                self.parameters_.add(p_i)
            for c_i in c:
                self.constants_.add(c_i)
            for o_i in o:
                self.observeds_.add(o_i)

        # Default observed variable is a scalar
        self.observeds_.add(self.X)

    def make_(self, expression, name):
        if hasattr(self, name):
            raise ValueError("Attribute {} already exists!")

        func = theano.function(
            [theano.Param(v, name=v.name) for v in self.observeds_],
            expression, allow_input_downcast=True
        )

        setattr(self, name, func)

    # Scikit-Learn estimator interface
    def get_params(self, deep=True):
        return super(DistributionMixin, self).get_params(deep=deep)

    def set_params(self, **params):
        for name, value in params.items():
            var = getattr(self, name, None)

            if isinstance(var, SharedVariable):
                var.set_value(value)
            elif isinstance(var, T.TensorVariable):
                raise ValueError("Only shared variables can be updated.")
            else:
                super(DistributionMixin, self).set_params(**{name: value})

        # XXX: shall we also allow replacement of variables and
        #      recompile all expressions instead?

    def fit(self, X, y=None):
        # XXX: todo
        raise NotImplementedError

    def score(self, X):
        # XXX: todo
        raise NotImplementedError
