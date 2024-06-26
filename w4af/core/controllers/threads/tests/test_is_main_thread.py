"""
test_is_main_thread.py

Copyright 2019 Andres Riancho

This file is part of w4af, https://w4af.net/ .

w4af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w4af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w4af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import unittest
import threading
import queue

from w4af.core.controllers.threads.is_main_thread import is_main_thread


class TestIsMainThread(unittest.TestCase):

    def test_true(self):
        self.assertTrue(is_main_thread())

    def test_false(self):
        def thread_func(result_queue):
            result_queue.put(is_main_thread())

        result_queue = queue.Queue()

        t = threading.Thread(target=thread_func, args=(result_queue,))
        t.start()
        t.join()

        result = result_queue.get()

        self.assertFalse(result)
