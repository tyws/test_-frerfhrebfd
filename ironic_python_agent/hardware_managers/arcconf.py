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

from oslo_config import cfg
from oslo_log import log

from ironic_python_agent import encoding
from ironic_python_agent import hardware
from ironic_python_agent import utils

LOG = log.getLogger()
CONF = cfg.CONF

ARCCONF = "/opt/arcconf/cmdline/arcconf"
UNIT = ['KB', 'MB', 'GB', 'TB', 'PB']


class PhysicalDisk(encoding.SerializableComparable):
    serializable_fields = ('id', 'controller_id', 'type', 'size')

    def __init__(self, ID, ControllerID, Type, Size):
        self.id = ID
        self.controller_id = ControllerID
        self.type = Type
        self.size = Size


def _detect_raid_card():
    cmd = "%s list | grep Controller" % ARCCONF
    try:
        report, _e = utils.execute(cmd, shell=True)
        clounms = report.split(':')
        LOG.debug('Get Adapter Info:%s', clounms[2])
        adaptercount = int(clounms[1].split()[0])
        if adaptercount != 0:
            return True
        else:
            return False
    except Exception:
        return False


def _find_controllers():
    cmd = "%s list | grep Controller" % ARCCONF
    report, _e = utils.execute(cmd, shell=True)
    lines = report.split('\n')

    controllers = []
    for i in range(3, len(lines) - 1):
        controllers.append(lines[i].split()[1].split(':')[0])

    LOG.info('Controllers found:%s', str(controllers))
    return controllers


def _change_disk_unit(TotalSize):
    val = float(TotalSize.split()[0])
    uni = TotalSize.split()[1].upper()
    uni_idx = 1
    for i in range(0, 4):
        if uni == UNIT[i]:
            uni_idx = i
            break
    if uni_idx < 2:
        while uni_idx < 2:
            val /= 1024
            uni_idx += 1
    elif uni_idx > 2:
        while uni_idx < 2:
            val /= 1024
            uni_idx -= 1
    return str(round(val, 2)) + ' ' + UNIT[uni_idx]


class ArcconfHardwareManager(hardware.GenericHardwareManager):
    HARDWARE_MANAGER_NAME = 'ArcconfHardwareManager'
    HARDWARE_MANAGER_VERSION = '1.0'

    def evaluate_hardware_support(self):
        if _detect_raid_card():
            LOG.debug('Found ARCCONF Raid card')
            return hardware.HardwareSupport.MAINLINE
        else:
            LOG.debug('No ARCCONF Raid card found')
            return hardware.HardwareSupport.NONE

    def list_hardware_info(self):
        """Return full hardware inventory as a serializable dict.

        This inventory is sent to Ironic on lookup and to Inspector on
        inspection.

        :return: a dictionary representing inventory
        """
        # NOTE(dtantsur): don't forget to update docs when extending inventory
        hardware_info = {}
        hardware_info['interfaces'] = self.list_network_interfaces()
        hardware_info['cpu'] = self.get_cpus()
        hardware_info['disks'] = self.list_block_devices()
        hardware_info['physical_disks'] = self.list_physical_devices()
        hardware_info['memory'] = self.get_memory()
        hardware_info['bmc_address'] = self.get_bmc_address()
        hardware_info['system_vendor'] = self.get_system_vendor_info()
        hardware_info['boot'] = self.get_boot_info()
        return hardware_info

    def create_configuration(self, node, ports):
        target_raid_config = node.get('target_raid_config', {}).copy()
        target_raid_config_list = target_raid_config['logical_disks']

        LOG.info('Begin to create configuration')
        ld_num = 0
        for vdriver in target_raid_config_list:
            size = 'MAX'
            raid_level = None
            physical_disks = None
            controller = 1

            if 'size_gb' in vdriver and vdriver['size_gb'] != 'MAX':
                size = str(vdriver['size_gb'] * 1024)
            if 'raid_level' in vdriver:
                raid_level = vdriver['raid_level']
            if 'physical_disks' in vdriver:
                physical_disks = vdriver['physical_disks']
            if 'controller' in vdriver:
                controller = vdriver['controller']
            LOG.info('Raid Configuration:[size:%(size)s, '
                     'raid_level:%(raid_level)s, '
                     'physical_disks:%(p_disks)s, '
                     'controller:%(controller)s]',
                     {'size': size, 'raid_level': raid_level,
                      'p_disks': physical_disks,
                      'controller': controller})
            disklist = " "
            for i in range(0, len(physical_disks)):
                if i == 0:
                    disklist = physical_disks[i]
                else:
                    disklist = disklist + " " + physical_disks[i]

            cmd = ('%s create ' % ARCCONF) + controller \
                + ' LOGICALDRIVE ' + size + ' ' + raid_level \
                + ' ' + disklist + ' noprompt'
            report, _e = utils.execute(cmd, shell=True)
            ld_num1 = report.split('\n')[2].split()[-1]
            report1, _e = utils.execute(('%s getconfig ' %
                                         ARCCONF + controller
                                         + ' ld ' + ld_num1
                                         + '|grep -i size'), shell=True)
            ld_size = report1.split('\n')[1].split()[-2]
            target_raid_config['logical_disks'][ld_num]['size_gb'] = int(
                int(ld_size) / 1024)
            ld_num += 1
            if raid_level is not None and physical_disks \
                    is not None and controller is not None:
                LOG.info('Raid Configuration Command:%s', cmd)
                LOG.info('System Reaction:%s', report)
            else:
                LOG.info(
                    ('Param Error,No Raid Configuration'
                     ' Command being Created:%s'), cmd)

        return target_raid_config

    def delete_configuration(self, node, ports):
        controllers = _find_controllers()

        for controller in controllers:
            cmd = ('%s getconfig ' % ARCCONF) + \
                controller + ' ld'
            report, _e = utils.execute(cmd, shell=True)
            lines = report.split('\n')
            if 'No logical devices configured' in lines[4]:
                continue
            cmd = ('%s delete ' % ARCCONF) + controller + \
                ' LOGICALDRIVE ALL noprompt'
            report, _e = utils.execute(cmd, shell=True)
        return

    def list_physical_devices(self):
        devices = []
        controllers = _find_controllers()

        for controller in controllers:
            report, _e = utils.execute(('%s getconfig ' %
                                        ARCCONF + controller + ' pd'),
                                       shell=True)
            lines = report.split('\n')
            i = 0
            while i in range(0, len(lines)):
                device = {}
                if 'Hard drive' in lines[i]:
                    i += 1
                    while ' : ' in lines[i]:
                        key, val = lines[i].split(' : ', 1)
                        device[key.strip()] = val.strip()
                        i += 1

                    ID = device['Reported Channel,Device(T:L)'].split('(')[0]
                    ID = ID.replace(',', ' ')
                    if device['SSD'].lower() == 'yes':
                        Type = 'SSD'
                    else:
                        Type = device['Transfer Speed'].split()[0].upper()
                    Size = _change_disk_unit(device['Total Size'])
                    devices.append(
                        PhysicalDisk(ID=ID,
                                     ControllerID=controller,
                                     Type=Type,
                                     Size=Size))
                else:
                    i += 1
                    continue
        return devices

    def get_clean_steps(self, node, ports):
        return [
            {
                'step': 'erase_devices',
                'priority': 0,
                'interface': 'deploy',
                'reboot_requested': False,
                'abortable': True
            },
            {
                'step': 'erase_devices_metadata',
                'priority': 99,
                'interface': 'deploy',
                'reboot_requested': False,
                'abortable': True
            },
            {
                'step': 'delete_configuration',
                'priority': 20,
                'interface': 'deploy',
                'reboot_requested': False,
                'abortable': False
            },
            {
                'step': 'create_configuration',
                'priority': 15,
                'interface': 'deploy',
                'reboot_requested': False,
                'abortable': False
            }
        ]
