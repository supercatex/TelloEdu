from tools import *


def v_callback(frame):
    pass
    # print(frame.shape)


def k_callback(event_name, key):
    print(event_name, key)


c = Controller(video_callback=v_callback, keyboard_callback=k_callback)
c.run_video()

print("takeoff")
c.drone.do_takeoff()

c.drone.get_tof()
print(c.drone.response)

print("land")
c.drone.do_land()

c.run_keyboard()