#!/usr/bin/env python2
"""Classes to enable painless process-level parallelism."""
import threading

class Thread(object):
    """Abstract convenience class for work done concurrently in a thread."""
    def __init__(self):
        self._thread = None
        self._run = False

    @property
    def name(self):
        """The name of the thread.
        Override this to use something other than the name of the derived class."""
        return self.__class__.__name__

    # Child methods

    def on_run_start(self):
        """Do any work in the child before execute starts being called.
        Implement this."""
        pass

    def execute(self):
        """Do the work.
        Implement this with the work to be done. If the work never ends,
        it needs to check self._run to be able to be preemptively terminated.
        If the work does end, it will be called repeatedly as long as self._run is True."""
        pass

    def on_run_finish(self):
        """Do any work in the child after execute stops being called.
        Implement this."""
        pass

    def run_serial(self):
        """Perform the work in the current execution thread."""
        self._run = True
        self.on_run_start()
        while self._run:
            self.execute()
        self.on_run_finish()

    # Parent methods

    def on_run_parent_start(self):
        """Do any work in the parent before execute starts being called.
        Implement this."""
        pass

    def run_concurrent(self):
        """Perform the work in a new concurrent thread."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self.run_serial, name=self.name)
        self.on_run_parent_start()
        self._thread.start()

    def on_terminate(self):
        """Do any work in the parent right before termination.
        Implement this."""
        pass

    def on_terminate_finish(self):
        """Do any work in the parent right after termination.
        Implement this."""
        pass

    def terminate(self):
        self.on_terminate()
        self._run = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self.on_terminate_finish()

