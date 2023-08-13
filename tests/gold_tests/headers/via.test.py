'''
Test the VIA header. This runs several requests through ATS and extracts the upstream VIA headers.
Those are then checked against a gold file to verify the protocol stack based output is correct.
'''

#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os

Test.Summary = '''
Check VIA header for protocol stack data.
'''

Test.SkipUnless(
    Condition.HasCurlFeature('http2'),
    Condition.HasCurlFeature('IPv6')
)
Test.ContinueOnFail = True

# Define default ATS
if Condition.HasATSFeature('TS_USE_QUIC') and Condition.HasCurlFeature('http3'):
    ts = Test.MakeATSProcess("ts", enable_tls=True, enable_quic=True)
else:
    ts = Test.MakeATSProcess("ts", enable_tls=True)


server = Test.MakeOriginServer("server", options={'--load': os.path.join(Test.TestDirectory, 'via-observer.py')})

testName = "VIA"

# We only need one transaction as only the VIA header will be checked.
request_header = {"headers": "GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n", "timestamp": "1469733493.993", "body": ""}
response_header = {"headers": "HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n", "timestamp": "1469733493.993", "body": ""}
server.addResponse("sessionlog.json", request_header, response_header)

# These should be promoted rather than other tests like this reaching around.
ts.addDefaultSSLFiles()

ts.Disk.records_config.update({
    'proxy.config.http.insert_request_via_str': 4,
    'proxy.config.http.insert_response_via_str': 4,
    'proxy.config.ssl.server.cert.path': '{0}'.format(ts.Variables.SSLDir),
    'proxy.config.ssl.server.private_key.path': '{0}'.format(ts.Variables.SSLDir),
})

ts.Disk.remap_config.AddLine(
    'map http://www.example.com http://127.0.0.1:{0}'.format(server.Variables.Port)
)
ts.Disk.remap_config.AddLine(
    'map https://www.example.com http://127.0.0.1:{0}'.format(server.Variables.Port, ts.Variables.ssl_port)
)

ts.Disk.ssl_multicert_config.AddLine(
    'dest_ip=* ssl_cert_name=server.pem ssl_key_name=server.key'
)

# Set up to check the output after the tests have run.
via_log_id = Test.Disk.File("via.log")
if Condition.HasATSFeature('TS_USE_QUIC') and Condition.HasCurlFeature('http3'):
    via_log_id.Content = "via_h3.gold"
else:
    via_log_id.Content = "via.gold"

# Basic HTTP 1.1
tr = Test.AddTestRun()
# Wait for the micro server
tr.Processes.Default.StartBefore(server, ready=When.PortOpen(server.Variables.Port))
# Delay on readiness of our ssl ports
tr.Processes.Default.StartBefore(Test.Processes.ts)

tr.Processes.Default.Command = f'curl --verbose --ipv4 --http1.1 --proxy localhost:{ts.Variables.port} http://www.example.com'
tr.Processes.Default.ReturnCode = 0

tr.StillRunningAfter = server
tr.StillRunningAfter = ts

# HTTP 1.0
tr = Test.AddTestRun()
tr.Processes.Default.Command = f'curl --verbose --ipv4 --http1.0 --proxy localhost:{ts.Variables.port} http://www.example.com'
tr.Processes.Default.ReturnCode = 0

tr.StillRunningAfter = server
tr.StillRunningAfter = ts

# HTTP 2
tr = Test.AddTestRun()
tr.Processes.Default.Command = f'curl --verbose --ipv4 --http2 --insecure --header "Host: www.example.com" https://localhost:{ts.Variables.ssl_port}'
tr.Processes.Default.ReturnCode = 0

tr.StillRunningAfter = server
tr.StillRunningAfter = ts

# HTTP 3
if Condition.HasATSFeature('TS_HAS_QUICHE') and Condition.HasCurlFeature('http3'):
    tr = Test.AddTestRun()
    tr.Processes.Default.Command = f'curl --verbose --ipv4 --http3 --insecure --header "Host: www.example.com" https://localhost:{ts.Variables.ssl_port}'
    tr.Processes.Default.ReturnCode = 0
    tr.StillRunningAfter = server
    tr.StillRunningAfter = ts

# TLS
tr = Test.AddTestRun()
tr.Processes.Default.Command = f'curl --verbose --ipv4 --http1.1 --insecure --header "Host: www.example.com" https://localhost:{ts.Variables.ssl_port}'
tr.Processes.Default.ReturnCode = 0

tr.StillRunningAfter = server
tr.StillRunningAfter = ts

# IPv6
tr = Test.AddTestRun()
tr.Processes.Default.Command = f'curl --verbose --ipv6 --http1.1 --proxy localhost:{ts.Variables.portv6} http://www.example.com'
tr.Processes.Default.ReturnCode = 0
tr.StillRunningAfter = server
tr.StillRunningAfter = ts

tr = Test.AddTestRun()
tr.Processes.Default.Command = f'curl --verbose --ipv6 --http1.1 --insecure --header "Host: www.example.com" https://localhost:{ts.Variables.ssl_portv6}'
tr.Processes.Default.ReturnCode = 0

tr.StillRunningAfter = server
tr.StillRunningAfter = ts
