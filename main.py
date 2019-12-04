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

print("back")
c.drone.do_back(20)

print("up")
c.drone.do_up(30)

print("down")
c.drone.do_down(30)

print("left")
c.drone.do_left(20)

print("right")
c.drone.do_right(20)

print("forward")
c.drone.do_forward(20)

print("cw")
c.drone.do_cw(90)

print("ccw")
c.drone.do_ccw(90)

print("go")
c.drone.do_go(0, 0, 50, 50)

print("land")
c.drone.do_land()

c.run_keyboard()
