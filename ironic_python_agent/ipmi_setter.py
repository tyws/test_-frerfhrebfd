# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from oslo_config import cfg
from oslo_log import log
import requests

from ironic_python_agent import hardware
from ironic_python_agent import utils

LOG = log.getLogger(__name__)


def set_bm_ipmi(data, failures, retry=3):
    """Set baremetal node's ipmi info.

    make sure that this collector be placed first among
    `inspection_collectors`

    :param data: mutable dict that we'll send to inspector
    :param failures: AccumulatedFailures object
    :param retry: number of retries when failure
    """
    data['set_ipmi'] = {'result': False}
    try:
        sysinfo = hardware\
            .dispatch_to_managers('get_system_vendor_info')
        ip = hardware\
            .dispatch_to_managers('get_bmc_address')
        sn = sysinfo.serial_number
        callback_url = cfg.CONF.inspection_callback_url
        host = callback_url.rsplit(r"/v1/continue")[0]
        resp = requests.get(host + "/v1/bmc/%s" % sn)
        body = resp.json()

        if body:

            if body['ip_address'] == ip:
                data['set_ipmi']['result'] = True
                return

            commands = [
                ('lan', 'set', '1', 'ipsrc', 'static'),
                ('lan', 'set', '1', 'ipaddr', body['ip_address']),
                ('lan', 'set', '1', 'netmask', body['netmask']),
                ('lan', 'set', '1', 'defgw', 'ipaddr', body['gateway']),
            ]

            for cmd in commands:
                utils.execute('ipmitool', *cmd)
            requests.post(
                host + "/v1/bmc/%s" % sn,
                json={"has_set": True}
            )
            data['set_ipmi']['result'] = True

    except Exception as exc:
        if retry > 0:
            LOG.warning('setting ipmi address failed, retry 60s later, '
                        '%s times left', retry)
            time.sleep(60)
            set_bm_ipmi(data, failures, retry - 1)
        else:
            failures.add('setting ipmi address failed: %s', exc)
