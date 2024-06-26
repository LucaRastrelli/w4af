"""
output_manager.py

Copyright 2006 Andres Riancho

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
import urllib.request, urllib.error, urllib.parse

import w4af.core.controllers.output_manager as om

from w4af.core.data.url.HTTPResponse import HTTPResponse
from w4af.core.data.url.HTTPRequest import HTTPRequest


class OutputManagerHandler(urllib.request.BaseHandler):
    """
    Send the HTTP request and response to the output manager
    """

    handler_order = urllib.request.HTTPErrorProcessor.handler_order - 1

    def http_response(self, request, response):
        self._log_req_resp(request, response)
        return response

    https_response = http_response

    def _log_req_resp(self, request, response):
        """
        Send the request and the response to the output manager.
        """
        if not isinstance(response, HTTPResponse):
            url = request.url_object
            resp = HTTPResponse.from_httplib_resp(response,
                                                  original_url=url)
            resp.set_id(response.id)
        else:
            resp = response
            
        if not isinstance(request, HTTPRequest):
            msg = ('There is something odd going on in OutputManagerHandler,'
                   ' request should be of type HTTPRequest got %s'
                   ' instead.')
            raise TypeError(msg % type(request))

        om.out.log_http(request, resp)
