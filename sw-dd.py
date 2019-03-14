#!/usr/bin/env python

import os
import re
import time
from dateutil import parser
from datetime import datetime
import pytz
from datadog import initialize, api
from pygtail import Pygtail

pattern = re.compile("""(?P<date>[0-9A-z-:]+) (?P<host>[a-z0-9]+) (?P<app>[%A-z0-9:]+) (?P<dd_key>[a-z0-9]+) (?P<connection>.*) - (?P<port_and_box>[^|]*)\|  RX (?P<rx>[0-9]+) %  \|  TX (?P<tx>[0-9]+) %""")


options = {
    'api_key': os.environ.get('DD_KEY')
}
initialize(**options)


while True:
    for line in Pygtail("/var/log/syslog", offset_file='/tmp/syslog.offset'):
        if 'vawvorion01' in line:
            match = pattern.match(line)
            if not match:
                print repr(line)
                continue
            data = match.groupdict()
            connection = data['connection'].replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('_', '')
            ts = (parser.parse(data['date']) - datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds()
            print ts
            for direction in ('tx', 'rx'):
                print api.Metric.send(
                    host=data['host'],
                    metric='solarwinds.network.%s.%s' % (connection, direction),
                    points=[(ts, int(data[direction]))],
                    type='gauge')
    time.sleep(30)
