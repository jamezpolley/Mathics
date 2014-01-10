#!/usr/bin/env python2
import os
import sys
import json
import zmq
from threading import Thread

from IPython.utils.localinterfaces import LOCALHOST
from IPython.kernel.zmq.session import Session

class Heartbeat(Thread):
    "A simple ping-pong style heartbeat that runs in a thread."
    def __init__(self, context, config):
        Thread.__init__(self)
        self.context = context
        self.ip = config['ip']
        self.port = config['hb_port']

        # if self.port == 0:
        #     s = socket.socket()
        #     # '*' means all interfaces to 0MQ, which is '' to socket.socket
        #     s.bind(('' if self.ip == '*' else self.ip, 0))
        #     self.port = s.getsockname()[1]
        #     s.close()
        self.addr = (self.ip, self.port)
        self.daemon = True

    def run(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind('tcp://%s:%i' % self.addr)
        zmq.device(zmq.FORWARDER, self.socket, self.socket)


class Kernel(object):
    def __init__(self, context, config):
        self.context = context
        self.stdin = self.context.socket(zmq.ROUTER)
        self.shell = self.context.socket(zmq.ROUTER)
        self.iopub = self.context.socket(zmq.PUB)

        self.session = Session(debug=True)

        self.stdin.bind("{transport}://{ip}:{stdin_port}".format(**config))
        self.shell.bind("{transport}://{ip}:{shell_port}".format(**config))
        self.iopub.bind("{transport}://{ip}:{iopub_port}".format(**config))

    def start(self):
        # start kernel
        self.session.send(self.iopub, 'status',
                     content={'execution_state': 'starting'})

        # TODO Start the mathics kernel

        self.session.send(self.iopub, 'status',
                     content={'execution_state': 'idle'})

        while True:
            shell_idents, shell_msg = self.session.recv(self.shell)

            if shell_msg is None:
                continue

            msg_type = shell_msg['msg_type']
            if msg_type == 'kernel_info_request':
                self.session.send(self.shell, 'kernel_info_reply', content={
                    'protocol_version': [1, 1, 0],
                    'language_version': [0, 6],
                    'language': 'mathics',
                })
            elif msg_type == 'execute_request':
                request_content = shell_msg['content']

                # report the kernel as busy
                self.session.send(self.iopub, 'status',
                                  content={'execution_state': 'busy'})

                self.session.send(self.iopub, 'pyin', content={
                    'code': request_content['code'],
                    'execution_count': 1,
                })

                self.session.send(self.iopub, 'pyout', content={
                    'execution_count': 1,
                    'data': {'text/plain': '123'},
                    'metadata': {},
                })

                # sucessful execution
                self.session.send(self.shell, 'execute_reply', content={
                    'status': 'ok',
                    'execution_count': 1,
                    'payload': [],
                    'user_variables': {},
                    'user_expressions': {},
                })


                # report the kernel as idle
                self.session.send(self.iopub, 'status',
                             content={'execution_state': 'idle'})
            else:
                raise ValueError("Unknown msg_type %s" % msg_type)

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
