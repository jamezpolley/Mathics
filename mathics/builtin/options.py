# -*- coding: utf8 -*-

"""
Options and default arguments
"""

from mathics.builtin.base import Builtin, Predefined, BinaryOperator
from mathics.core.expression import Symbol, Expression, Integer, get_default_value
from mathics.core.rules import Rule


class Options(Builtin):
    """
    <dl>
    <dt>'Options[$f$]'
        <dd>gives a list of optional arguments to $f$ and their default values.
    </dl>

    You can assign values to 'Options' to specify options.
    >> Options[f] = {n -> 2}
     = {n -> 2}
    >> Options[f]
     = {n :> 2}
    >> f[x_, OptionsPattern[f]] := x ^ OptionValue[n]
    >> f[x]
     = x ^ 2
    >> f[x, n -> 3]
     = x ^ 3

    Delayed option rules are evaluated just when the corresponding 'OptionValue' is called:
    >> f[a :> Print["value"]] /. f[OptionsPattern[{}]] :> (OptionValue[a]; Print["between"]; OptionValue[a]);
     | value
     | between
     | value
    In contrast to that, normal option rules are evaluated immediately:
    >> f[a -> Print["value"]] /. f[OptionsPattern[{}]] :> (OptionValue[a]; Print["between"]; OptionValue[a]);
     | value
     | between

    Options must be rules or delayed rules:
    >> Options[f] = {a}
     : {a} is not a valid list of option rules.
     = {a}
    A single rule need not be given inside a list:
    >> Options[f] = a -> b
     = a -> b
    >> Options[f]
     = {a :> b}
    Options can only be assigned to symbols:
    >> Options[a + b] = {a -> b}
     : Argument a + b at position 1 is expected to be a symbol.
     = {a -> b}

    #> f /: Options[f] = {a -> b}
     = {a -> b}
    #> Options[f]
     = {a :> b}
    #> f /: Options[g] := {a -> b}
     : Rule for Options can only be attached to g.
     = $Failed

    #> Options[f] = a /; True
     : a /; True is not a valid list of option rules.
     = a /; True
    """

    def apply(self, f, evaluation):
        'Options[f_]'

        name = f.get_name()
        if not name:
            evaluation.message('Options', 'sym', f, 1)
            return
        options = evaluation.definitions.get_options(name)
        result = []
        for option, value in sorted(options.items(), key=lambda item: item[0]):
            # result.append(Expression('RuleDelayed', Expression('HoldPattern', Symbol(option)), value))
            # Don't use HoldPattern, since the returned List should be assignable to
            # Options again!
            result.append(Expression('RuleDelayed', Symbol(option), value))
        return Expression('List', *result)


class OptionValue(Builtin):
    """
    <dl>
    <dt>'OptionValue[$name$]'
        <dd>gives the value of the option $name$ as specified in a call to a function
        with 'OptionsPattern'.
    </dl>

    >> f[a->3] /. f[OptionsPattern[{}]] -> {OptionValue[a]}
     = {3}

    Unavailable options generate a message:
    >> f[a->3] /. f[OptionsPattern[{}]] -> {OptionValue[b]}
     : Option name b not found.
     = {OptionValue[b]}

    The argument of 'OptionValue' must be a symbol:
    >> f[a->3] /. f[OptionsPattern[{}]] -> {OptionValue[a+b]}
     : Argument a + b at position 1 is expected to be a symbol.
     = {OptionValue[a + b]}
    However, it can be evaluated dynamically:
    >> f[a->5] /. f[OptionsPattern[{}]] -> {OptionValue[Symbol["a"]]}
     = {5}
    """

    messages = {
        'optnf': "Option name `1` not found.",
    }

    def apply(self, symbol, evaluation):
        'OptionValue[symbol_]'

        if evaluation.options is None:
            return
        name = symbol.get_name()
        if not name:
            evaluation.message('OptionValue', 'sym', symbol, 1)
            return
        value = evaluation.options.get(name)
        if value is None:
            evaluation.message('OptionValue', 'optnf', symbol)
            return
        return value


class Default(Builtin):
    """
    <dl>
    <dt>'Default[$f$]'
        <dd>gives the default value for an omitted paramter of $f$.
    <dt>'Default[$f$, $k$]'
        <dd>gives the default value for a parameter on the $k$th position.
    <dt>'Default[$f$, $k$, $n$]'
        <dd>gives the default value for the $k$th parameter out of $n$.
    </dl>

    Assign values to 'Default' to specify default values.

    >> Default[f] = 1
     = 1
    >> f[x_.] := x ^ 2
    >> f[]
     = 1

    Default values are stored in 'DefaultValues':
    >> DefaultValues[f]
     = {HoldPattern[Default[f]] :> 1}

    You can use patterns for $k$ and $n$:
    >> Default[h, k_, n_] := {k, n}
    Note that the position of a parameter is relative to the pattern, not the matching expression:
    >> h[] /. h[___, ___, x_., y_., ___] -> {x, y}
     = {{3, 5}, {4, 5}}
    """

    def apply(self, f, i, evaluation):
        'Default[f_, i___]'

        i = i.get_sequence()
        if len(i) > 2:
            evaluation.message('Default', 'argb', 1 + len(i), 1, 3)
            return
        i = [index.get_int_value() for index in i]
        for index in i:
            if index is None or index < 1:
                evaluation.message('Default', 'intp')
                return
        name = f.get_name()
        if not name:
            evaluation.message('Default', 'sym', f, 1)
            return
        result = get_default_value(name, evaluation, *i)
        return result


def options_to_rules(options):
    items = sorted(options.iteritems())
    return [Expression('Rule', Symbol(name), value) for name, value in items]
