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


class PhysicalDisk(encoding.SerializableComparable):
    serializable_fields = ('state', 'block_size', 'supported',
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
                           'ssd', 'temperature')

    def __init__(self, state, block_size, supported, programmed_max_speed,
                 transfer_speed, reported_channel_and_device,
                 reported_location, reported_esd, vendor, model,
                 firmware, serial_number, world_wide_name,
                 reserved_size, used_size, unused_size, total_size,
                 write_cache, fru, s_m_a_r_t, s_m_a_r_t_warnings,
                 power_state, supported_power_states, ssd, temperature):
        self.state = state
        self.block_size = block_size
        self.supported = supported
        self.programmed_max_speed = programmed_max_speed
        self.transfer_speed = transfer_speed
        self.reported_channel_and_device = reported_channel_and_device
        self.reported_location = reported_location
        self.reported_esd = reported_esd
        self.vendor = vendor
        self.model = model
        self.firmware = firmware
        self.serial_number = serial_number
        self.world_wide_name = world_wide_name
        self.reserved_size = reserved_size
        self.used_size = used_size
        self.unused_size = unused_size
        self.total_size = total_size
        self.write_cache = write_cache
        self.fru = fru
        self.s_m_a_r_t = s_m_a_r_t
        self.s_m_a_r_t_warnings = s_m_a_r_t_warnings
        self.power_state = power_state
        self.supported_power_states = supported_power_states
        self.ssd = ssd
        self.temperature = temperature


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

            if 'size_gb' in vdriver:
                size = vdriver['size_gb']
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
                                         ARCCONF + controller +
                                         ' ld ' + ld_num1 +
                                         '|grep -i size'), shell=True)
            ld_size = report1.split('\n')[1].split()[-2]
            target_raid_config['logical_disks'][ld_num]['size_gb'] = int(
                ld_size) / 1024
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

                    devices.append(
                        PhysicalDisk(state=device['State'],
                                     block_size=device['Block Size'],
                                     supported=device['Supported'],
                                     programmed_max_speed=device[
                            'Programmed Max Speed'],
                            transfer_speed=device['Transfer Speed'],
                            reported_channel_and_device=device[
                                         'Reported Channel,Device(T:L)'],
                            reported_location=device['Reported Location'],
                            reported_esd=device['Reported ESD(T:L)'],
                            vendor=device['Vendor'],
                            model=device['Model'],
                            firmware=device['Firmware'],
                            serial_number=device['Serial number'],
                            world_wide_name=device['World-wide name'],
                            reserved_size=device['Reserved Size'],
                            used_size=device['Used Size'],
                            unused_size=device['Unused Size'],
                            total_size=device['Total Size'],
                            write_cache=device['Write Cache'],
                            fru=device['FRU'],
                            s_m_a_r_t=device['S.M.A.R.T.'],
                            s_m_a_r_t_warnings=device[
                            'S.M.A.R.T. warnings'],
                            power_state=device['Power State'],
                            supported_power_states=device[
                            'Supported Power States'],
                            ssd=device['SSD'],
                            temperature=device['Temperature']))
                else:
                    i += 1
                    continue
        return devices
