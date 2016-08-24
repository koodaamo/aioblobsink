"""
streamsink.

Usage:
  streamsink <stream_port>
  streamsink -h | --help
  streamsink --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""

import sys, os, io
import asyncio
import signal
import logging
import itertools

from growler import App
from growler.middleware import (Logger, Static, StringRenderer)

from docopt import docopt

version = "streamsink 1.0"
HOST = "127.0.0.1"
BOUNDARY = b' --- boundary --- '

logging.basicConfig()
logger = logging.getLogger("streamsink")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr = logging.FileHandler('streamsink.log')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)


class ReceiveMultipartStreamProtocol(asyncio.Protocol):

   def __init__(self):
      self.buffer = io.BytesIO()
      self.counter = 0

   def connection_made(self, transport):
      self.transport = transport

   def data_received(self, data):
      "append to part, write and truncate if full"
      parts = data.split(BOUNDARY)
      # If data contains no boundary marker, there is only
      # one non-empty part equal to the data (1).
      # If data has a boundary marker at either end,
      # we may have empty first or last part (2).
      # If the data consists of boundary marker only, we 
      # may have two empty parts (3).

      # We split data by boundary value, and after that
      # interleave the resulting parts using None as
      # separator, to simplify processing. The resulting
      # possible extra checks at beginning and end
      # are inconsequential.

      parts = data.split(BOUNDARY)
      separators = [None for i in range(len(parts))]
      paired = zip(parts, separators)
      interleaved = list(itertools.chain(*paired))

      for part in interleaved:
         if part:
            self.buffer.write(part)
         else: # boundary or separator
            data = self.buffer.getvalue()
            if data:
               self.complete_part()
               logger.info("got part %s" % self.counter)

   def complete_part(self, data=None):
      self.counter += 1
      if data:
         self.buffer.write(data)
      part = self.buffer.getvalue()
      with open("data/part_%i.jpg" % self.counter, "wb") as partfile:
         partfile.write(part)
      self.buffer.seek(0)
      self.buffer.truncate(0)


def start_stream_receiver(loop, ip, port):
   proto = ReceiveMultipartStreamProtocol
   coro = loop.create_server(proto, ip, port)
   task = asyncio.Task(coro)
   server = loop.run_until_complete(task)
   return server


if __name__ == '__main__':
   args = docopt(__doc__, version=version)

   loop = asyncio.get_event_loop()
   loop.add_signal_handler(signal.SIGINT, loop.stop)

   stream_receiver_transport = start_stream_receiver(loop, HOST, args["<stream_port>"])
   logger.info("starting stream receiver at port %s" % args["<stream_port>"])

   try:
      with open("streamsink.pid", "w") as pidfile:
         pidfile.write(str(os.getpid()))
      loop.run_forever()
   finally:
      stream_receiver_transport.close()
      loop.close()
      os.remove("streamsink.pid")
