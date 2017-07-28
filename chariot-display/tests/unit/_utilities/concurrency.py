#!/usr/bin/env python2
import unittest
import sys
import time

from utilities import concurrency

class TightThread(concurrency.Thread):
    def __init__(self, cooperative=False):
        super(TightThread, self).__init__()
        self.work_started = False
        self.work_counter = 0
        self.work_finished = False
        self.cooperative = cooperative

    def on_run_start(self):
        self.work_started = True
        sys.stdout.write('[')

    def on_run_finish(self):
        self.work_finished = True
        print(']')

    def execute(self):
        time.sleep(0.02)
        self.work_counter += 1
        sys.stdout.write(str(self.work_counter))
        if self.cooperative and self.work_counter >= 6:
            self._run = False
        elif self.work_counter > 1000:
            print('Warning: TightThread should have terminated!')

class LooseThread(concurrency.Thread):
    def __init__(self, cooperative=False):
        super(LooseThread, self).__init__()
        self.work_started = False
        self.work_counter = 0
        self.work_finished = False
        self.cooperative = cooperative

    def on_run_start(self):
        self.work_started = True

    def on_run_finish(self):
        self.work_finished = True
        print()

    def execute(self):
        work_counter = 0
        sys.stdout.write('[')
        while work_counter < 6:
            time.sleep(0.01)
            work_counter += 1
            sys.stdout.write(str(work_counter))
        sys.stdout.write(']')
        self.work_counter += 1
        sys.stdout.write(str(self.work_counter) + ',')
        if self.cooperative and self.work_counter >= 6:
            self._run = False
        elif self.work_counter > 1000:
            print('Warning: LooseThread should have terminated!')

class TestThreading(unittest.TestCase):
    def assert_thread_state(self):
        self.assertFalse(self.thread._run,
                         'Incorrect thread state')
        self.assertTrue(self.thread.work_started,
                        'Incorrect thread state')
        self.assertTrue(self.thread.work_finished,
                        'Incorrect thread state')
        self.assertTrue(self.thread.work_counter >= 6,
                        'Incorrect thread state')

    def test_tight_cooperative_sync(self):
        self.thread = TightThread(cooperative=True)
        self.thread.run_sync()
        self.assert_thread_state()

    def test_tight_cooperative_async(self):
        self.thread = TightThread(cooperative=True)
        self.thread.run_async()
        self.assertEqual(self.thread._thread.name, 'TightThread',
                         'Incorrect thread name')
        while self.thread.work_counter < 6:
            time.sleep(0.01)
        self.assert_thread_state()
        self.thread.terminate()
        self.assertIsNone(self.thread._thread,
                          'Incorrect thread state')

    def test_tight_preemptive(self):
        self.thread = TightThread()
        self.thread.run_async()
        while self.thread.work_counter < 6:
            time.sleep(0.01)
        self.thread.terminate()
        self.assert_thread_state()

    def test_loose_cooperative_sync(self):
        self.thread = LooseThread(cooperative=True)
        self.thread.run_sync()
        self.assert_thread_state()

    def test_loose_cooperative_async(self):
        self.thread = LooseThread(cooperative=True)
        self.thread.run_async()
        self.assertEqual(self.thread._thread.name, 'LooseThread',
                         'Incorrect thread name')
        while self.thread.work_counter < 6:
            time.sleep(0.01)
        self.assert_thread_state()
        self.thread.terminate()
        self.assertIsNone(self.thread._thread,
                          'Incorrect thread state')

    def test_loose_preemptive(self):
        self.thread = LooseThread()
        self.thread.run_async()
        while self.thread.work_counter < 6:
            time.sleep(0.01)
        self.thread.terminate()
        self.assert_thread_state()

