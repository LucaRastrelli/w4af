"""
test_w4af_console.py

Copyright 2012 Andres Riancho

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
import py_compile
import subprocess
import sys

from w4af.core.data.db.startup_cfg import StartUpConfig


class Testw4afConsole(unittest.TestCase):
    def test_compiles(self):
        try:
            py_compile.compile('w4af_console', '/tmp/foo.tmp', 'exec')
        except SyntaxError as se:
            self.assertTrue(False, 'Error in w4af_console code "%s"' % se)

    def test_get_prompt(self):
        # We want to get the prompt, not a disclaimer message
        startup_cfg = StartUpConfig()
        startup_cfg.accepted_disclaimer = True
        startup_cfg.save()

        # The easy way to do this was to simply pass 'python' to Popen
        # but now that we want to run the tests in virtualenv, we need to
        # find the "correct" / "virtual" python executable using which and
        # then pass that one to Popen
        python_executable = sys.executable
        
        p = subprocess.Popen([python_executable, 'w4af_console', '-n'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             shell=False,
                             universal_newlines=True)

        expected_prompt = 'w4af>>>'
        
        stdout, stderr = p.communicate('exit\r\n')
                
        msg = 'Failed to find "%s" in "%s" using "%s" as python executable.'
        msg = msg % (expected_prompt, stdout, python_executable)
        self.assertIn(expected_prompt, stdout, msg)
