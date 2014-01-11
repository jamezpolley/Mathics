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
            shell_idents, shell_msg = self.session.recv(self.shell)

            if shell_msg is None:
                continue

            msg_type = shell_msg['msg_type']
            handler = getattr(self, shell_msg['msg_type'], None)
            if handler is None:
                raise ValueError("Unknown msg_type %s" % shell_msg['msg_type'])
            handler(shell_msg)

    def publish(self, text):
        self.session.send(
            self.iopub, 'pyout', content={
                'execution_count': self.execution_count(),
                'data': {'text/plain': unicode(text)},
                'metadata': {},
            })

    def evaluate(self, text):
        evaluation = Evaluation(text, self.definitions, timeout=TIMEOUT,
                                out_callback=self.publish)
        for result in evaluation.results:
            if result.result:
                self.publish(result.result)

    def execution_count(self, number=None):
        "returns the current $Line integer, optionally also sets $Line first"
        if number is not None:
            self.definitions.set_ownvalue('$Line', Integer(number))
            return number
        else:
            return self.definitions.get_ownvalues('$Line')[0].replace.get_int_value()

    def kernel_info_request(self, shell_msg):
        self.session.send(
            self.shell, 'kernel_info_reply',
            parent=shell_msg['header'], content={
                'protocol_version': [1, 1, 0],
                'language_version': [0, 6],
                'language': 'mathics'})

    def execute_request(self, shell_msg):
        request_content = shell_msg['content']

        # report the kernel as busy
        self.session.send(
            self.iopub, 'status', content={'execution_state': 'busy'})

        self.evaluate(request_content['code'])

        # FIXME What about errors?
        # sucessful execution
        self.session.send(
            self.shell, 'execute_reply', parent=shell_msg['header'],
            content={
                'status': 'ok',
                'execution_count': self.execution_count(),
                'payload': [],
                'user_variables': {},
                'user_expressions': {}})

        # report the kernel as idle
        self.session.send(self.iopub, 'status',
                          content={'execution_state': 'idle'})


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
