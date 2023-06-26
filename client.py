import requests
import json
import time

scan_profile = open('/home/rastrelli2/.w4af/profiles/OWASP_TOP10.pw4af', 'r')
data = {'scan_profile': scan_profile.read(),
        'target_urls': ['http://192.168.10.11/payroll_app.php']}

response = requests.post('http://127.0.0.1:5000/scans/',
                         data=json.dumps(data),
                         headers={'content-type': 'application/json'})

time.sleep(30)

response = requests.get('http://127.0.0.1:5000/scans/0/stop',
                        data=json.dumps(data),
                         headers={'content-type': 'application/json'})
