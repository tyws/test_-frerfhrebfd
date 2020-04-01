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

import re

from oslo_config import cfg
from oslo_log import log

from ironic_python_agent import encoding
from ironic_python_agent import hardware
from ironic_python_agent import utils

LOG = log.getLogger()
CONF = cfg.CONF

JBOD_ON = '1'
JBOD_OFF = '0'

MEGACLI = "/opt/MegaRAID/MegaCli/MegaCli64"
UNIT = ['KB', 'MB', 'GB', 'TB', 'PB']


class PhysicalDisk(encoding.SerializableComparable):
    serializable_fields = ('id', 'controller_id', 'type', 'size')

    def __init__(self, ID, ControllerID, Type, Size):
        self.id = ID
        self.controller_id = ControllerID
        self.type = Type
        self.size = Size


def _detect_raid_card():
    cmd = "%s -adpCount | grep Controller" % MEGACLI
    try:
        report, _e = utils.execute(cmd, shell=True)
        clounms = report.split(':')
        LOG.debug('Get Adapter Info:%s', clounms[1])
        adaptercount = int(clounms[1].split('.')[0])
        if adaptercount == 0:
            return False
        else:
            return True
    except Exception:
        return False


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


class MegaHardwareManager(hardware.GenericHardwareManager):
    HARDWARE_MANAGER_NAME = 'MegaHardwareManager'
    HARDWARE_MANAGER_VERSION = '1.0'

    def evaluate_hardware_support(self):
        if _detect_raid_card():
            LOG.debug('Found LSI Raid card')
            return hardware.HardwareSupport.MAINLINE
        else:
            LOG.debug('No LSI Raid card found')
            return hardware.HardwareSupport.NONE

    def create_configuration(self, node, ports):

        target_raid_config = node.get('target_raid_config', {}).copy()
        target_raid_config_list = target_raid_config['logical_disks']

        LOG.info('Begin to create configuration')
        ld_num = 0
        for vdriver in target_raid_config_list:
            size = 'MAX'
            raid_level = None
            physical_disks = None
            controller = None

            if 'size_gb' in vdriver and vdriver['size_gb'] != 'MAX':
                size = str(vdriver['size_gb'] * 1024)
            if 'raid_level' in vdriver:
                raid_level = vdriver['raid_level']
            if 'physical_disks' in vdriver:
                physical_disks = vdriver['physical_disks']
            if 'controller' in vdriver:
                controller = vdriver['controller']
            LOG.info(('Raid Configuration:[size:%s, '
                      'raid_level:%s, p_disks:%s, controller:%s]'),
                     size, raid_level, physical_disks, controller)
            disklist = " "
            for i in range(0, len(physical_disks)):
                if i == 0:
                    disklist = physical_disks[i]
                else:
                    disklist = disklist + "," + physical_disks[i]

            LOG.info('Raid disk list:[%s]', disklist)

            cmd = ('%s -CfgLdAdd ' % MEGACLI) + '-r' \
                + raid_level + "[" + disklist + "] " + "-a" + controller
            report, _e = utils.execute(cmd, shell=True)

            ld_num1 = report.split('\n')[1].split()[-1]
            cmd1 = ('%s -LDInfo -L' % MEGACLI) + \
                ld_num1 + ' -aAll | grep -i size'
            report1, _e = utils.execute(cmd1, shell=True)
            if report1.split('\n')[0].split(':')[-1].split()[-1] == 'GB':
                ld_size = float(report1.split('\n')[
                    0].split(':')[-1].split()[-2])
            else:
                ld_size = float(report1.split('\n')[0].split(
                    ':')[-1].split()[-2]) * 1024
            target_raid_config['logical_disks'][ld_num]['size_gb'] = int(
                ld_size)
            ld_num += 1
            if raid_level is not None and physical_disks \
                    is not None and controller is not None:
                LOG.info('Raid Configuration Command:%s', cmd)
            else:
                LOG.info(
                    ('Param Error,No Raid Configuration'
                        ' Command being Created:%s'), cmd)
        return target_raid_config

    def delete_configuration(self, node, ports):

        LOG.info('Begin to delete configuration')
        cmd = '%s -CfgLdDel -LAll -aAll' % MEGACLI
        report, _e = utils.execute(cmd, shell=True)

        cmd = '%s -CfgForeign -Clear -aAll' % MEGACLI
        report, _e = utils.execute(cmd, shell=True)
        return

    def set_jbod_mode(self, node, ports, mode):

        cmd = "%s -AdpSetProp EnableJBOD %s -a0" % (MEGACLI, mode)
        utils.execute(cmd, shell=True)
        return

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

    def list_physical_devices(self):
        report, _e = utils.execute(('/opt/MegaRAID/MegaCli/MegaCli64'
                                    ' -PDList -aALL | grep -iE \"adapter'
                                    '|Enclosure Device ID|slot number'
                                    '|Raw size|PD Type|Inquiry Data\"'),
                                   shell=True)
        lines = report.split('\n')

        i = 0
        j = 0
        devices = []
        adapter = None
        LOG.info('Get line string is: %s', lines)
        while i < len(lines):
            # Split into KEY=VAL pairs
            if lines[i].find('Adapter') != -1:
                adapter = lines[i].split('#')[1]
                i += 1
                LOG.info('Get a Adapter with id: %s. Continuing', adapter)
            elif lines[i].find('Adapter') == -1:
                device = {}
                # 5 metrics are collected
                # Enclosure ID, slot number, Raw size
                for j in range(i, len(lines)):
                    LOG.info(('Parse the Megacli Result for'
                              ' Physical Disk: %s'), lines[j])
                    if lines[j].find("Adapter") != -1:
                        adapter = lines[i].split('#')[1]
                        i = j + 1
                    elif lines[j] == "":
                        i = j + 1
                        break
                    elif lines[j].find("Adapter") == -1:
                        device['Adapter_Id'] = adapter
                        # increment i by 1 avoid endless looping
                        i = j + 1
                        # Enclosure & Slot are required
                        # when adding configurations
                        if j % 5 == 1:
                            device['Enclosure_Device_Id'] = lines[j].\
                                split(':')[1].strip()
                        if j % 5 == 2:
                            device['Slot_Id'] = lines[j].split(':')[1].strip()
                        if j % 5 == 3:
                            # Physical Disk Type
                            device['Type'] = lines[j].split(':')[1].strip()
                        if j % 5 == 4:
                            disk_size = lines[j].split(':')[1]
                            disk_size = disk_size.split('[')
                            disk_size = disk_size[0].strip()
                            disk_size.strip()

                            # LSI Raw type is same as PMC total size
                            device['Total_Size'] = disk_size
                        if j % 5 == 0:
                            # Inquiry Data: Manufacturer & Series Number
                            device['Model'] = lines[j].split(':')[1].strip()
                            copy = device.copy()
                            if re.search(r'SSD|Micron_5200', copy['Model']) \
                                    is not None:
                                copy['Type'] = 'SSD'
                            ID = copy['Enclosure_Device_Id'] + \
                                ":" + copy['Slot_Id']
                            Controller = copy['Adapter_Id']
                            Type = copy['Type']
                            Size = _change_disk_unit(copy['Total_Size'])
                            devices.append(PhysicalDisk(ID=ID,
                                                        ControllerID=Controller,
                                                        Type=Type,
                                                        Size=Size))

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

