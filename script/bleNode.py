#!/usr/bin/env python

import subprocess
import time

# restart bluetoothd
killall = subprocess.Popen(['killall', 'bluetoothd'], stdout = subprocess.PIPE, )
time.sleep(1.0)
bluetoothd = subprocess.Popen(['bluetoothd', '-nE'], stdout = subprocess.PIPE, )
end_of_pipe = bluetoothd.stdout
time.sleep(1.0)

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import array
import gobject

#from random import randint

import rospy
from std_msgs.msg import String

# register BLE node to ROS
rospy.init_node('bleNode', anonymous = True)
pub = rospy.Publisher('BleToControl', String, queue_size = 10)

mainloop = None

BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'

class Common(dbus.service.Object):
    def __init__(self, path, bus, uuid):
        self.path = path
        self.uuid = uuid
        self.childs = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        pass

    def add_child(self, child):
        self.childs.append(child)

    def get_child_paths(self):
        result = []
        for child in self.childs:
            result.append(child.get_path())
        return result

    def get_childs(self):
        return self.childs

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        pass

class Service(Common):
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        self.primary = primary
        Common.__init__(self, self.PATH_BASE + str(index), bus, uuid)

    def get_properties(self):
        child_paths = self.get_child_paths()
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    child_paths,
                    signature='o')
            }
        }

    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties[GATT_SERVICE_IFACE]

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        response[self.get_path()] = self.get_properties()
        characteristics = self.get_childs()
        for characteristic in characteristics:
            response[characteristic.get_path()] = characteristic.get_properties()
            descriptors = characteristic.get_childs()
            for descriptor in descriptors:
                response[descriptor.get_path()] = descriptor.get_properties()

        return response


class Characteristic(Common):
    def __init__(self, bus, index, uuid, flags, service_path):
        self.flags = flags
        Common.__init__(self, service_path + '/char' + str(index), bus, uuid)

    def get_properties(self):
        splited_path = self.path.split('/char')
        child_paths = self.get_child_paths
        return {
            GATT_CHRC_IFACE: {
                'Service': splited_path[0],
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    child_paths,
                    signature='o')
            }
        }

    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()

        return self.get_properties[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, out_signature='ay')
    def ReadValue(self):
        print('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='ay')
    def WriteValue(self, value):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(Common):
    def __init__(self, bus, index, uuid, flags, characteristic_path):
        self.flags = flags
        Common.__init__(self, characteristic_path + '/desc' + str(index), bus, uuid)

    def get_properties(self):
        splited_path = self.path.split('/desc')
        return {
            GATT_DESC_IFACE: {
                'Characteristic': splited_path[0],
                'UUID': self.uuid,
                'Flags': self.flags,
            }
        }

    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()

        return self.get_properties[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_DESC_IFACE, out_signature='ay')
    def ReadValue(self):
        print ('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_DESC_IFACE, in_signature='ay')
    def WriteValue(self, value):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

class TestService(Service):

    TEST_SVC_UUID = 'E1F40469-CFE1-43C1-838D-DDBC9DAFDDE6'
    CH_UUID =  'F90E9CFE-7E05-44A5-9D75-F13644D6F645'
    CH_UUID2 = 'CF70EE7F-2A26-4F62-931F-9087AB12552C'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.TEST_SVC_UUID, True)
        self.add_child(TestCharacteristic(bus, 1, self.path, self.CH_UUID2,0,1,['read']))
        self.add_child(TestCharacteristic(bus, 2, self.path, self.CH_UUID,0,1,['read', 'write','writable-auxiliaries']))

class TestCharacteristic(Characteristic):

    def __init__(self, bus, index, service_path,TEST_CHRC_UUID,flag,flag2,p):
        Characteristic.__init__(
                self, bus, index,
                TEST_CHRC_UUID,
                p,
                service_path)
        self.value = []
        if flag == 1:
                self.add_child(TestDescriptor(bus, 0, self.path))
        if flag2 == 1:
                self.add_child(CharacteristicUserDescriptionDescriptor(bus, 1, self))

    def ReadValue(self):
        print('TestCharacteristic Read: ' + repr(self.value))
        print('TestCharacteristic Read value: ' + str(self.value))
        return self.value

    def WriteValue(self, value):
        self.value = value
        s = "".join(chr(b) for b in value)
        print s
        rospy.loginfo("controlNode %s", s)

        if ('#' in s or '$' in s or '<' in s or '>' in s):
            LEDon = String()
            LEDon.data = "gpio,w,act"
            send(LEDon)

        message = String()
        message.data = "serial,w," + s
        send(message)

    def StartNotify(self):
        print('callback:StartNotify')

class TestDescriptor(Descriptor):

    def __init__(self, bus, index, characteristic_path):
        Descriptor.__init__(
                self, bus, index,
                self.TEST_DESC_UUID,
                ['read', 'write'],
                characteristic_path)

    def ReadValue(self):
        return [
                dbus.Byte('T'), dbus.Byte('e'), dbus.Byte('s'), dbus.Byte('t')
        ]


class CharacteristicUserDescriptionDescriptor(Descriptor):
    CUD_UUID = '2901'

    def __init__(self, bus, index, characteristic):
        self.writable = 'writable-auxiliaries' in characteristic.flags
        self.value = array.array('B', 'TX Data')
        self.value = self.value.tolist()
        Descriptor.__init__(
                self, bus, index,
                self.CUD_UUID,
                ['read', 'write'],
                characteristic.path)

    def ReadValue(self):
        return self.value

    def WriteValue(self, value):
        if not self.writable:
            raise NotPermittedException()
        self.value = value

def property_changed(interface, changed, invalidated, path):
    iface = interface[interface.rfind(".") + 1:]
    for name, value in changed.iteritems():
        val = str(value)
        if name == 'Connected':
            if val == "1":
                print("ON")
                message = String()
                message.data = "gpio,w,on"
                send(message)
            elif val == "0":
                print("OFF")
                message = String()
                message.data = "gpio,w,off"
                send(message)
                advertise()

            else:
                pass
        elif name == 'Alias' or name == 'Name':
            print("ON")
            message = String()
            message.data = "gpio,w,on"
            send(message)
        else:
            pass

def register_service_cb():
    print('GATT service registered')


def register_service_error_cb(error):
    print('Failed to register service: ' + str(error))
    mainloop.quit()


def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.iteritems():
        if props.has_key(GATT_MANAGER_IFACE):
            return o

    return None

def send(message):
    pub.publish(message)

def prepare_ble_cmd():
    pass

def advertise():
    print('hciup')
    hci_on = subprocess.Popen(['hciconfig','hci0','up'], stdout=subprocess.PIPE,)

    end_of_pipe = hci_on.stdout
    time.sleep(0.1)
    print('hcitool')
    hcitool_cmd2 = subprocess.Popen(['hcitool', '-i', 'hci0', 'cmd', '0x08', '0x0006', '20', '00', '20', '00','00', '00', '00', '00', '00', '00', '00', '00', '00', '07','00'], stdout=subprocess.PIPE,)

    end_of_pipe = hcitool_cmd2.stdout
    hcitool_cmd = subprocess.Popen(['hcitool','-i','hci0','cmd','0x08','0x0008','15','02','01','06','11','07','e6','dd','af','9d','bc','dd','8d','83','c1','43','e1','cf','69','04','f4','e1'], stdout=subprocess.PIPE,)

    end_of_pipe = hcitool_cmd.stdout
    hcitool_cmd3 = subprocess.Popen(['hcitool', '-i', 'hci0', 'cmd', '0x08', '0x000a' ,'01'],stdout=subprocess.PIPE,)
    end_of_pipe = hcitool_cmd3.stdout

def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    test_service = TestService(bus,0)

    mainloop = gobject.MainLoop(is_running=True)

    bus.add_signal_receiver(property_changed, bus_name="org.bluez",
                        dbus_interface="org.freedesktop.DBus.Properties",
                        signal_name="PropertiesChanged",
                        path_keyword="path")

    service_manager.RegisterService(test_service.get_path(), {}, reply_handler=register_service_cb, error_handler=register_service_error_cb)
    advertise()
    advertise()
    try:
        print "mainloop.run!"
        mainloop.run()

    except (KeyboardInterrupt, SystemExit):
        mainloop.quit()
        print "mainloop.quit!"

def mybleNode_shutdown():
    global mainloop
    mainloop.quit()
    print "shutdown now!"

rospy.on_shutdown(mybleNode_shutdown)

if __name__ == '__main__':
    main()
