# -*- coding: utf8 -*-

u"""
    Mathics: a general-purpose computer algebra system
    Copyright (C) 2011-2013 The Mathics Team

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import os
import sys

from mathics import get_banner_string
from mathics.core.expression import Expression, Integer, String, Symbol
from mathics.core.rules import Rule
from mathics.core.evaluation import Evaluation
from mathics.core.definitions import Definitions
from mathics.core.parser import parse, TranslateError


def main():
    argparser = argparse.ArgumentParser(
        prog='MathicsKernel',
        usage='%(prog)s [options]',
        add_help=False,
        description = "Runs a standalone Mathics kernel",
        epilog = """Please feel encouraged to contribute to Mathics! Create
            your own fork, make the desired changes, commit, and make a pull 
            request.""")

    # Core Commands
    argparser.add_argument('-mathlink', help='communicate only via MathLink', action='store_true')
    argparser.add_argument('-lmverbose', help='print information on MathLM interaction', action='store_true')
    argparser.add_argument('-initfile', metavar='"file"', help='execute commands from file during startup', action='append')
    argparser.add_argument('-noinit', help='do not read initialization files', action='store_true')
    argparser.add_argument('-password', nargs=1, metavar='"pw"', help='use a password')
    argparser.add_argument('-pwfile', nargs=1, metavar='"file"', help='use a password file')
    argparser.add_argument('-run', metavar='cmd', help='run command on startup', action='append')
    argparser.add_argument('-noprompt', help='do not display banner or In/Out prompts', action='store_true')
    argparser.add_argument('-script', metavar='"file"', help='run commands from a file', action='append')

    # Extra Commands
    # argparser.add_argument('--version', '-v', action='version', version=get_version_string(False))
    # argparser.add_argument('--help', '-h', action='help', help='show this help message and exit')

    args = argparser.parse_args()

    if args.noprompt:
        in_prompt, out_prompt = "", "{1}\n" 
    else:
        in_prompt, out_prompt = "In[{0}]:= ", "Out[{0}]= {1}\n"

    instream, outstream = sys.stdin, sys.stdout

    def get_input_line(line_no):
        "Gets the next input line"
        return result

    def put_result_output(expression, line_no):
        outstream.write(out_prompt.format(line_no, expression))
        outstream.write('\n')

    def put_message_output(message):
        outstream.write('{0}\n\n'.format(message))

    def apply_syntaxhandler(input_string):
        pass

    def print_syntax_warnings(exception):
        outstream.write('{0}\n\n'.format(unicode(exception)))

    def simple_evaluate(input_string):
        """
        Evaluation outside the main loop
        does not print propmpts or modify In[n], Out[n] etc
        """
        try:
            input_expression = parse(input_string)
        except TranslateError as e:
            print_syntax_warnings(e)
            return
        evaluation = Evaluation(input_expression, definitions, timeout=30)
        expression = evaluation.result
        messages = evaluation.messages
        for message in messages:
            put_message_output(message)
        return expression

    ## INITIALIZATION

    # Load the definitions
    definitions = Definitions(add_builtin=True)

    # Print banner
    if not args.noprompt:
        outstream.write(get_banner_string(is_server=False, verbose=False))
    outstream.write("\n")

    ## PRE EVALUATION

    # Initialisation (init.m) files
    def get_init_dirs():
        """returns a list of directories to search for init.m files"""
        init_dirs = []

        # $BaseDirectory
        base_dir = simple_evaluate('$BaseDirectory').get_string_value()
        if base_dir is not None:
            init_dirs.append(os.path.join(base_dir, 'Kernel'))
            init_dirs.append(os.path.join(base_dir, 'FrontEnd'))

        # $UserBaseDirectory
        user_base_dir = simple_evaluate('$UserBaseDirectory').get_string_value()
        if user_base_dir is not None:
            init_dirs.append(os.path.join(user_base_dir, 'Kernel'))
            init_dirs.append(os.path.join(user_base_dir, 'FrontEnd'))

        # Autoload directories
        #TODO

        return init_dirs

    init_files = [os.path.join(root, 'init.m') for subdir in get_init_dirs()
                  for root, dirs, names in os.walk(subdir) if 'init.m' in names]

    # Add the files specified with -initfile "file"
    if args.initfile:
        for initfilearg in args.initfile:
            init_files.append(initfilearg)

    #TODO
    #if args.noinit is None:
    #    for init_file in init_files:
    #        parse_file(init_file)

    # Command line '-script "file"' argument
    script_files = []
    if args.script is not None:
        for scriptarg in args.script:
            script_files.append(scriptarg)

    #TODO
    #for script_file in script_files:
    #    parse_file(script_file)

    # Command line '-run "cmd"' arguments
    if args.run is not None:
        for runarg in args.run:
            simple_evaluate(runarg)

    ## MAIN LOOP
    line_no = 1
    definitions.set_ownvalue('$Line', Integer(line_no))

    while True:
        try:
            outstream.write(in_prompt.format(line_no))
            input_string = instream.readline()

            if input_string == '':          # Stream is closed
                raise EOFError
            elif input_string == '\n':      # Empty input
                continue
            input_string = input_string.rstrip('\n')
        except KeyboardInterrupt:
            outstream.write('\nKeyboardInterrupt\n')
            #TODO: Interrupt> prompt
            continue
        except EOFError:
            outstream.write('\n')
            break

        outstream.write('\n')

        # Apply $PreRead
        # TODO

        try:
            input_expression = parse(input_string)
        except TranslateError as e:
            print_syntax_warnings(e)
            apply_syntaxhandler(input_string)
            continue

        # Assign InString[n]
        definitions.add_rule('InString', Rule(Expression('InString', Integer(line_no)), String(input_string)))

        # Apply $Pre
        # TODO

        # Assign In[n]
        definitions.add_rule('In', Rule(Expression('In', Integer(line_no)), input_expression))

        # Evaluate Expression
        evaluation = Evaluation(input_expression, definitions, timeout=30)
        expression = evaluation.result
        messages = evaluation.messages

        for message in messages:
            put_message_output(message)
        definitions.set_ownvalue('$MessageList', Expression('List', *[msg.to_expression() for msg in messages]))

        # Apply $Post
        # TODO

        # Assign Out[n]
        definitions.add_rule('Out', Rule(Expression('Out', Integer(line_no)), expression))

        # Print Expression (unless it's Null)
        if expression != Symbol('Null'):
            put_result_output(expression, line_no)

        # Assign MessageList[n]

        # FIXME: Do this during evaluation such that e.g. '1/0; $MessageList'
        # returns {Power::infy}
        definitions.add_rule('MessageList', Rule(Expression('MessageList', Integer(line_no)), simple_evaluate('$MessageList')))

        # Reset $MessageList
        definitions.set_ownvalue('$MessageList', Expression('List'))

        # Increment $Line
        line_no = evaluation.get_config_value('$Line') + 1
        definitions.set_ownvalue('$Line', Integer(line_no))

if __name__ == '__main__':
    main()
