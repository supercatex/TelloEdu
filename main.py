from tools import *


def callback(frame):
    print(frame.shape)


drone = TelloEdu()
controller = Controller(drone, callback)
controller.run()
