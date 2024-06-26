"""
vulns.py

Copyright 2012 Andres Riancho

This file is part of w4af, http://w4af.net/ .

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
VULNS = {
         'TestCase': None,

         # Core
         'Target redirect': None,

         # Audit
         'Blind SQL injection vulnerability': 46,
         'Buffer overflow vulnerability': None,
         'Sensitive CORS methods enabled': None,
         'Uncommon CORS methods enabled': None,
         'Access-Control-Allow-Origin set to "*"': None,
         'Insecure Access-Control-Allow-Origin with credentials': None,
         'Insecure Access-Control-Allow-Origin': None,
         'Incorrect withCredentials implementation': None,
         'CSRF vulnerability': 13,
         'Insecure DAV configuration': 52,
         'Publicly writable directory': 23,
         'DAV incorrect configuration': None,
         'Insecure file upload': 65,
         'Format string vulnerability': None,
         'Insecure Frontpage extensions configuration': 69,
         'Insecure redirection': 50,
         'Misconfigured access control': 20,
         'LDAP injection vulnerability': 30,
         'Local file inclusion vulnerability': 17,
         'File read error': 73,
         'MX injection vulnerability': None,
         'OS commanding vulnerability': 36,
         'Phishing vector': 74,
         'Unsafe preg_replace usage': None,
         'ReDoS vulnerability': None,
         'Response splitting vulnerability': 41,
         'Remote code execution': 42,
         'Remote file inclusion': 42,
         'Potential remote file inclusion': 42,
         'SQL injection': 45,
         'Server side include vulnerability': None,
         'Persistent server side include vulnerability': None,
         'Insecure SSL version': 66,
         'Self-signed SSL certificate': 67,
         'Invalid SSL connection': None,
         'Soon to expire SSL certificate': None,
         'SSL Certificate dump': None,
         'Secure content over insecure channel': None,
         'XPATH injection vulnerability': 54,
         'Persistent Cross-Site Scripting vulnerability': 70,
         'Cross site scripting vulnerability': 55,
         'Cross site tracing vulnerability': 63,
         'Parameter modifies response headers': None,
         'eval() input injection vulnerability': 6,
         'Reflected File Download vulnerability': 71,
         'Shell shock vulnerability': 68,
         'Rosetta Flash': None,
         'Memcache injection vulnerability': None,

         # WebSockets
         'Insecure WebSocket Origin filter': None,
         'Open WebSocket': None,
         'Origin restricted WebSocket': None,
         'Websockets CSRF vulnerability': None,

         # Crawl
         'dwsync.xml file found': None,
         'phpinfo() file found': None,
         'PHP register_globals: On': None,
         'PHP allow_url_fopen: On': None,
         'PHP allow_url_include: On': None,
         'PHP display_errors: On': None,
         'PHP expose_php: On': None,
         'PHP lowest_privilege_test:fail': None,
         'PHP disable_functions:few': None,
         'PHP curl_file_support:not_fixed': None,
         'PHP cgi_force_redirect: Off': None,
         'PHP session.cookie_httponly: Off': None,
         'PHP session_save_path:Everyone': None,
         'PHP session_use_trans: On': None,
         'PHP default_charset: Off': None,
         'PHP enable_dl: On': None,
         'PHP memory_limit:high': None,
         'PHP post_max_size:high': None,
         'PHP upload_max_filesize:high': None,
         'PHP upload_tmp_dir:Everyone': None,
         'PHP file_uploads: On': None,
         'PHP magic_quotes_gpc: On': None,
         'PHP magic_quotes_gpc: Off': None,
         'PHP open_basedir:disabled': None,
         'PHP open_basedir:enabled': None,
         'PHP session.hash_function:md5': None,
         'PHP session.hash_function:sha': None,
         'Insecure URL': 9,
         '.listing file found': None,
         'Operating system username and group leak': None,
         'Google hack database match': None,
         'Phishing scam': None,
         'Source code repository': 14,
         'Insecure RIA settings': None,
         'Cross-domain allow ACL': None,
         'Potential web backdoor': 2,
         'Captcha image detected': 5,
         'Oracle Application Server': None,
         'Potentially interesting file': 4,
         'urllist.txt file': None,
         'Fingerprinted operating system': None,
         'Identified installed application': None,
         'robots.txt file': None,
         'HTTP Content Negotiation enabled': None,
         'Fingerprinted Wordpress version': None,
         'Gears manifest resource': None,
         'Invalid RIA settings file': None,
         'Identified WordPress user': None,
         'WordPress path disclosure': None,
         'PHP register_globals: Off': None,
         'PHP enable_dl: Off': None,
         'Web user home directory': None,
         
         # Grep
         'US Social Security Number disclosure': 48,
         'DOM Cross site scripting': 56,
         'Parameter has SQL sentence': None,
         'Uncommon query string parameter': None,
         'Credit card number disclosure': 12,
         'Code disclosure vulnerability': 44,
         'Code disclosure vulnerability in 404 page': 44,
         'Unhandled error in web application': 73,
         'Basic HTTP credentials': None,
         'Authentication without www-authenticate header': None,
         'NTLM authentication': None,
         'HTTP Basic authentication': 77,
         'Cookie without HttpOnly': 22,
         'Secure cookie over HTTP': None,
         'Secure flag missing in HTTPS cookie': 25,
         'Secure cookies over insecure channel': None,
         'Identified cookie': None,
         'Cookie': None,
         'Invalid cookie': None,
         'Click-Jacking vulnerability': 53,
         'Private IP disclosure vulnerability': 40,
         'Directory indexing': 15,
         'Path disclosure vulnerability': None,
         'Missing cache control for HTTPS content': 72,
         'SVN user disclosure vulnerability': None,
         'HTTP Request in HTTP body': None,
         'HTTP Response in HTTP body': None,
         'Auto-completable form': 38,
         'Session ID in URL': None,
         'WSDL resource': None,
         'DISCO resource': None,
         'Symfony Framework with CSRF protection disabled': None,
         'Descriptive error page': 73,
         'Multiple descriptive error pages': 73,
         'Error page with information disclosure': 73,
         'Oracle application server': None,
         'Strange header': None,
         'Content-Location HTTP header anomaly': None,
         '.NET Event Validation is disabled': None,
         '.NET ViewState encryption is disabled': None,
         'Email address disclosure': 16,
         'Interesting HTML comment': None,
         'HTML comment contains HTML code': None,
         'Strange HTTP response code': 29,
         'File upload form': 18,
         'Interesting META tag': None,
         'User defined regular expression match': None,
         'Mark of the web': None,
         'Cross-domain javascript source': None,
         'Insecure X-XSS-Protection header usage': None,
         'Browser plugin content': None,
         'Strange HTTP Reason message': None,
         'Hash string in HTML content': None,
         'Blank http response body': None,
         'Content feed resource': None,
         'Malware identified': None,
         'Insecure password submission over HTTP': 49,
         'CSP vulnerability': None,
         'Missing X-Content-Type-Options header': 76,
         'Missing Strict Transport Security header': 19,
         'Missing Expect-CT header': None,
         'HTML5 WebSocket detected': None,
         'Insecure password form access over HTTP': 49,
         
         # Infrastructure
         'Potential XSS vulnerability': None,
         'HTTP and HTTPs hop distance': None,
         'HTTP traceroute': None,
         'Apache Server version': None,
         'Shared hosting': None,
         'Virtual host identified': None,
         'Previous defacements': None,
         'Email account': None,
         'Internal hostname in HTML link': None,
         'Default virtual host': None,
         'No DNS wildcard': None,
         'DNS wildcard': None,
         'Webserver fingerprint': None,
         'Web Application Firewall fingerprint': None,
         'FrontPage configuration information': None,
         'Customized frontpage configuration': None,
         'FrontPage FPAdminScriptUrl': None,
         'Operating system': None,
         'Favicon identification': None,
         'Favicon identification failed': None,
         'Transparent proxy detected': None,
         'PHP Egg': None,
         'Fingerprinted PHP version': None,
         'Server header': None,
         'Omitted server header': None,
         'Powered-by header': None,
         'Non existent methods default to GET': None,
         'DAV methods enabled': None,
         'Allowed HTTP methods': 1,
         'Active filter detected': None,
         'Reverse proxy identified': None,
         'HTTP load balancer detected': None,
         'Information disclosure via .NET errors': 73,
         'Potential virtual host misconfiguration': None,
         'MS15-034': None,
         'JetLeak': None,
         'Werkzeug debugger enabled': None,
         
         # Bruteforce
         'Guessable credentials': 75,

         # Attack
         'DAV Misconfiguration': 23,
         'Arbitrary file upload': 65,
         'OS Commanding code execution': 36,
         'Code execution via remote file inclusion': 42,
         '(Blind) SQL injection': 46,
         'Arbitrary file read': 17,
         'Eval() code execution': 6,

         # Users can add their vulnerabilities
         'Manually added vulnerability': None,
         }


def is_valid_name(name):
    return name in VULNS
