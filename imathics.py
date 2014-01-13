#!/usr/bin/env python2
import os
import sys
import json
import zmq
import time
from threading import Thread

from IPython.utils.localinterfaces import LOCALHOST
from IPython.kernel.zmq.session import Session

from mathics.core.definitions import Definitions
from mathics.core.evaluation import Evaluation
from mathics.core.expression import Integer
from mathics.settings import TIMEOUT


class Heartbeat(Thread):
    "A simple ping-pong style heartbeat that runs in a thread."
    def __init__(self, context, config):
        Thread.__init__(self)
        self.context = context
        self.config = config
        self.daemon = True
        self.socket = self.context.socket(zmq.REP)

    def run(self):
        self.socket.bind(
            "{transport}://{ip}:{hb_port}".format(**self.config))
        zmq.device(zmq.FORWARDER, self.socket, self.socket)


class Kernel(object):
    "IPython kernel for Mathics"
    def __init__(self, context, config):
        self.context = context
        self.config = config
        self.session = Session(username='MathicsKernel', debug=False)
        self.stdin = self.context.socket(zmq.ROUTER)
        self.shell = self.context.socket(zmq.ROUTER)
        self.iopub = self.context.socket(zmq.PUB)

    def start(self):
        self.stdin.bind(
            "{transport}://{ip}:{stdin_port}".format(**self.config))
        self.shell.bind(
            "{transport}://{ip}:{shell_port}".format(**self.config))
        self.iopub.bind(
            "{transport}://{ip}:{iopub_port}".format(**self.config))
        # start kernel
        self.session.send(self.iopub, 'status',
                          content={'execution_state': 'starting'})

        # Load the defintions
        self.definitions = Definitions(add_builtin=True)
        self.execution_count(0)

        self.session.send(self.iopub, 'status',
                          content={'execution_state': 'idle'})

        # Event Loop
        while True:
            try:
                shell_idents, shell_msg = self.session.recv(self.shell)

                if shell_msg is None:
                    continue

                msg_type = shell_msg['msg_type']
                handler = getattr(self, shell_msg['msg_type'], None)
                if handler is None:
                    raise ValueError(
                        "Unknown msg_type %s" % shell_msg['msg_type'])
                handler(shell_msg)
            except KeyboardInterrupt:
                # Interrupts during Evaluation return $Aborted. Here we just
                # ignore it and wait for the next message
                continue

    def execution_count(self, number=None):
        "returns the current $Line integer, optionally also sets $Line first"
        if number is not None:
            self.definitions.set_ownvalue('$Line', Integer(number))
            return number
        else:
            line = self.definitions.get_ownvalues('$Line')[0].replace
            return line.get_int_value()

    def kernel_info_request(self, shell_msg):
        self.session.send(
            self.shell, 'kernel_info_reply', content={
                'protocol_version': [1, 1, 0],
                'language_version': [0, 6],
                'language': 'mathics'
            }, parent=shell_msg)

    def execute_request(self, shell_msg):
        request_content = shell_msg['content']

        # report the kernel as busy
        self.session.send(
            self.iopub, 'status', content={'execution_state': 'busy'},
            parent=shell_msg)

        def publish(text):
            self.session.send(
                self.iopub, 'pyout', content={
                    'execution_count': self.execution_count(),
                    'data': {'text/plain': unicode(text)},
                    'metadata': {},
                }, parent=shell_msg)

        code = request_content['code']
        self.session.send(
            self.iopub, 'pyin', content={
                'execution_count': self.execution_count(),
                'data': {'text/plain': code},
                'metadata': {},
            }, parent=shell_msg)

        evaluation = Evaluation(
            code, self.definitions, timeout=TIMEOUT, out_callback=publish)
        results = [result.get_data() for result in evaluation.results]

        status = 'ok'
        for result in results:
            for msg in result['out']:
                status = 'error'
                self.session.send(
                    self.iopub, 'pyerr', content={
                        'execution_count': self.execution_count(),
                        'ename': msg['prefix'],
                        'evalue': msg['text'],
                        # 'traceback': [''],
                        'traceback': [msg['prefix'] + msg['text']],
                    }, parent=shell_msg)
            if result['result'] is not None:
                self.session.send(
                    self.iopub, 'pyout', content={
                        'execution_count': result['line'],
                        'data': {'text/plain': result['result']},
                        'metadata': {},
                    }, parent=shell_msg)

        self.session.send(
            self.shell, 'execute_reply', content={
                'status': status,
                'execution_count': self.execution_count(),
                'user_variables': {},
                'payload': [],
                'user_expressions': {},
            }, parent=shell_msg)

        # report the kernel as idle
        self.session.send(
            self.iopub, 'status', content={'execution_state': 'idle'},
            parent=shell_msg)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        try:
            json_config = open(sys.argv[1])
        except IOError:
            print "failed to open %s" % sys.argv[1]
            sys.exit(1)
        config = json.load(json_config)
    else:
        print "expected 1 command line argument, got %i" % (len(sys.argv) - 1)
        sys.exit(1)

    context = zmq.Context.instance()

    heartbeat = Heartbeat(context, config)
    heartbeat.start()

    kernel = Kernel(context, config)
    kernel.start()
