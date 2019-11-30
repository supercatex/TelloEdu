from tools import *


def v_callback(frame):
    print(frame.shape)


def k_callback(event_name, key):
    print(event_name, key)


c = Controller(video_callback=v_callback, keyboard_callback=k_callback)
c.run_video()
c.run_keyboard()
