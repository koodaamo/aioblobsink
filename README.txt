aioblobsink - a binary object stream receiver

This package implements a pluggable asynchronous TCP/IP server for receiving
binary objects separated by a configurable boundary marker.

The server can save received binary objects to disk or pass them on to
third-party application code for processing.

Application examples include receiving a mjpeg stream pushed by a webcam and
then saving the stream to disk, or showing it using a web app.
