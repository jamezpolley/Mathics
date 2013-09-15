# -*- coding: utf8 -*-

"""
String functions
"""

import re
from mathics.builtin.base import BinaryOperator, Builtin, Test
from mathics.core.expression import (Expression, Symbol, String, Integer,
                                     from_python)


class StringJoin(BinaryOperator):
    """
    >> StringJoin["a", "b", "c"]
     = abc
    >> "a" <> "b" <> "c" // InputForm
     = "abc"

    'StringJoin' flattens lists out:
    >> StringJoin[{"a", "b"}] // InputForm
     = "ab"
    >> Print[StringJoin[{"Hello", " ", {"world"}}, "!"]]
     | Hello world!
    """

    operator = '<>'
    precedence = 600
    attributes = ('Flat', 'OneIdentity')

    def apply(self, items, evaluation):
        'StringJoin[items___]'

        result = ''
        items = items.flatten(Symbol('List'))
        if items.get_head_name() == 'List':
            items = items.leaves
        else:
            items = items.get_sequence()
        for item in items:
            if not isinstance(item, String):
                evaluation.message('StringJoin', 'string')
                return
            result += item.value
        return String(result)


class StringSplit(Builtin):
    """
    >> StringSplit["abc,123", ","]
     = {abc, 123}

    >> StringSplit["abc 123"]
     = {abc, 123}

    #> StringSplit["  abc    123  "]
     = {abc, 123}

    >> StringSplit["abc,123.456", {",", "."}]
     = {abc, 123, 456}

    #> StringSplit["x", "x"]
     = {}

    #> StringSplit[x]
     : String or list of strings expected at position 1 in StringSplit[x].
     = StringSplit[x]

    #> StringSplit["x", x]      (* Mathematica uses StringExpression *)
     : String or list of strings expected at position 2 in StringSplit[x, x].
     = StringSplit[x, x]
    """

    messages = {
        'strse': 'String or list of strings expected at position `1` in `2`.',
    }

    def apply(self, string, seps, evaluation):
        'StringSplit[string_String, seps_]'
        result = [string.get_string_value()]
        if seps.has_form('List', None):
            py_seps = seps.get_leaves()
        else:
            py_seps = [seps]

        py_seps = [to_regex(s) for s in py_seps]
        if any(s is None for s in py_seps):
            evaluation.message('StringSplit', 'strse', Integer(2),
                               Expression('StringSplit', string, seps))
            return

        for s in py_seps:
            result = [t for res in result for t in re.split(s, res)]

        return from_python(filter(lambda x: x != u'', result))

    def apply_empty(self, string, evaluation):
        'StringSplit[string_String]'
        py_string = string.get_string_value()
        result = py_string.split()
        return from_python(filter(lambda x: x != u'', result))

    def apply_strse1(self, x, evaluation):
        'StringSplit[x_/;Not[StringQ[x]]]'
        evaluation.message('StringSplit', 'strse', Integer(1),
                           Expression('StringSplit', x))
        return

    def apply_strse2(self, x, y, evaluation):
        'StringSplit[x_/;Not[StringQ[x]], y_]'
        evaluation.message('StringSplit', 'strse', Integer(1),
                           Expression('StringSplit', x))
        return


class StringLength(Builtin):
    """
    'StringLength' gives the length of a string.
    >> StringLength["abc"]
     = 3
    'StringLength' is listable:
    >> StringLength[{"a", "bc"}]
     = {1, 2}

    >> StringLength[x]
     : String expected.
     = StringLength[x]
    """

    attributes = ('Listable',)

    def apply(self, str, evaluation):
        'StringLength[str_]'

        if not isinstance(str, String):
            evaluation.message('StringLength', 'string')
            return
        return Integer(len(str.value))


class StringReplace(Builtin):
    """
    <dl>
    <dt>'StringReplace["$string$", $s$->$sp$]' or 'StringReplace["$string$", {$s1$->$sp1$, $s2$->$sp2$}]'
      <dd>replace the string $si$ by $spi$ for all occurances in "$string$".
    <dt>'StringReplace["$string$", $srules$, $n$]'
      <dd>only perform the first $n$ replacements.
    <dt>'StringReplace[{"$string1$", "$string2$", ...}, srules]'
      <dd>perform replacements on a list of strings
    </dl>

    StringReplace replaces all occurances of one substring with another:
    >> StringReplace["xyxyxyyyxxxyyxy", "xy" -> "A"]
     = AAAyyxxAyA

    Multiple replacements can be supplied:
    >> StringReplace["xyzwxyzwxxyzxyzw", {"xyz" -> "A", "w" -> "BCD"}]
     = ABCDABCDxAABCD

    Only replace the first 2 occurances:
    >> StringReplace["xyxyxyyyxxxyyxy", "xy" -> "A", 2]
     = AAxyyyxxxyyxy

    StringReplace acts on lists of strings too:
    >> StringReplace[{"xyxyxxy", "yxyxyxxxyyxy"}, "xy" -> "A"]
     = {AAxA, yAAxxAyA}

    #> StringReplace["abcabc", "a" -> "b", Infinity]
     = bbcbbc
    #> StringReplace[x, "a" -> "b"]
     : String or list of strings expected at position 1 in StringReplace[x, a -> b].
     = StringReplace[x, a -> b]
    #> StringReplace["xyzwxyzwaxyzxyzw", x]
     : x is not a valid string replacement rule.
     = StringReplace[xyzwxyzwaxyzxyzw, x]
    #> StringReplace["xyzwxyzwaxyzxyzw", x -> y]
     : Element x is not a valid string or pattern element in x.
     = StringReplace[xyzwxyzwaxyzxyzw, x -> y]
    #> StringReplace["abcabc", "a" -> "b", x]
     : Non-negative integer or Infinity expected at position 3 in StringReplace[abcabc, a -> b, x].
     = StringReplace[abcabc, a -> b, x]

    #> StringReplace["01101100010", "01" .. -> "x"]
     = x1x100x0

    #> StringReplace["abc abcb abdc", "ab" ~~ _ -> "X"]
     = X Xb Xc

    #> StringReplace["abc abcd abcd",  WordBoundary ~~ "abc" ~~ WordBoundary -> "XX"]
     = XX abcd abcd

    #> StringReplace["abcd acbd", RegularExpression["[ab]"] -> "XX"]
     = XXXXcd XXcXXd

    #> StringReplace["abcd acbd", RegularExpression["[ab]"] ~~ _ -> "YY"]
     = YYcd YYYY

    #> StringReplace["abcdabcdaabcabcd", {"abc" -> "Y", "d" -> "XXX"}]
     = YXXXYXXXaYYXXX


    #> StringReplace["  Have a nice day.  ", (StartOfString ~~ Whitespace) | (Whitespace ~~ EndOfString) -> ""] // FullForm
     = "Have a nice day."
    """


    # TODO Special Characters
    """
    #> StringReplace["product: A \[CirclePlus] B" , "\[CirclePlus]" -> "x"]
     = A x B
    """

    attributes = ('Protected')

    # TODO: Implement these options
    options = {
        'IgnoreCase': 'False',
        'MetaCharacters': 'None',
    }

    messages = {
        'strse': 'String or list of strings expected at position `1` in `2`.',
        'srep': '`1` is not a valid string replacement rule.',
        'innf': ('Non-negative integer or Infinity expected at '
                 'position `1` in `2`.'),
    }

    def apply(self, string, rule, evaluation):
        'StringReplace[string_, rule_]'
        return self.apply_n(string, rule, None, evaluation)

    def apply_n(self, string, rule, n, evaluation):
        'StringReplace[string_, rule_, n_]'

        if n is None:
            expr = Expression('StringReplace', string, rule)
        else:
            expr = Expression('StringReplace', string, rule, n)

        # convert string
        if string.has_form('List', None):
            py_strings = [stri.get_string_value() for stri in string.leaves]
            if None in py_strings:
                return evaluation.message(
                    'StringReplace', 'strse', Integer(1), expr)
        else:
            py_strings = string.get_string_value()
            if py_strings is None:
                return evaluation.message(
                    'StringReplace', 'strse', Integer(1), expr)

        # convert rule
        def convert_rule(r):
            if r.has_form('Rule', None) and len(r.leaves) == 2:
                py_s = to_regex(r.leaves[0])
                if py_s is None:
                    return evaluation.message(
                        'StringExpression', 'invld', r.leaves[0], r.leaves[0])
                # TODO: py_sp is allowed to be more general (function, etc)
                py_sp = r.leaves[1].get_string_value()
                if py_sp is not None:
                    return (py_s, py_sp)
            return evaluation.message('StringReplace', 'srep', r)

        if rule.has_form('List', None):
            py_rules = [convert_rule(r) for r in rule.leaves]
        else:
            py_rules = [convert_rule(rule)]
        if None in py_rules:
            return None

        # convert n
        if n is None:
            py_n = 0
        elif n == Expression('DirectedInfinity', Integer(1)):
            py_n = 0
        else:
            py_n = n.get_int_value()
            if py_n < 0:
                return evaluation.message(
                    'StringReplace', 'innf', Integer(3), expr)

        def do_subs(py_stri):
            for py_s, py_sp in py_rules:
                py_stri = re.sub(py_s, py_sp, py_stri, py_n)
            return py_stri

        if isinstance(py_strings, list):
            return Expression(
                'List', *[String(do_subs(py_stri)) for py_stri in py_strings])
        else:
            return String(do_subs(py_strings))


class Characters(Builtin):
    u"""
    >> Characters["abc"]
     = {a, b, c}

    #> \\.78\\.79\\.7A
     = xyz

    #> \\:0078\\:0079\\:007A
     = xyz

    #> \\101\\102\\103\\061\\062\\063
     = ABC123

    #> \\[Alpha]\\[Beta]\\[Gamma]
     = \u03B1\u03B2\u03B3
    """

    attributes = ('Listable',)

    def apply(self, string, evaluation):
        'Characters[string_String]'

        return Expression('List', *(String(c) for c in string.value))


class CharacterRange(Builtin):
    """
    >> CharacterRange["a", "e"]
     = {a, b, c, d, e}
    >> CharacterRange["b", "a"]
     = {}
    """

    attributes = ('ReadProtected',)

    messages = {
        'argtype': "Arguments `1` and `2` are not both strings of length 1.",
    }

    def apply(self, start, stop, evaluation):
        'CharacterRange[start_String, stop_String]'

        if len(start.value) != 1 or len(stop.value) != 1:
            evaluation.message('CharacterRange', 'argtype', start, stop)
            return
        start = ord(start.value[0])
        stop = ord(stop.value[0])
        return Expression('List', *[
            String(unichr(code)) for code in xrange(start, stop + 1)])


class String_(Builtin):
    """
    'String' is the head of strings.
    >> Head["abc"]
     = String
    >> "abc"
     = abc
    Use 'InputForm' to display quotes around strings:
    >> InputForm["abc"]
     = "abc"
    'FullForm' also displays quotes:
    >> FullForm["abc" + 2]
     = Plus[2, "abc"]
    """

    name = 'String'


class ToString(Builtin):
    """
    >> ToString[2]
     = 2
    >> ToString[2] // InputForm
     = "2"
    >> ToString[a+b]
     = a + b
    >> "U" <> 2
     : String expected.
     = U <> 2
    >> "U" <> ToString[2]
     = U2
    """

    def apply(self, value, evaluation):
        'ToString[value_]'

        text = value.format(evaluation, 'OutputForm').boxes_to_text(
            evaluation=evaluation)
        return String(text)


class ToExpression(Builtin):
    """
    <dl>
    <dt>'ToExpression[$input$]'
      <dd>inteprets a given string as Mathics input.
    <dt>'ToExpression[$input$, $form$]'
      <dd>reads the given input in the specified form.
    <dt>'ToExpression[$input$, $form$, $h$]'
      <dd>applies the head $h$ to the expression before evaluating it.
    </dl>

    >> ToExpression["1 + 2"]
     = 3

    >> ToExpression["{2, 3, 1}", InputForm, Max]
     = 3

    #> ToExpression["log(x)", InputForm]
     = log x

    #> ToExpression["1+"]
     : Incomplete expression; more input is needed .
     = $Failed

    #> ToExpression[]
     : ToExpression called with 0 arguments; between 1 and 3 arguments are expected.
     = ToExpression[]
    """

    # TODO: Other forms
    """
    >> ToExpression["log(x)", TraditionalForm]
     = Log[x]
    #> ToExpression["log(x)", StandardForm]
     = log x
    """

    attributes = ('Listable', 'Protected')

    messages = {
        'argb': ('`1` called with `2` arguments; '
                 'between `3` and `4` arguments are expected.'),
        'interpfmt': ('`1` is not a valid interpretation format. '
                      'Valid interpretation formats include InputForm '
                      'and any member of $BoxForms.'),
        'notstr': 'The format type `1` is valid only for string input.',
        'sntxi': 'Incomplete expression; more input is needed `1`.',
    }

    def apply(self, seq, evaluation):
        'ToExpression[seq__]'

        # Organise Arguments
        py_seq = seq.get_sequence()
        if len(py_seq) == 1:
            (inp, form, head) = (py_seq[0], Symbol('InputForm'), None)
        elif len(py_seq) == 2:
            (inp, form, head) = (py_seq[0], py_seq[1], None)
        elif len(py_seq) == 3:
            (inp, form, head) = (py_seq[0], py_seq[1], py_seq[2])
        else:
            assert len(py_seq) > 3  # 0 case handled by apply_empty
            evaluation.message('ToExpression', 'argb', 'ToExpression',
                               Integer(len(py_seq)), Integer(1), Integer(3))
            return

        # Apply the differnet forms
        if form == Symbol('InputForm'):
            if isinstance(inp, String):
                from mathics.core.parser import parse, ParseError
                try:
                    result = parse(inp.get_string_value())
                except ParseError:
                    evaluation.message('ToExpression', 'sntxi', String(''))
                    return Symbol('$Failed')
            else:
                result = inp
        else:
            evaluation.message('ToExpression', 'interpfmt', form)
            return

        # Apply head if present
        if head is not None:
            result = Expression(head, result).evaluate(evaluation)

        return result

    def apply_empty(self, evaluation):
        'ToExpression[]'
        evaluation.message('ToExpression', 'argb', 'ToExpression',
                           Integer(0), Integer(1), Integer(3))
        return


class StringQ(Test):
    """
    <dl>
    <dt>'StringQ[$expr$]'
      <dd>returns 'True' if $expr$ is a 'String' or 'False' otherwise.
    </dl>

    >> StringQ["abc"]
     = True
    >> StringQ[1.5]
     = False
    >> Select[{"12", 1, 3, 5, "yz", x, y}, StringQ]
     = {12, yz}
    """

    def test(self, expr):
        return isinstance(expr, String)


# TODO
class RegularExpression(Builtin):
    """
    >> RegularExpression["[abc]"]
     = RegularExpression[[abc]]
    """


# TODO
class StringExpression(Builtin):
    """
    """

    # TODO
    """
    >> a ~~ b
     = a~~b

    >> "a" ~~ "b"
     = "ab"
    """

    messages = {
        'invld': 'Element `1` is not a valid string or pattern element in `2`.'
    }


def to_regex(expr):
    if expr is None:
        return None

    head = expr.get_head_name()
    if head == 'Symbol':
        return {
            'NumberString': r'\d+',
            'Whitespace': r'\s+',
            'DigitCharacter': r'\d',
            'WhitespaceCharacter': r'\s',
            'WordCharacter': r'\s',
            'StartOfLine': r'(?m)^',
            'EndOfLine': r'(?m)$',
            'StartOfString': r'^',
            'EndOfString': r'$',
            'WordBoundary': r'\b',
            'LetterCharacter': r'[a-zA-Z]',
            'HexidecimalCharacter': r'[0-9a-fA-F]',
        }.get(expr.get_name())
    elif head == 'String':
        leaf = expr.get_string_value()
        if leaf is not None:
            return "({0})".format(re.escape(leaf))
    elif head == 'RegularExpression':
        if len(expr.leaves) == 1:
            return "({0})".format(expr.leaves[0].get_string_value())
    elif head == 'CharacterRange':
        if len(expr.leaves) == 2:
            (start, stop) = (leaf.get_string_value() for leaf in expr.leaves)
            if all(x is not None and len(x) == 1 for x in (start, stop)):
                return "[{0}-{1}]".format(re.escape(start), re.escape(stop))
    elif head == 'Blank':
        if len(expr.leaves) == 0:
            return r'(.|\n)'
    elif head == 'BlankSequence':
        if len(expr.leaves) == 0:
            return r'(.|\n)+'
    elif head == 'BlankNullSequence':
        if len(expr.leaves) == 0:
            return r'(.|\n)*'
    elif head == 'Except':
        if len(expr.leaves) == 1:
            leaf = to_regex(expr.leaves[0])
            if leaf is not None:
                return '^{0}'.format(leaf)
        # TODO
        # if len(expr.leaves) == 2:
        #     pass
    elif head == 'Characters':
        if len(expr.leaves) == 1:
            leaf = expr.leaves[0].get_string_value()
            if leaf is not None:
                return '[{0}]'.format(re.escape(leaf))
    elif head == 'StringExpression':
        leaves = [to_regex(leaf) for leaf in expr.leaves]
        if None in leaves:
            return None
        return "".join(leaves)
    elif head == 'Longest':
        if len(leaves) == 1:
            return to_regex(expr.leaves[0])
    elif head == 'Shortest':
        if len(leaves) == 1:
            leaf = to_regex(expr.leaves[0])
            if leaf is not None:
                return '{0}*?'.format(leaf)
                # p*?|p+?|p??
    elif head == 'Repeated':
        if len(expr.leaves) == 1:
            leaf = to_regex(expr.leaves[0])
            if leaf is not None:
                return '{0}+'.format(leaf)
    elif head == 'RepeatedNull':
        if len(expr.leaves) == 1:
            leaf = to_regex(expr.leaves[0])
            if leaf is not None:
                return '{0}*'.format(leaf)
    elif head == 'Alternatives':
        leaves = [to_regex(leaf) for leaf in expr.leaves]
        if all(leaf is not None for leaf in leaves):
            return "|".join(leaves)
    else:
        #print expr, head
        pass
