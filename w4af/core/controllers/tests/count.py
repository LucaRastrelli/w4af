"""
count.py

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
import time

from w4af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w4af.core.controllers.ci.moth import get_moth_http
from w4af.core.data.parsers.doc.url import URL


class count(CrawlPlugin):
    """
    This is a test plugin that will count how many times it called
    xurllib.GET and expose that as an attribute.
    
    Only useful for testing, see test_w4afcore.py

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        self.count = 0
        self.loops = 20

    def crawl(self, fuzzable_req, debugging_id):
        for i in range(self.loops):
            self._uri_opener.GET(URL(get_moth_http('/%s' % i)))
            self.count += 1
            time.sleep(0.5)
