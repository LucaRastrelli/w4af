"""
seed.py

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
import traceback

from queue import Empty
from multiprocessing.dummy import Queue, Process

import w4af.core.controllers.output_manager as om
import w4af.core.data.kb.knowledge_base as kb

from w4af.core.data.request.fuzzable_request import FuzzableRequest
from w4af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w4af.core.controllers.exceptions import (ScanMustStopException,
                                              HTTPRequestException)


class seed(Process):
    """
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
    requests.
    """

    def __init__(self, w4af_core):
        """
        :param w4af_core: The w4af core that we'll use for status reporting
        """
        super(seed, self).__init__(name='%sController' % self.get_name())

        self._w4af_core = w4af_core

        # See documentation in the property below
        self._out_queue = Queue()

    def get_name(self):
        return 'Seed'

    def get_result(self, timeout=0.5):
        return self._out_queue.get_nowait()

    def has_pending_work(self):
        return self._out_queue.qsize() != 0

    def join(self):
        return

    @property
    def out_queue(self):
        # This output queue can contain one of the following:
        #    * POISON_PILL
        #    * (plugin_name, fuzzable_request, AsyncResult)
        #    * An ExceptionData instance
        return self._out_queue

    def terminate(self):
        while True:
            try:
                self._out_queue.get_nowait()
            except Empty:
                break
            else:
                self._out_queue.task_done()

        om.out.debug('No more tasks in Seed consumer output queue.')

    def seed_output_queue(self, target_urls):
        """
        Create the first fuzzable request objects based on the targets and put
        them in the output Queue.

        This will start the whole discovery process, since plugins are going
        to consume from that Queue and then put their results in it again in
        order to continue discovering.
        """
        # We only want to scan pages that are in current scope
        in_scope = lambda fr: fr.get_url().get_domain() == url.get_domain()

        for url in target_urls:
            try:
                #
                #    GET the initial target URLs in order to save them
                #    in a list and use them as our bootstrap URLs
                #
                response = self._w4af_core.uri_opener.GET(url, cache=True)
            except ScanMustStopException as w3:
                om.out.error('The target server is unreachable. Stopping.')
                raise w3
            except HTTPRequestException as hre:
                msg = 'The target URL: "%s" is unreachable. Exception: "%s".'
                om.out.error(msg % (url, hre))
            except Exception as e:
                msg = ('The target URL: "%s" is unreachable because of an'
                       ' unhandled exception. Error description: "%s". See'
                       ' debug output for more information.\n'
                       'Traceback for this error:\n%s')
                om.out.error(msg % (url, e, traceback.format_exc()))
            else:
                _seed = FuzzableRequest(response.get_uri())

                if in_scope(_seed):
                    self._out_queue.put((None, None, _seed))

                    # Update the set that lives in the KB
                    kb.kb.add_fuzzable_request(_seed)

        self._out_queue.put(POISON_PILL)
