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

import mock

from ironic_python_agent import errors
from ironic_python_agent import ipmi_setter
from ironic_python_agent.tests.unit import base
from ironic_python_agent import utils


class TestIpmiSetter(base.IronicAgentTest):
    def setUp(self):
        super(TestIpmiSetter, self).setUp()
        self.data = {}
        self.failures = utils.AccumulatedFailures()
        self.set_defaults(
            inspection_callback_url="1.1.1.1"
        )

    @mock.patch("ironic_python_agent.utils.execute", autospec=True)
    @mock.patch("requests.post", autospec=True)
    @mock.patch("requests.get", autospec=True)
    @mock.patch("ironic_python_agent.hardware.dispatch_to_managers",
                autospec=True)
    def test_set_new_bmc_address(self, mock_manager, mock_get,
                                 mock_post, mock_exec):
        mock_manager.side_effect = [
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0"
        ]
        mock_json = mock.Mock()
        mock_json.json = mock.Mock(
            return_value={
                "ip_address": "192.168.2.20",
                "netmask": "255.255.255.0",
                "gateway": "192.168.2.254"

            })
        mock_get.return_value = mock_json
        ipmi_setter.set_bm_ipmi(self.data, None)
        mock_calls = [
            mock.call('ipmitool', 'lan', 'set', '1', 'ipsrc', 'static'),
            mock.call('ipmitool', 'lan', 'set', '1', 'ipaddr', '192.168.2.20'),
            mock.call('ipmitool', 'lan', 'set', '1',
                      'netmask', '255.255.255.0'),
            mock.call('ipmitool', 'lan', 'set', '1',
                      'defgw', 'ipaddr', '192.168.2.254'),
        ]
        mock_exec.assert_has_calls(mock_calls)
        mock_post.assert_called_once_with('1.1.1.1/v1/bmc/fake_sn',
                                          json={'has_set': True})

    @mock.patch("ironic_python_agent.utils.execute", autospec=False)
    @mock.patch("requests.get", autospec=False)
    @mock.patch("requests.post", autospec=False)
    @mock.patch("ironic_python_agent.hardware.dispatch_to_managers",
                autospec=True)
    def test_set_used_bmc_address(self, mock_manager,
                                  mock_post, mock_get, mock_exec):
        mock_manager.side_effect = [
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "192.168.2.20"
        ]
        mock_json = mock.Mock()
        mock_json.json = mock.Mock(
            return_value={
                "ip_address": "192.168.2.20",
                "netmask": "255.255.255.0",
                "gateway": "192.168.2.254"

            })
        mock_get.return_value = mock_json
        ipmi_setter.set_bm_ipmi(self.data, None)
        mock_exec.assert_not_called()
        mock_post.assert_not_called()

    @mock.patch("ironic_python_agent.utils.execute", autospec=True)
    @mock.patch("requests.post", autospec=True)
    @mock.patch("requests.get", autospec=True)
    @mock.patch("ironic_python_agent.hardware.dispatch_to_managers",
                autospec=True)
    def test_set_new_bmc_address_retry(self, mock_manager, mock_get,
                                       mock_post, mock_exec):
        mock_manager.side_effect = [
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0"
        ]

        failures = utils.AccumulatedFailures(exc_class=errors.InspectionError)
        mock_json = mock.Mock()
        mock_json.json = mock.Mock(
            return_value={
                "ip_address": "192.168.2.20",
                "netmask": "255.255.255.0",
                "gateway": "192.168.2.254"

            })
        mock_get.side_effect = [
            Exception(),
            Exception(),
            Exception(),
            mock_json
        ]
        ipmi_setter.set_bm_ipmi(self.data, failures, retry=3)
        mock_get.assert_has_calls([
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn')])
        mock_post.assert_called_once_with('1.1.1.1/v1/bmc/fake_sn',
                                          json={'has_set': True})
        failures.raise_if_needed()

    @mock.patch("ironic_python_agent.utils.execute", autospec=True)
    @mock.patch("requests.post", autospec=True)
    @mock.patch("requests.get", autospec=True)
    @mock.patch("ironic_python_agent.hardware.dispatch_to_managers",
                autospec=True)
    def test_set_new_bmc_address_retry_failed(self, mock_manager, mock_get,
                                              mock_post, mock_exec):
        mock_manager.side_effect = [
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0",
            mock.Mock(
                product_name='fake_prouect',
                serial_number="fake_sn",
                manufacturer="fake_manufacturer"
            ),
            "0.0.0.0"
        ]

        failures = utils.AccumulatedFailures(exc_class=errors.InspectionError)
        mock_json = mock.Mock()
        mock_json.json = mock.Mock(
            return_value={
                "ip_address": "192.168.2.20",
                "netmask": "255.255.255.0",
                "gateway": "192.168.2.254"

            })
        mock_get.side_effect = Exception()
        ipmi_setter.set_bm_ipmi(self.data, failures, retry=3)
        mock_get.assert_has_calls([
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn'),
            mock.call('1.1.1.1/v1/bmc/fake_sn')])
        self.assertRaises(errors.InspectionError, failures.raise_if_needed)
