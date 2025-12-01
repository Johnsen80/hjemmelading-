"""
Init-fil for src-pakken

This package is intended to be imported by application code. To avoid the
``No handlers could be found for logger XYZ`` one-off warning when the
application using this package does not configure logging, attach a
``NullHandler`` to the top-level package logger here. Library code can then
`logging.getLogger(__name__)` safely without forcing any global logging
configuration.
"""
import logging

# Avoid "No handlers could be found for logger ..." warnings in apps that
# don't configure logging. Libraries should add a NullHandler to their
# top-level logger so they don't emit warnings as a side-effect of being
# imported.
logging.getLogger(__name__).addHandler(logging.NullHandler())
