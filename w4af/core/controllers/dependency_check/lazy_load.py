"""
lazy_load.py

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
from multiprocessing import Pool


def _module_load_worker(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True


def lazy_load(module_name):
    return _module_load_worker(module_name)

    #TODO: Why isn't this working?
    #pool = Pool(processes=1)
    #result = pool.apply_async(_module_load_worker, [module_name])
    #return result.get(timeout=5)
