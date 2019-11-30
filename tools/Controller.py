from pynput.keyboard import Key, Listener, KeyCode
import cv2
import time
import threading


class Controller(object):
    def __init__(self, drone, callback=None):
        self.drone = drone
        self.callback = callback
        self.key_list = []
        self.frame = None
        self.speed = 30

    def on_press(self, key):
        if key not in self.key_list:
            self.key_list.append(key)
            self.do_action()

    def on_release(self, key):
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

        if KeyCode.from_char('1') in self.key_list:
            self.key_list.remove(KeyCode.from_char('1'))
            self.drone.do_find_card(1)
            return

        if KeyCode.from_char('2') in self.key_list:
            self.key_list.remove(KeyCode.from_char('2'))
            self.drone.do_find_card(2)
            return

        if key in self.key_list:
            self.key_list.remove(key)
            self.do_action()

    def on_tello_video_capture(self):
        while True:
            if self.drone.frame is None:
                continue
            self.frame = self.drone.frame

            if self.callback is not None:
                self.callback(self.frame)

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

    def run(self):
        if self.drone.is_ready:
            video_thread = threading.Thread(target=self.on_tello_video_capture)
            video_thread.daemon = True
            video_thread.start()

            with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                listener.join()
        else:
            print("Drone is not ready yet.")
