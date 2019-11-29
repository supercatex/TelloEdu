from pynput.keyboard import Key, Listener, KeyCode
import cv2
import threading
from tools import TelloEdu
from SocketObject import SocketClient
import time


def on_press(key):
    global key_list
    if key not in key_list:
        key_list.append(key)
        do_action()


def on_release(key):
    global key_list, speed, is_auto

    if Key.esc in key_list:
        Listener.stop()

    if Key.space in key_list:
        key_list.remove(Key.space)
        tello.do_stop()
        return

    if KeyCode.from_char('t') in key_list:
        tello.do_takeoff()

    if KeyCode.from_char('g') in key_list:
        tello.do_land()

    if Key.up in key_list:
        speed = min(speed + 5, 100)

    if Key.down in key_list:
        speed = max(speed - 5, 20)

    if KeyCode.from_char('o') in key_list:
        tello.send_command("mon")
        time.sleep(0.1)
        tello.send_command("mdirection 0")
        time.sleep(0.1)

    if KeyCode.from_char('p') in key_list:
        tello.send_command("moff")

    if KeyCode.from_char('1') in key_list:
        key_list.remove(KeyCode.from_char('1'))
        tello.do_find_card(1)
        return

    if KeyCode.from_char('2') in key_list:
        key_list.remove(KeyCode.from_char('2'))
        tello.do_find_card(2)
        return

    if KeyCode.from_char('0') in key_list:
        key_list.remove(KeyCode.from_char('0'))
        is_auto = not is_auto
        return

    if key in key_list:
        key_list.remove(key)
        do_action()


def detect_yellow(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = (25, 100, 100)
    upper = (30, 255, 255)
    mask = cv2.inRange(hsv, lower, upper)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_cnt = None
    max_area = 0
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area > 2000:
            if max_cnt is None:
                max_cnt = cnt
                max_area = area
            elif max_area < area:
                max_cnt = cnt
                max_area = area
    if max_cnt is not None:
        x, y, w, h = cv2.boundingRect(max_cnt)
        # cv2.drawContours(image, [max_cnt], 0, (0, 0, 255), 2)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cx = x + w // 2
        cy = y + h // 2
        cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)
        return cx, cy
    return None, None


def on_video_capture():
    global object_detect, sc, out
    camera = cv2.VideoCapture(0)
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break

        if object_detect:
            sc.send_image(frame)
            frame = sc.receive_image()
        if frame is not None:
            # detect_yellow(frame)
            cv2.imshow("frame", frame)
            out.write(frame)

        if cv2.waitKey(1) == 27:
            break
    camera.release()
    out.release()
    cv2.destroyAllWindows()


def on_tello_video_capture():
    global tello, object_detect, is_auto, out
    valid_frame = None
    while True:
        frame = tello.frame

        if frame is None:
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if object_detect:
            sc.send_image(frame)
            frame = sc.receive_image()
        if frame is not None:
            frame = auto_mission(frame)
            cx, cy = detect_yellow(frame)
            cv2.imshow("frame", frame)
            valid_frame = frame

            if is_auto and cx is not None and cy is not None:
                c = 0
                d = 0
                r = 50
                if cx < frame.shape[1] // 2 - r:
                    d = -20
                elif cx > frame.shape[1] // 2 + r:
                    d = 20
                if cy < frame.shape[0] // 2 - r * 4:
                    c = 20
                elif cy > frame.shape[0] // 2 - r * 2:
                    c = -20

                if c != 0 or d != 0:
                    tello.do_rc(0, 0, c, d)
                else:
                    tello.do_stop()
                    print("found")
                    time.sleep(3)
                    # tello.do_rc(0, 20, 0, 0)
                    # time.sleep(2)
                    is_auto = False
                    # tello.do_stop()

        if valid_frame is not None:
            print(valid_frame.shape)
            out.write(valid_frame)

        if cv2.waitKey(1) == 27:
            break
    out.release()
    cv2.destroyAllWindows()


def do_action():
    global key_list, tello, speed

    a = 0
    b = 0
    c = 0
    d = 0

    if KeyCode.from_char('q') in key_list:
        a -= speed
    if KeyCode.from_char('e') in key_list:
        a += speed
    if KeyCode.from_char('w') in key_list:
        b += speed
    if KeyCode.from_char('s') in key_list:
        b -= speed
    if KeyCode.from_char('u') in key_list:
        c += speed
    if KeyCode.from_char('j') in key_list:
        c -= speed
    if KeyCode.from_char('a') in key_list:
        d -= speed
    if KeyCode.from_char('d') in key_list:
        d += speed

    tello.do_rc(a, b, c, d)


mission = 0
def auto_mission(frame):
    global tello, mission

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = (36, 100, 50)
    upper = (40, 250, 250)
    mask = cv2.inRange(hsv, lower, upper)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_cnt = None
    max_area = 0
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area > 5500:
            if max_cnt is None:
                max_cnt = cnt
                max_area = area
            elif max_area < area:
                max_cnt = cnt
                max_area = area
    if max_cnt is not None:
        x, y, w, h = cv2.boundingRect(max_cnt)
        # cv2.drawContours(image, [max_cnt], 0, (0, 0, 255), 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cx = x + w // 2
        cy = y + h // 2
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        # return frame
        if mission == 0 or mission == 1:
            error = 80
            if max_area < 150000:
                vz = 0
                if cy > frame.shape[0] // 2 + error:
                    vz = -20
                elif cy < frame.shape[0] // 2:
                    vz = 20

                vy = 0
                if cx > frame.shape[1] // 2 - 40:
                    vy = 10
                elif cx < frame.shape[1] // 2 + 40:
                    vy = -10

                if vz == 0 and vy == 0:
                    tello.do_rc(0, 0, 0, 0)
                else:
                    tello.do_rc(0, 20, vz, vy)
                    if mission == 0:
                        tello.do_rc(0, 0, 0, -30)
                        cv2.waitKey(1000)
                    mission = 1
            else:
                if mission == 1:
                    tello.do_rc(0, 0, 0, 0)
                    mission = 2
        elif mission == 2:
            tello.do_rc(0, 0, 20, 0)
            cv2.waitKey(1000)
            tello.do_rc(0, 0, 0, 0)
            cv2.waitKey(1000)

            tello.send_command("tof?", True)
            h1 = int(tello.response.split("mm")[0])
            h2 = h1
            while abs(h1 - h2) < 250:
                tello.do_rc(0, 30, 0, 0)
                cv2.waitKey(500)
                tello.do_rc(0, 0, 0, 0)
                cv2.waitKey(500)
                tello.send_command("tof?", True)
                print(tello.response)
                h2 = int(tello.response.split("mm")[0])
            tello.do_rc(0, 20, 0, 0)
            cv2.waitKey(500)
            tello.do_land()
            cv2.waitKey(3000)
            mission = 3
    else:
        if mission == 0:
            tello.do_rc(0, 0, 0, -30)
        else:
            tello.do_rc(0, 0, 0, 0)
    print(mission, max_area)
    return frame


if __name__ == "__main__":
    speed = 30
    object_detect = False
    is_auto = False
    if object_detect:
        sc = SocketClient("127.0.0.1", 8886, "127.0.0.1", 8889)

    tello = TelloEdu()
    # tello.send_command("ap PCRM 12345678")

    fourcc = cv2.VideoWriter_fourcc(*'MP4V')

    if tello.is_ready:
        out = cv2.VideoWriter('./videos/{}.mp4'.format(time.strftime("%y%m%d%H%M%S", time.localtime())), fourcc, 100.0,
                              (960, 720))
        video_thread = threading.Thread(target=on_tello_video_capture)
    else:
        out = cv2.VideoWriter('./videos/{}.mp4'.format(time.strftime("%y%m%d%H%M%S", time.localtime())), fourcc, 10.0,
                              (640, 480))
        video_thread = threading.Thread(target=on_video_capture)
    video_thread.daemon = True
    video_thread.start()

    key_list = []
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
