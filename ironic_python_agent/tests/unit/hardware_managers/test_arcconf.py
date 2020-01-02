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
from mock import call

from ironic_python_agent import hardware
from ironic_python_agent.hardware_managers import arcconf
from ironic_python_agent.tests.unit import base
from ironic_python_agent import utils


PHYSICAL_DISKS_TEMLATE = ('\nControllers found: 1\n----------------'
                          '----------------------------------------'
                          '--------------\nPhysical Device information\n'
                          '----------------------------------------'
                          '------------------------------\n      '
                          'Device #0\n         Device is a Hard drive\n'
                          '         State                              '
                          ': Online\n         Block Size               '
                          '          : 512 Bytes\n         Supported   '
                          '                       : Yes\n         '
                          'Programmed Max Speed               : '
                          'SAS 12.0 Gb/s\n         Transfer Speed      '
                          '               : SAS 12.0 Gb/s\n         '
                          'Reported Channel,Device(T:L)       : '
                          '0,0(0:0)\n         Reported Location        '
                          '          : Enclosure 0, Slot 0(Connector 0)\n'
                          '         Reported ESD(T:L)                  '
                          ': 2,0(0:0)\n         Vendor                 '
                          '            : HGST\n         Model          '
                          '                    : HUC101860CSS200\n     '
                          '    Firmware                           : AD02\n'
                          '         Serial number                      '
                          ': 0BH68ZVD\n         World-wide name        '
                          '            : 5000CCA07D43CDFF\n         '
                          'Reserved Size                      : 956312 KB\n'
                          '         Used Size                          : '
                          '571392 MB\n         Unused Size              '
                          '          : 64 KB\n         Total Size       '
                          '                  : 572325 MB\n         '
                          'Write Cache                        : '
                          'Enabled (write-back)\n         FRU           '
                          '                     : None\n         '
                          'S.M.A.R.T.                         : No\n    '
                          '     S.M.A.R.T. warnings                : 0\n'
                          '         Power State                        :'
                          ' Full rpm\n         Supported Power States   '
                          '          : Full rpm,Powered off\n         SSD'
                          '                                : No\n       '
                          '  Temperature                        : 46 C/ '
                          '114 F\n      --------------------------------'
                          '--------------------------------\n      Device'
                          ' Phy Information                \n      ------'
                          '----------------------------------------------'
                          '------------\n         Phy #0\n            PHY'
                          ' Identifier                  : 0\n            '
                          'SAS Address                     : '
                          '5000CCA07D43CDFD\n            Attached PHY '
                          'Identifier         : 6\n            Attached '
                          'SAS Address            : 56C92BF00069D386\n  '
                          '       Phy #1\n            PHY Identifier    '
                          '              : 1\n            SAS Address   '
                          '                  : 5000CCA07D43CDFE\n      -'
                          '---------------------------------------------'
                          '------------------\n      Runtime Error '
                          'Counters                \n      -------------'
                          '---------------------------------------------'
                          '------\n         Hardware Error Count        '
                          '       : 0\n         Medium Error Count      '
                          '           : 0\n         Parity Error Count  '
                          '               : 0\n         Link Failure '
                          'Count                 : 0\n         Aborted '
                          'Command Count              : 0\n         '
                          'SMART Warning Count                : 0\n\n   '
                          '   Device #1\n         Device is a Hard '
                          'drive\n         State                        '
                          '      : Online\n         Block Size          '
                          '               : 512 Bytes\n         '
                          'Supported                          : Yes\n   '
                          '      Programmed Max Speed               : '
                          'SAS 12.0 Gb/s\n         Transfer Speed       '
                          '              : SAS 12.0 Gb/s\n         '
                          'Reported Channel,Device(T:L)       : '
                          '0,1(1:0)\n         Reported Location         '
                          '         : Enclosure 0, Slot 1(Connector 0)\n'
                          '         Reported ESD(T:L)                  :'
                          ' 2,0(0:0)\n         Vendor                   '
                          '          : HGST\n         Model             '
                          '                 : HUC101860CSS200\n         '
                          'Firmware                           : AD02\n  '
                          '       Serial number                      : '
                          '0BH67UPD\n         World-wide name           '
                          '         : 5000CCA07D43BC7B\n         '
                          'Reserved Size                      : 956312 '
                          'KB\n         Used Size                      '
                          '    : 571392 MB\n         Unused Size        '
                          '                : 64 KB\n         Total Size '
                          '                        : 572325 MB\n        '
                          ' Write Cache                        : Enabled'
                          ' (write-back)\n         FRU                  '
                          '              : None\n         S.M.A.R.T.    '
                          '                     : No\n         '
                          'S.M.A.R.T. warnings                : 0\n     '
                          '    Power State                        : '
                          'Full rpm\n         Supported Power States    '
                          '         : Full rpm,Powered off\n         SSD'
                          '                                : No\n       '
                          '  Temperature                        : 45 C/ '
                          '113 F\n      --------------------------------'
                          '--------------------------------\n      '
                          'Device Phy Information                \n     '
                          ' --------------------------------------------'
                          '--------------------\n         Phy #0\n      '
                          '      PHY Identifier                  : 0\n  '
                          '          SAS Address                     : '
                          '5000CCA07D43BC79\n            Attached PHY '
                          'Identifier         : 7\n            Attached '
                          'SAS Address            : 56C92BF00069D386\n  '
                          '       Phy #1\n            PHY Identifier    '
                          '              : 1\n            SAS Address   '
                          '                  : 5000CCA07D43BC7A\n      -'
                          '---------------------------------------------'
                          '------------------\n      Runtime Error '
                          'Counters                \n      -------------'
                          '---------------------------------------------'
                          '------\n         Hardware Error Count        '
                          '       : 0\n         Medium Error Count      '
                          '           : 0\n         Parity Error Count  '
                          '               : 0\n         Link Failure '
                          'Count                 : 0\n         Aborted '
                          'Command Count              : 0\n         '
                          'SMART Warning Count                : 0\n '
                          '\nCommand completed successfully.\n')

CREATE_DISKS_OUTPUT = ('Controllers found: 1\n\n'
                       'Creating logical device:'
                       ' LogicalDrv 0\n\nCommand'
                       ' completed successfully.')

LOGIC_DISKS_SIZE_TEMPLATE = ('   Block Size of member '
                             'drives              : 512'
                             ' Bytes\n   Size          '
                             '                         '
                             '  : 511990 MB\n   '
                             'Stripe-unit size         '
                             '                : 256 KB')


class TestArcconfHardwareManager(base.IronicAgentTest):
    def setUp(self):
        super(TestArcconfHardwareManager, self).setUp()
        self.hardware = arcconf.ArcconfHardwareManager()
        self.node = {'uuid': 'dda135fb-732d-4742-8e72-df8f3199d244',
                     'driver_internal_info': {}}

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_detect_raid_card(self, mock_execute):
        mock_execute.return_value = (('Controllers found: 1\n'
                                      'Controller information\n   '
                                      'Controller ID             : '
                                      'Status, Slot, Mode, Name, '
                                      'SerialNumber, WWN\n   '
                                      'Controller 1:             : '
                                      'Optimal, Slot 1, RAID (Expose'
                                      ' RAW), PM8060-RAID , '
                                      '1000000EB87, 56C92BF00069D386\n'), '')
        self.assertTrue(arcconf._detect_raid_card())

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_find_controllers(self, mock_execute):
        mock_execute.return_value = (('Controllers found: 1\n'
                                      'Controller information\n   '
                                      'Controller ID             : '
                                      'Status, Slot, Mode, Name, '
                                      'SerialNumber, WWN\n   '
                                      'Controller 1:             : '
                                      'Optimal, Slot 1, RAID (Expose'
                                      ' RAW), PM8060-RAID , '
                                      '1000000EB87, 56C92BF00069D386\n'), '')
        expected_controllers = ['1']
        actual_controllers = arcconf._find_controllers()
        self.assertEqual(expected_controllers, actual_controllers)

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_create_configration_size_int(self, mock_execute):
        self.node['target_raid_config'] = {
            "logical_disks":
            [
                {
                    "size_gb": 500,
                    "raid_level": "1",
                    "controller": "1",
                    "volume_name": "RAID1_1",
                    "is_root_volume": True,
                    "physical_disks": [
                        "0 0",
                        "0 1"
                    ]
                }
            ]
        }
        mock_execute.side_effect = [(CREATE_DISKS_OUTPUT, ''),
                                    (LOGIC_DISKS_SIZE_TEMPLATE, '')]
        expected_raid = {
            "logical_disks":
            [
                {
                    "size_gb": 499,
                    "raid_level": "1",
                    "controller": "1",
                    "volume_name": "RAID1_1",
                    "is_root_volume": True,
                    "physical_disks": [
                        "0 0",
                        "0 1"
                    ]
                }
            ]
        }
        actual_raid = self.hardware.create_configuration(self.node, [])
        self.assertEqual(expected_raid, actual_raid)
        calls = [call('/opt/arcconf/cmdline/arcconf create 1 '
                      'LOGICALDRIVE 512000 1 0 0 0 1 noprompt',
                      shell=True),
                 call('/opt/arcconf/cmdline/arcconf getconfig'
                      ' 1 ld 0|grep -i size', shell=True)]
        mock_execute.assert_has_calls(calls)

    @mock.patch.object(utils, 'execute', autospec=True)
    def test_create_configration_size_MAX(self, mock_execute):
        self.node['target_raid_config'] = {
            "logical_disks":
            [
                {
                    "size_gb": "MAX",
                    "raid_level": "1",
                    "controller": "1",
                    "volume_name": "RAID1_1",
                    "is_root_volume": True,
                    "physical_disks": [
                        "0 0",
                        "0 1"
                    ]
                }
            ]
        }
        mock_execute.side_effect = [(CREATE_DISKS_OUTPUT, ''),
                                    (LOGIC_DISKS_SIZE_TEMPLATE, '')]
        expected_raid = {
            "logical_disks":
            [
                {
                    "size_gb": 499,
                    "raid_level": "1",
                    "controller": "1",
                    "volume_name": "RAID1_1",
                    "is_root_volume": True,
                    "physical_disks": [
                        "0 0",
                        "0 1"
                    ]
                }
            ]
        }
        actual_raid = self.hardware.create_configuration(self.node, [])
        self.assertEqual(expected_raid, actual_raid)
        calls = [call('/opt/arcconf/cmdline/arcconf create 1 '
                      'LOGICALDRIVE MAX 1 0 0 0 1 noprompt',
                      shell=True),
                 call('/opt/arcconf/cmdline/arcconf getconfig'
                      ' 1 ld 0|grep -i size', shell=True)]
        mock_execute.assert_has_calls(calls)

    @mock.patch(
        'ironic_python_agent.hardware_managers.arcconf._detect_raid_card',
        autospec=True)
    def test_evaluate_hardware_support(self, mock_detect):
        mock_detect.return_value = True
        expected_support = hardware.HardwareSupport.MAINLINE
        actual_support = self.hardware.evaluate_hardware_support()
        self.assertEqual(expected_support, actual_support)

    @mock.patch(
        'ironic_python_agent.hardware_managers.arcconf._detect_raid_card',
        autospec=True)
    def test_evaluate_hardware_support_no_arcconf(self, mock_detect):
        mock_detect.return_value = False
        expected_support = hardware.HardwareSupport.NONE
        actual_support = self.hardware.evaluate_hardware_support()
        self.assertEqual(expected_support, actual_support)

    @mock.patch(
        'ironic_python_agent.hardware_managers.arcconf._find_controllers',
        autospec=True)
    @mock.patch.object(utils, 'execute', autospec=True)
    def test_list_physical_devices(self, mock_execute, mock_find_controllers):
        mock_execute.return_value = (PHYSICAL_DISKS_TEMLATE, '')
        mock_find_controllers.return_value = ['1']
        expected_devices = [
            arcconf.PhysicalDisk(state='Online',
                                 block_size='512 Bytes',
                                 supported='Yes',
                                 programmed_max_speed='SAS 12.0 Gb/s',
                                 transfer_speed='SAS 12.0 Gb/s',
                                 reported_channel_and_device='0,0(0:0)',
                                 reported_location=('Enclosure 0, '
                                                    'Slot 0(Connector 0)'),
                                 reported_esd='2,0(0:0)',
                                 vendor='HGST',
                                 model='HUC101860CSS200',
                                 firmware='AD02',
                                 serial_number='0BH68ZVD',
                                 world_wide_name='5000CCA07D43CDFF',
                                 reserved_size='956312 KB',
                                 used_size='571392 MB',
                                 unused_size='64 KB',
                                 total_size='572325 MB',
                                 write_cache='Enabled (write-back)',
                                 fru='None',
                                 s_m_a_r_t='No',
                                 s_m_a_r_t_warnings='0',
                                 power_state='Full rpm',
                                 supported_power_states=('Full rpm'
                                                         ',Powered off'),
                                 ssd='No',
                                 temperature='46 C/ 114 F'),
            arcconf.PhysicalDisk(state='Online',
                                 block_size='512 Bytes',
                                 supported='Yes',
                                 programmed_max_speed='SAS 12.0 Gb/s',
                                 transfer_speed='SAS 12.0 Gb/s',
                                 reported_channel_and_device='0,1(1:0)',
                                 reported_location=('Enclosure 0, '
                                                    'Slot 1(Connector 0)'),
                                 reported_esd='2,0(0:0)',
                                 vendor='HGST',
                                 model='HUC101860CSS200',
                                 firmware='AD02',
                                 serial_number='0BH67UPD',
                                 world_wide_name='5000CCA07D43BC7B',
                                 reserved_size='956312 KB',
                                 used_size='571392 MB',
                                 unused_size='64 KB',
                                 total_size='572325 MB',
                                 write_cache='Enabled (write-back)',
                                 fru='None',
                                 s_m_a_r_t='No',
                                 s_m_a_r_t_warnings='0',
                                 power_state='Full rpm',
                                 supported_power_states=('Full rpm'
                                                         ',Powered off'),
                                 ssd='No',
                                 temperature='45 C/ 113 F')]
        devices = self.hardware.list_physical_devices()
        self.assertEqual(2, len(devices))
        for expected, device in zip(expected_devices, devices):
            for attr in ['state', 'block_size', 'supported',
                         'programmed_max_speed', 'transfer_speed',
                         'reported_channel_and_device',
                         'reported_location', 'reported_esd',
                         'vendor', 'model', 'firmware',
                         'serial_number', 'world_wide_name',
                         'reserved_size', 'used_size',
                         'unused_size', 'total_size', 'write_cache',
                         'fru', 's_m_a_r_t',
                         's_m_a_r_t_warnings', 'power_state',
                         'supported_power_states',
                         'ssd', 'temperature']:
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
            arcconf.PhysicalDisk(state='Online',
                                 block_size='512 Bytes',
                                 supported='Yes',
                                 programmed_max_speed='SAS 12.0 Gb/s',
                                 transfer_speed='SAS 12.0 Gb/s',
                                 reported_channel_and_device='0,0(0:0)',
                                 reported_location='Enclosure 0, \
                                 Slot 0(Connector 0)',
                                 reported_esd='2,0(0:0)',
                                 vendor='HGST',
                                 model='HUC101860CSS200',
                                 firmware='AD02',
                                 serial_number='0BH68ZVD',
                                 world_wide_name='5000CCA07D43CDFF',
                                 reserved_size='956312 KB',
                                 used_size='571392 MB',
                                 unused_size='64 KB',
                                 total_size='572325 MB',
                                 write_cache='Enabled (write-back)',
                                 fru='None',
                                 s_m_a_r_t='No',
                                 s_m_a_r_t_warnings='0',
                                 power_state='Full rpm',
                                 supported_power_states='Full rpm\
                                 ,Powered off',
                                 ssd='No',
                                 temperature='46 C/ 114 F'),
            arcconf.PhysicalDisk(state='Online',
                                 block_size='512 Bytes',
                                 supported='Yes',
                                 programmed_max_speed='SAS 12.0 Gb/s',
                                 transfer_speed='SAS 12.0 Gb/s',
                                 reported_channel_and_device='0,1(1:0)',
                                 reported_location=('Enclosure 0, '
                                                    'Slot 1(Connector 0)'),
                                 reported_esd='2,0(0:0)',
                                 vendor='HGST',
                                 model='HUC101860CSS200',
                                 firmware='AD02',
                                 serial_number='0BH67UPD',
                                 world_wide_name='5000CCA07D43BC7B',
                                 reserved_size='956312 KB',
                                 used_size='571392 MB',
                                 unused_size='64 KB',
                                 total_size='572325 MB',
                                 write_cache='Enabled (write-back)',
                                 fru='None',
                                 s_m_a_r_t='No',
                                 s_m_a_r_t_warnings='0',
                                 power_state='Full rpm',
                                 supported_power_states='Full rpm,\
                                 Powered off',
                                 ssd='No',
                                 temperature='45 C/ 113 F'),
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
