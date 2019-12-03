from tools import *


def v_callback(frame):
    print(frame.shape)


def k_callback(event_name, key):
    print(event_name, key)


c = Controller(video_callback=v_callback, keyboard_callback=k_callback)
c.run_video()

c.drone.do_takeoff(True)
time.sleep(8)

c.drone.do_back(20)
c.drone.do_up(30)

c.drone.do_land()
time.sleep(1)

# c.run_keyboard()
