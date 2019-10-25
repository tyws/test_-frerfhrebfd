# Copyright (C) 2019 Inspur Corporation
#
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

from ironic_python_agent import hardware
from ironic_python_agent.hardware_managers import mega
from ironic_python_agent.tests.unit import base
from ironic_python_agent import utils

PHYSICAL_DISKS_TEMLATE = ('Adapter #0\nEnclosure Device ID: 8\n'
                          'Slot Number: 0\nPD Type: SATA\nRaw '
                          'Size: 894.252 GB [0x6fc81ab0 Sectors]\n'
                          'Inquiry Data: BTYF84730BXY960CGN'
                          '  INTEL SSDSC2KB960G8              '
                          '       XCV10100\nEnclosure Device ID'
                          ': 8\nSlot Number: 1\nPD Type: SATA\n'
                          'Raw Size: 894.252 GB [0x6fc81ab0 '
                          'Sectors]\nInquiry Data: '
                          'BTYF84820BNW960CGN  INTEL SSDSC2KB960G8'
                          '                     XCV10100\n'
                          'Enclosure Device ID: 8\nSlot Number: '
                          '2\nPD Type: SATA\nRaw Size: 894.252 GB '
                          '[0x6fc81ab0 Sectors]\nInquiry Data: '
                          'BTYF84820BT4960CGN  INTEL SSDSC2KB960G8'
                          '                     XCV10100\n')


class TestMegaHardwareManager(base.IronicAgentTest):
    def setUp(self):
        super(TestMegaHardwareManager, self).setUp()
        self.hardware = mega.MegaHardwareManager()
        self.node = {'uuid': 'dda135fb-732d-4742-8e72-df8f3199d244',
                     'driver_internal_info': {}}

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_detect_raid_card(self, mock_execute):
        mock_execute.return_value = ('Controller Count: 1.\n', '')
        self.assertTrue(mega._detect_raid_card())

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_detect_raid_card_no_mega(self, mock_execute):
        mock_execute.return_value = ('Controller Count: 0.\n', '')
        self.assertFalse(mega._detect_raid_card())

    @mock.patch(
        'ironic_python_agent.hardware_managers.mega._detect_raid_card',
        autospec=True)
    def test_evaluate_hardware_support(self, mock_detect):
        mock_detect.return_value = True
        expected_support = hardware.HardwareSupport.MAINLINE
        actual_support = self.hardware.evaluate_hardware_support()
        self.assertEqual(expected_support, actual_support)

    @mock.patch(
        'ironic_python_agent.hardware_managers.mega._detect_raid_card',
        autospec=True)
    def test_evaluate_hardware_support_no_mega(self, mock_detect):
        mock_detect.return_value = False
        expected_support = hardware.HardwareSupport.NONE
        actual_support = self.hardware.evaluate_hardware_support()
        self.assertEqual(expected_support, actual_support)

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_list_physical_devices(self, mock_execute):
        mock_execute.return_value = (PHYSICAL_DISKS_TEMLATE, '')
        expected_devices = [
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='0',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84730BXY960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='1',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84820BNW960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='2',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84820BT4960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
        ]
        devices = self.hardware.list_physical_devices()
        self.assertEqual(3, len(devices))
        for expected, device in zip(expected_devices, devices):
            for attr in ['Enclosure_Device_Id',
                         'Slot_Id', 'Type', 'Total_Size', 'Model']:
                self.assertEqual(getattr(expected, attr),
                                 getattr(device, attr))

    def test_list_hardware_info(self):
        self.hardware.list_network_interfaces = mock.Mock()
        self.hardware.list_network_interfaces.return_value = [
            hardware.NetworkInterface('eth0', '00:0c:29:8c:11:b1'),
            hardware.NetworkInterface('eth1', '00:0c:29:8c:11:b2'),
        ]

        self.hardware.get_cpus = mock.Mock()
        self.hardware.get_cpus.return_value = hardware.CPU(
            'Awesome CPU x14 9001',
            9001,
            14,
            'x86_64')

        self.hardware.get_memory = mock.Mock()
        self.hardware.get_memory.return_value = hardware.Memory(1017012)

        self.hardware.list_block_devices = mock.Mock()
        self.hardware.list_block_devices.return_value = [
            hardware.BlockDevice('/dev/sdj', 'big', 1073741824, True),
            hardware.BlockDevice('/dev/hdaa', 'small', 65535, False),
        ]

        self.hardware.list_physical_devices = mock.Mock()
        self.hardware.list_physical_devices.return_value = [
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='0',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84730BXY960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='1',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84820BNW960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
            mega.PhysicalDisk(
                Enclosure_Device_Id='8',
                Slot_Id='2',
                Type='SSD',
                Total_Size='894.252 GB',
                Model=('BTYF84820BT4960CGN  INTEL SSDSC2KB960G8  '
                           '                   XCV10100')),
        ]

        self.hardware.get_boot_info = mock.Mock()
        self.hardware.get_boot_info.return_value = hardware.BootInfo(
            current_boot_mode='bios', pxe_interface='boot:if')

        self.hardware.get_bmc_address = mock.Mock()
        self.hardware.get_system_vendor_info = mock.Mock()

        hardware_info = self.hardware.list_hardware_info()
        self.assertEqual(self.hardware.get_memory(),
                         hardware_info['memory'])
        self.assertEqual(self.hardware.get_cpus(), hardware_info['cpu'])
        self.assertEqual(self.hardware.list_block_devices(),
                         hardware_info['disks'])
        self.assertEqual(self.hardware.list_physical_devices(),
                         hardware_info['physical_disks'])
        self.assertEqual(self.hardware.list_network_interfaces(),
                         hardware_info['interfaces'])
        self.assertEqual(self.hardware.get_boot_info(),
                         hardware_info['boot'])
