#!/usr/bin/env python
import rospy
import mraa
from plen_msgs.msg import Eyes


class PlenEye(object):

    def __init__(self, pin, pwm_period_us=700):
        self._pwm = mraa.Pwm(pin)
        self._pwm.period_us(pwm_period_us)
        self._pwm.enable(True)
        self._loop = True
        self._pattern = [0]
        self._pattern_index = 0

    def set_pattern(self, pattern, loop):
        # finished pattern or change loop pattern
        if self._loop and (map(float, self._pattern) != map(float, pattern)) or (not self._loop) and (self._pattern_index == len(self._pattern) - 1):
            self._pattern_index = 0
            self._pattern = pattern
            self._loop = loop


    def update(self):
        self._pwm.write(self._pattern[self._pattern_index])
        self._pattern_index += 1
        if self._loop:
            if self._pattern_index == len(self._pattern):
                self._pattern_index = 0
        else:
            if self._pattern_index == len(self._pattern):
                self._pattern_index = len(self._pattern) - 1


def left_eye():
    return PlenEye(pin=14)


def right_eye():
    return PlenEye(pin=20)


class Node(object):
    ROSPY_RATE_HZ = 100

    def __init__(self):
        self.eyes = (left_eye(), right_eye())

        rospy.init_node('eyes_node', anonymous=True)
        self.subscriber = rospy.Subscriber(
            'instruction_to_eyes', Eyes, self.subscribe)
        self.rospy_rate = rospy.Rate(self.ROSPY_RATE_HZ)

    def subscribe(self, message):
        self.eyes[0].set_pattern(message.left.pattern, message.left.loop)
        self.eyes[1].set_pattern(message.right.pattern, message.right.loop)

    def start(self):
        try:
            while not rospy.is_shutdown():
                for eye in self.eyes:
                    eye.update()
                self.rospy_rate.sleep()
        finally:
            for eye in self.eyes:
                eye.set_pattern([0], False)
                eye.update()


if __name__ == '__main__':
    Node().start()
