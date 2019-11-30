from pynput.keyboard import Key, Listener, KeyCode
import cv2
import time
import threading
from tools import TelloEdu


class Controller(object):
    def __init__(self, drone=None, video_callback=None, keyboard_callback=None):
        self.drone = drone
        if self.drone is None:
            self.drone = TelloEdu()
        self.camera = None
        self.video_callback = video_callback
        self.keyboard_callback = keyboard_callback
        self.key_list = []
        self.frame = None
        self.speed = 30

    def on_press(self, key):
        if self.keyboard_callback is not None:
            self.keyboard_callback("on_press", key)
        if key not in self.key_list:
            self.key_list.append(key)
            self.do_action()

    def on_release(self, key):
        if self.keyboard_callback is not None:
            self.keyboard_callback("on_release", key)

        if Key.esc in self.key_list:
            Listener.stop()

        if Key.space in self.key_list:
            self.key_list.remove(Key.space)
            self.drone.do_stop()
            return

        if KeyCode.from_char('t') in self.key_list:
            self.drone.do_takeoff()

        if KeyCode.from_char('g') in self.key_list:
            self.drone.do_land()

        if Key.up in self.key_list:
            self.speed = min(self.speed + 5, 100)

        if Key.down in self.key_list:
            self.speed = max(self.speed - 5, 20)

        if KeyCode.from_char('o') in self.key_list:
            self.drone.send_command("mon")
            time.sleep(0.1)
            self.drone.send_command("mdirection 0")
            time.sleep(0.1)

        if KeyCode.from_char('p') in self.key_list:
            self.drone.send_command("moff")

        if key in self.key_list:
            self.key_list.remove(key)
            self.do_action()

    def get_frame(self):
        if self.drone.is_ready:
            return self.drone.frame
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
        success, frame = self.camera.read()
        if success:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def on_tello_video_capture(self):
        while True:
            frame = self.get_frame()
            if frame is None:
                continue
            self.frame = frame

            if self.video_callback is not None:
                self.video_callback(self.frame)

            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("frame", self.frame)

            if cv2.waitKey(1) == 27:
                break
        cv2.destroyAllWindows()

    def do_action(self):
        a = 0
        b = 0
        c = 0
        d = 0

        if KeyCode.from_char('q') in self.key_list:
            a -= self.speed
        if KeyCode.from_char('e') in self.key_list:
            a += self.speed
        if KeyCode.from_char('w') in self.key_list:
            b += self.speed
        if KeyCode.from_char('s') in self.key_list:
            b -= self.speed
        if KeyCode.from_char('u') in self.key_list:
            c += self.speed
        if KeyCode.from_char('j') in self.key_list:
            c -= self.speed
        if KeyCode.from_char('a') in self.key_list:
            d -= self.speed
        if KeyCode.from_char('d') in self.key_list:
            d += self.speed

        self.drone.do_rc(a, b, c, d)

    def run_video(self):
        video_thread = threading.Thread(target=self.on_tello_video_capture)
        video_thread.daemon = True
        video_thread.start()

    def run_keyboard(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()
