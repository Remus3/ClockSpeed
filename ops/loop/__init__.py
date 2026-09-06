"""The headless `queue` lane - lock, launcher, runner and driver.

See `ops/loop/queue_loop.py` for why the DRIVER owns every wait and the worker
owns none, and `docs/OPERATIONS.md` for how to fire and stop the lane.
"""
