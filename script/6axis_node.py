#!/usr/bin/env python
# coding=utf-8

import struct

import mraa
import rospy
from geometory_msgs.msg import Accel
from std_msgs.msg import Empty


class Mpu(object):
    I2C_PORT = 0
    I2C_ADDRESS = 0x68

    def __init__(self):
        self._i2c = mraa.I2c(Mpu.I2C_PORT)
        self._i2c.address(Mpu.I2C_ADDRESS)
        self._i2c.writeReg(0x6B, 0x00)

    def read_accelgyros(self):
        start_address = 0x3B
        data_nbytes = 12
        reg_addresses = xrange(start_address, start_address + data_nbytes)

        i2c_data = map(self._i2c.readReg, reg_addresses)

        # '<' :  リトルエンディアン
        # 'h' :  2byte符号付き整数
        data_format = '<' + 'h' * (data_nbytes / struct.calcsize('h'))
        assert struct.calcsize(data_format) == data_nbytes
        accelgyros = struct.unpack(data_format, bytes(bytearray(i2c_data)))

        return accelgyros


class Node(object):
    NAME = '6axis_node'
    PUBLISHER_NAME = 'accel'
    SUBSCRIBER_NAME = 'request_accel'
    ROSPY_RATE_HZ = 10

    def __init__(self):
        self.mpu = Mpu()

        rospy.init_node(Node.NAME, anonymous=True)
        self.publisher = rospy.Publisher(
            Node.PUBLISHER_NAME, String, queue_size=10)
        rospy.Subscriber(Node.SUBSCRIBER_NAME, String, self.subscribe)
        self.rospy_rate = rospy.Rate(Node.ROSPY_RATE_HZ)

    def subscribe(self, message):
        rospy.loginfo('GET REQUEST')

        accelgyro = self.mpu.read_accelgyros()

        response = Accel()
        response.linear.x = accelgyro[0]
        response.linear.y = accelgyro[1]
        response.linear.z = accelgyro[2]
        response.angular.x = accelgyro[3]
        response.angular.y = accelgyro[4]
        response.angular.z = accelgyro[5]
        self.publisher.publish(response)

    def start(self):
        try:
            while not rospy.is_shutdown():
                #self.publish_accelgyros()
                self.rospy_rate.sleep()
        finally:
            pass


if __name__ == '__main__':
    Node().start()