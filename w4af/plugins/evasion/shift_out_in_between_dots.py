"""
shift_out_in_between_dots.py

Copyright 2008 Jose Ramon Palanco

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
from w4af.core.controllers.plugins.evasion_plugin import EvasionPlugin


class shift_out_in_between_dots(EvasionPlugin):
    """
    Insert between dots shift-in and shift-out control characters which are
    cancelled each other when they are below
    
    :author: Jose Ramon Palanco( jose.palanco@hazent.com )
    """
    def modify_request(self, request):
        """
        Mangles the request

        :param request: HTTPRequest instance that is going to be modified by
                        the evasion plugin
        :return: The modified request
        """
        # We mangle the URL
        path = request.url_object.get_path()
        path = path.replace('/../', '/.%0E%0F./')

        # Finally, we set all the mutants to the request in order to return it
        new_url = request.url_object.copy()
        new_url.set_path(path)

        new_req = request.copy()
        new_req.set_uri(new_url)

        return new_req

    def get_priority(self):
        """
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.

        :return: An integer specifying the priority. 100 is run first, 0 last.
        """
        return 20

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return r"""
        This evasion plugin insert between dots shift-in and shift-out control
        characters which are cancelled each other when they are below so some
        ".." filters are bypassed

        Example:
            Input:      '../../etc/passwd'
            Output:     '.%0E%0F./.%0E%0F./etc/passwd'
        """
