#!/usr/bin/env python2
"""Classes to enable painless process-level parallelism."""
import traceback
import os
import signal
import multiprocessing
from multiprocessing import Value
import ctypes
try:
    from Queue import Empty, Full
except ImportError:
    from queue import Empty, Full
try:
    from _thread import interrupt_main
except ImportError:
    from thread import interrupt_main

from data import data
import concurrency

# WORKER POOLS

class EarlyTermination(Exception):
    """A custom exception used when multiprocessing workers are terminated early.
    Raise this when the worker in a pool needs to terminate early.
    """
    pass

class Workset():
    """An interface for embarrassingly parallelizable work.
    Extend this to implement a set of work units for a worker pool to handle.
    """

    def work(self, work_id):
        """The method which gets executed on each worker, with a unique work_id."""
        pass

    def work_ids(self):
        """The method which defines the immutable work_ids for the work units."""

    def handle_early_termination(self, work_id):
        """The method called when a worker is terminated early by Ctrl+C."""
        pass

    def handle_exception(self, work_id, e):
        """The method called when a worker is terminated early by an exception."""
        pass

    def __call__(self, work_id):
        try:
            self.work(work_id)
        except EarlyTermination:
            self.handle_early_termination(work_id)
        except Exception as e:
            self.handle_exception(work_id, e)

    def execute_sequential(self):
        """Executes work sequentially in the current process."""
        for work_id in self.work_ids():
            self(work_id)

    def execute_parallel(self, num_processes=(multiprocessing.cpu_count() - 1)):
        print('Initializing pool of ' + str(num_processes) + ' worker processes...')
        pool = multiprocessing.Pool(processes=num_processes)
        try:
            print('Distributing work across workers...')
            pool.map(self, self.work_ids())
            pool.close()
            print('Finished work.')
        except (KeyboardInterrupt, EarlyTermination):
            print('Terminating work pool...')
            pool.terminate()
            print('Terminated work pool.')
        except Exception as e:
            print(e)
            print('Terminating pool...')
            pool.terminate()
            print('Terminated pool.')
        finally:
            print('Joining workers.')
            pool.join()
            print('Finished.')

# SYNCHRONIZATION WITH POLLING

def get_queue_poll(queue, block=True, timeout=None):
    """Gets the next item in the queue.
    If block is True and timeout is not None, periodically polls for interrupts while waiting
    so interrupts can be caught.
    If block is False, raises Empty if there is nothing to get.
    """
    while block:
        try:
            return queue.get(block, timeout)
        except Empty:
            pass
    return queue.get_nowait()

def put_queue_poll(queue, obj, block=True, timeout=None):
    """Gets the next item in the queue.
    If block is True and timeout is not None, periodically polls for interrupts while waiting
    so interrupts can be caught.
    If block is False, raises Full if there is nowhere to put.
    """
    while block:
        try:
            return queue.put(obj, block, timeout)
        except Full:
            pass
    return queue.put_nowait(obj)

def wait_event_poll(event, timeout=None):
    """Sleeps until the event is set.
    If block is True and timeout is not None, periodically polls for interrupts while waiting
    so interrupts can be caught.
    """
    while not event.wait(timeout):
        pass

def acquire_lock_poll(lock, block=True, timeout=None):
    """Acquires the lock.
    If block is True and timeout is not None, periodically polls for interrupts while waiting
    so interrupts can be caught.
    If block is False, returns whether the lock acquisition successfully completed.
    """
    if block:
        while not lock.acquire(block, timeout):
            pass
        return True
    else:
        return lock.acquire(False)

# SYNCHRONIZED PARALLELISM

def flush_queue(queue):
    try:
        for item in iter(queue.get_nowait, None):
            pass
    except Empty:
        pass

class ExceptionListener(concurrency.Thread):
    """A thread which passes exceptions from an associated child process.
    Listens for exceptions received by the send method from any process.
    Upon receipt of an exception, saves exception information to the exception
    attribute, and interrupts the main thread with a KeyboardInterrupt.
    """
    def __init__(self, process_name):
        super(ExceptionListener, self).__init__()
        self.process_name = process_name
        self.queue = multiprocessing.Queue(1)
        self.exception = None

    def send(self, child_name, child_pid, e, traceback, block=True, timeout=1):
        put_queue_poll(self.queue, {
            'child_name': child_name,
            'child_pid': child_pid,
            'exception': e,
            'traceback': traceback
        }, block, timeout)

    def receive_exception(self, block=True, timeout=0.1):
        exception_received = False
        try:
            self.exception = self.queue.get(block, timeout)
            exception_received = True
        except Empty:
            pass
        if exception_received:
            print('Interrupting main thread from ' +
                  repr(self.exception['exception']) +
                  ' raised in child ' + self.exception['child_name'] +
                  ' (pid ' + str(self.exception['child_pid']) + '):\n' +
                  self.exception['traceback'])
            interrupt_main()

    def reset(self, clear_exception=False):
        flush_queue(self.queue)
        if clear_exception:
            self.exception = None

    # From Thread

    @property
    def name(self):
        return self.process_name + ' ' + self.__class__.__name__

    def execute(self):
        self.receive_exception()

    def on_run_parent_start(self):
        self.exception = None

class Process(object):
    """Abstract base class for child processes synchronized over input and output queues.
    Data in the input queue is processed in FIFO order.
    None in the input queue is a sentinel for the child process to exit.
    Exceptions in the child process are saved in the exception property; uncaught
    exceptions raised from the child process will interrupt the main thread with a
    KeyboardInterrupt.
    """
    def __init__(self, max_input_queue_size, max_output_queue_size, *args, **kwargs):
        super(Process, self).__init__(*args, **kwargs)
        self.__process = None
        self._input_queue = multiprocessing.Queue(max_input_queue_size)
        self._output_queue = multiprocessing.Queue(max_output_queue_size)
        self.__exception_listener = ExceptionListener(self.name)

    @property
    def name(self):
        """The name of the process.
        Override this to use something other than the name of the derived class."""
        return self.__class__.__name__

    @property
    def process_running(self):
        return self.__process is not None

    @property
    def pid(self):
        return self.__process.pid

    # Child methods

    def on_run_start(self):
        """Do any work in the child before execute starts being called.
        Implement this."""
        pass

    def execute(self, next_input):
        """Do work on the input
        Implement this with an input handler."""
        pass

    def on_run_finish(self):
        """Do any work in the child after execute stops being called.
        Implement this."""
        pass

    def receive_input(self, block=True, timeout=1):
        """Retrieve the next input from the input queue.
        By default, this blocks with a timeout of 1 to allow preemptive child
        termination with a max delay of 1 second if the child is already active and
        waiting for input when it receives an interrupt.
        """
        return get_queue_poll(self._input_queue, block, timeout)

    def send_output(self, next_output, block=True, timeout=1):
        put_queue_poll(self._output_queue, next_output, block, timeout)

    def send_exception(self, child_name, child_pid, e, traceback):
        self.__exception_listener.send(child_name, child_pid, e, traceback)

    def run_serial(self, block=True, timeout=1):
        """Perform the work in the current execution thread.
        Only usable if inputs and outputs are being exchanged with another thread."""
        try:
            self.on_run_start()
            while True:
                next_input = self.receive_input(block, timeout)
                if next_input is None:
                    break
                else:
                    self.execute(next_input)
            self.on_run_finish()
        except BaseException as e:
            print('Raising exception from child ' + self.name +
                  ' (pid ' + str(self.pid) + ') to parent:')
            print(repr(e))
            traceback.print_exc()
            self.send_exception(self.name, self.pid, e, traceback.format_exc())

    # Parent methods

    @property
    def exception(self):
        """The last-raised exception.
        If no exception has been raised, returns None."""
        return self.__exception_listener.exception

    def on_run_parent_start(self):
        """Do any work in the parent when run_parallel is called.
        Implement this."""
        pass

    def run_parallel(self):
        """Perform the work in a new parallel process.
        Catch KeyboardInterrupts and check the exception property to catch exceptions
        from the child."""
        if self.process_running:
            return
        self.__process = multiprocessing.Process(
            target=self.run_serial, name=self.name
        )
        self.__exception_listener.run_concurrent()
        self.__process.start()
        self.on_run_parent_start()

    def send_input(self, next_input, block=True, timeout=1):
        put_queue_poll(self._input_queue, next_input, block, timeout)

    def receive_output(self, block=True, timeout=1):
        return get_queue_poll(self._output_queue, block, timeout)

    def on_terminate(self):
        """Do any work in the parent right before termination.
        Implement this."""
        pass

    def on_terminate_finish(self):
        """Do any work in the parent right after termination.
        Implement this."""
        pass

    def terminate(self, force_terminate=False):
        self.on_terminate()
        if not self.process_running:
            return
        if force_terminate:
            self.__process.terminate()
        else:
            self.send_input(None)
            self.__process.join()
        self.__exception_listener.terminate()
        self.__exception_listener.reset()
        self.__process = None
        self.on_terminate_finish()

    def kill(self, sig=signal.SIGINT):
        os.kill(self.pid, sig)

    def flush_queues(self):
        flush_queue(self._input_queue)
        flush_queue(self._output_queue)

# DOUBLE-BUFFERED SYNCHRONIZATION

class DoubleBuffer(object):
    """Abstract base class for double buffering.
    The read buffer is used for reading, while the write buffer is used for writing
    the next read buffer.
    Note that only the locks and event are synchronized across processes.
    """
    def __init__(self):
        self._buffer_id = Value(ctypes.c_int)
        self._buffer_id.value = 0
        self._buffer_locks = [multiprocessing.Lock(), multiprocessing.Lock()]
        self._buffer_readable_events = [multiprocessing.Event(), multiprocessing.Event()]

    def get_buffer(self, buffer_id):
        """Gets the buffer at the specified id.
        Implement this. Only Value and Array-backed references in the buffer will be synchronized.
        """
        pass

    def swap(self):
        self._buffer_id.value = 1 - self._buffer_id.value

    @property
    def read_id(self):
        return self._buffer_id.value

    @property
    def write_id(self):
        return 1 - self._buffer_id.value

    @property
    def read_buffer(self):
        return self.get_buffer(self.read_id)

    @property
    def write_buffer(self):
        return self.get_buffer(self.write_id)

    @property
    def read_lock(self):
        return self._buffer_locks[self.read_id]

    @property
    def write_lock(self):
        return self._buffer_locks[self.write_id]

    @property
    def read_readable(self):
        return self._buffer_readable_events[self.read_id]

    @property
    def write_readable(self):
        return self._buffer_readable_events[self.write_id]

    def release_locks(self):
        for lock in self._buffer_locks:
            try:
                lock.release()
            except ValueError:
                pass

    def reset(self):
        self.read_readable.clear()
        self.write_readable.clear()
        self.release_locks()
        self._buffer_id.value = 0

class DoubleBufferedProcess(Process):
    """A Process which supports double-buffering.
    Assumes the child writes to the buffer and the parent reads and swaps the buffer,
    though other configurations might also work well with this interface.
    DoubleBufferFactory needs to return an object which is a DoubleBuffer without any
    calling arguments.
    """
    def __init__(self, DoubleBufferFactory, max_input_queue_size, max_output_queue_size,
                 *args, **kwargs):
        super(DoubleBufferedProcess, self).__init__(
            max_input_queue_size, max_output_queue_size, *args, **kwargs)
        self.double_buffer = DoubleBufferFactory()

    @property
    def read_buffer(self):
        return self.double_buffer.read_buffer

    # Child methods

    def on_write_to_buffer(self, data, write_buffer):
        """Write the data to the double buffer's write buffer.
        Impelement this."""
        pass

    def write_to_buffer(self, data):
        acquire_lock_poll(self.double_buffer.write_lock, block=True, timeout=None)
        self.on_write_to_buffer(data, self.double_buffer.write_buffer)
        self.double_buffer.write_readable.set()
        self.double_buffer.write_lock.release()

    # Parent methods

    def swap_buffers(self):
        """Swaps the read and write buffers.
        Upon completion, the parent is ready to read from the new read buffer and the
        child is ready to write to the new write buffer.
        Assumes the parent has the lock on the old read buffer and no longer needs the
        data in the buffer, so that it's ready for the child to start writing to it.
        Before swapping, waits for the write buffer to become readable and lockable.
        Upon completion, the parent has the lock on the new read buffer, the new
        write buffer is no longer marked as readable, and the child is free to lock
        the new write buffer.
        """
        # Assumes the parent has the read lock and no longer needs the read buffer's data
        wait_event_poll(self.double_buffer.write_readable)
        # Lock the write buffer so we can read from it when it becomes a read buffer
        acquire_lock_poll(self.double_buffer.write_lock, block=True, timeout=1)
        # Swap buffers, so that our locked buffer becomes the new read buffer
        self.double_buffer.swap()
        # Reset and release our unneeded buffer as the new write buffer
        self.double_buffer.write_readable.clear()
        self.double_buffer.write_lock.release()

class LoaderGeneratorProcess(DoubleBufferedProcess, data.DataLoader, data.DataGenerator):
    """Abstract base class for a Loader/Generator which runs in a separate process.
    Implementation requires implementing the on_write_to_buffer, marshal_output, and
    unmarshal_output methods.
    LoaderGeneratorFactory needs to return an object which is a Loader and a Generator
    without any calling arguments.
    DoubleBufferFactory needs to return an object which is a DoubleBuffer without any
    calling arguments.
    """
    def __init__(self, LoaderGeneratorFactory, DoubleBufferFactory, *args, **kwargs):
        super(LoaderGeneratorProcess, self).__init__(
            DoubleBufferFactory, 1, 1, *args, **kwargs)
        self.loader = LoaderGeneratorFactory()

    # Child methods

    def marshal_output(self, loaded_next):
        """Generate the contents of the output queue message.
        Override this to pass custom picklable data over the output queue without
        having to store it into the double buffer."""
        return True

    def _load_next(self):
        try:
            loaded_next = next(self.loader)
            self.write_to_buffer(loaded_next)
            self.send_output({
                'next': self.marshal_output(loaded_next)
            })
        except StopIteration:
            self.double_buffer.write_readable.set()
            self.send_output(None)

    # From Process

    def on_run_parent_start(self):
        # Set up assumptions/loop invariants of the next() call
        acquire_lock_poll(self.double_buffer.read_lock, block=True, timeout=1)
        self.send_input('next')  # let child load the first value into the write buffer

    def on_terminate_finish(self):
        super(LoaderGeneratorProcess, self).stop_loading()

    def on_run_start(self):
        self.loader.load()

    def execute(self, next_input):
        if next_input == 'next':
            self._load_next()

    def on_run_finish(self):
        self.loader.stop_loading()

    # From DataGenerator

    def unmarshal_output(self, marshalled, read_buffer):
        """Given the marshalled data and the read buffer, reconstruct the data.
        Implement this to reconstruct the data to be returned from next()."""
        pass

    def next(self):
        self.swap_buffers()
        self.send_input('next')  # let the child start writing to the new write buffer
        output = self.receive_output()  # receive the output associated with the new read buffer
        if output is not None:
            return self.unmarshal_output(output['next'], self.double_buffer.read_buffer)
        else:
            raise StopIteration

    def reset(self):
        self.stop_loading()
        self.double_buffer.reset()
        self.flush_queues()

    # From DataLoader

    def load(self):
        self.run_parallel()

    def stop_loading(self):
        self.terminate()

