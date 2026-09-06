"""Operational machinery that is not part of the advice path.

`ops/` holds the headless lane: the lock that decides who may run, the launcher
that turns a claim into a worker, and the driver that repeats it. Nothing here
is imported by `clockspeed/` - the dependency runs one way only, so a lane fault
can never reach the advice path.
"""
