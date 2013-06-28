# -*- coding: utf8 -*-

import time

from sympy.utilities.lambdify import lambdify

from mathics.builtin.base import Builtin
from mathics.core.expression import Expression, Real, Integer
from mathics.core.convert import from_sympy

COMPILED = {}


class Compile(Builtin):
    """
    <dl>
    <dt>'Compile[{$x1$, $x2$, ...}, expr]'
      <dd>compiles $expr$ as a numerical function of $xi$.
    </dl>

    >> cf = Compile[{x, y}, Cos[x ^ 2] / (1 + x ^ 2 + y ^ 2)]
     = CompiledFunction[...]

    >> f = Function[{x, y}, Cos[x ^ 2] / (1 + x ^ 2 + y ^ 2)]
     = Function[{x, y}, Cos[x ^ 2] / (1 + x ^ 2 + y ^ 2)]

    Evaluating the compiled function lots of times is conseiderably faster
    >> x = RandomReal[{-1,1}, {100, 2}];
    >> f @@@ x; // AbsoluteTiming
    = {..., Null}
    >> cf @@@ x; // AbsoluteTiming
    = {..., Null}
    """

    rules = {
        'Compile[args_?NotListQ, expr]': 'Compile[{args}, expr]',
    }

    # TODO implement MakeBoxes properly (with -CompiledCode- etc)

    def apply(self, args, expr, evaluation):
        "Compile[args_List, expr_]"

        h = hash((args, expr))
        COMPILED[h] = lambdify(
            (arg.to_sympy() for arg in args.leaves), expr.to_sympy())
        return Expression('CompiledFunction', Integer(h))


class CompiledFunction(Builtin):
    """
    <dl>
    <dt>'CompiledFunctions[args...]'
      <dd>represents a compiled function
    </dl>
    """

    # Method used to store / lookup compiled functions based on expr, args
    # is quite different to the method used by MMA

    messages = {
        'invd': '`1` is not a valid CompiledFunction expression.'
    }

    def apply(self, h, args, evaluation):
        "CompiledFunction[h_Integer][args___]"
        try:
            cf = COMPILED[h.get_int_value()]
        except KeyError:
            return evaluation.message('CompiledFunction', 'invd', Expression(
                Expression('CompiledFunction', h), args))
        return from_sympy(cf(*[arg.to_sympy() for arg in args.get_sequence()]))
