#!/usr/bin/python3
import dbus

from advertisement import Advertisement
from server import WatchplantMain, Service, Characteristic, Descriptor
import random
import csv
import sys

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 1000

class WatchplantAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("FER WP1")
        self.include_tx_power = False
        self.add_service_uuid("5701")

class WatchplantService(Service):
    UUID = "8b0be1f6-ddd3-11ec-9d64-0242ac120002"


    def __init__(self, index):
        self.doorsOpen = True
        Service.__init__(self, index, self.UUID, True)
        self.add_characteristic(dataCharacteristic(self))
        self.add_characteristic(doorStateCharacteristic(self))

    def areDoorsOpen(self):
        return self.doorsOpen

    def setDoors(self, areOpen):
        self.doorsOpen = areOpen
        print("Doors state changed")
        print(self.doorsOpen)
        return

class dataCharacteristic(Characteristic):
    UUID = "ebcb181a-e01f-11ec-9d64-0242ac120002"
    numberOfLines = 0
    processedNumberOfLines = 1

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(self, self.UUID, ["notify", "read"], service)
        self.add_descriptor(DataDescriptor(self))

    def get_data(self):
        value = []
        data=self.getDataString()
        temp_string=data
        for c in temp_string :
            value.append(dbus.Byte(c.encode()))
        return value

    def set_data_callback(self):
        if self.notifying:
            value = self.get_data()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_data()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_data_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_data()
        return value

    def getDataString(self):
        string = ''
        interesedRow = []
        if self.numberOfLines == 0:
            tempNumberOfLines = 0
            with open('rpi0.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    tempNumberOfLines = tempNumberOfLines + 1
                self.numberOfLines = tempNumberOfLines
            print(self.numberOfLines)
        if self.numberOfLines != 0:
            currentActiveLine = self.processedNumberOfLines + 1
            tempLineNumber = 0
            with open('rpi0.csv') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                print(currentActiveLine)
                for row in csv_reader:
                    tempLineNumber=tempLineNumber+1
                    if tempLineNumber == currentActiveLine:
                        interestedRow = row
                        self.processedNumberOfLines = self.processedNumberOfLines + 1
        string = ','.join(interestedRow)  
        print(string)
        print(sys.getsizeof(string))     
        return string

class DataDescriptor(Descriptor):
    DATA_DESCRIPTOR_UUID = "2901"
    DATA_DESCRIPTOR_VALUE = "Current RPi information"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.DATA_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DATA_DESCRIPTOR_VALUE
        for c in desc:
            value.append(dbus.Byte(c.encode()))
        return value

class doorStateCharacteristic(Characteristic):
    DOOR_UUID = "fa2af5ec-e01f-11ec-9d64-0242ac120002"

    def __init__(self, service):
        Characteristic.__init__(self, self.DOOR_UUID,["read", "write"], service)
        self.add_descriptor(doorStateDescriptor(self))

    def WriteValue(self, value, options):
        value_string = str(value[0]).upper()
        print(value_string)
        print("INT VALUE STRINGA")
        print(int(value_string))
        if int(value_string) == 0:
            self.service.setDoors(False)
            print("SET DOORS TO CLOSED")
        elif int(value_string) == 1:
            self.service.setDoors(True)
            print("SET DOORS TO OPEN")

    def ReadValue(self, options):
        value = []
        print("READ VALUE")
        print(self.service.doorsOpen)
        if self.service.doorsOpen: 
            val = "Y"
            print("Value is yes")
        else: 
            val = "N"
            print("Value is no")
        value.append(dbus.Byte(val.encode()))
        print("Value in read value")
        print(value)

        return value

class doorStateDescriptor(Descriptor):
    DOORSTATE_DESCRIPTOR_UUID = "2901"
    DOORSTATE_DESCRIPTOR_VALUE = "State of the greenhouse doors"

    def __init__(self, characteristic):
        Descriptor.__init__(self, self.DOORSTATE_DESCRIPTOR_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.DOORSTATE_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))
        return value

if __name__ == '__main__':

    WatchplantMonitor = WatchplantMain()
    WatchplantMonitor.add_service(WatchplantService(0))
    WatchplantMonitor.register()

    WatchPlantAdvertisment = WatchplantAdvertisement(0)
    WatchPlantAdvertisment.register()

    try:
        WatchplantMonitor.run()
    except:
        WatchplantMonitor.quit()
