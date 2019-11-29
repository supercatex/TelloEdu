import socket
import threading
import time
import libh264decoder
import numpy as np


class TelloEdu:

    def __init__(self, ip="192.168.10.1"):
        print("Initializing Tello Edu...")
        self.tello_ip_address = ip
        self.tello_cmd_port = 8889
        self.tello_address = (self.tello_ip_address, self.tello_cmd_port)

        self.response = None
        self.frame = None
        self.locked = False
        self.is_ready = False

        print("Connecting Tello Edu command service...")
        self.cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd_socket.bind(("", 8889))

        self.receive_cmd_thread = threading.Thread(target=self._receive_cmd_thread)
        self.receive_cmd_thread.daemon = True
        self.receive_cmd_thread.start()

        print("Connecting Tello Edu video channel...")
        self.decoder = libh264decoder.H264Decoder()
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_socket.bind(("", 11111))

        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()

        self.do_command(True)
        self.do_stream_on(True)
        self.get_battery(True)

        if self.response is not None:
            self.is_ready = True
            print("Tello Edu is ready.")
        else:
            print("No response from Tello Edu.")

    def __del__(self):
        self.socket.close()

    def _receive_cmd_thread(self):
        while True:
            try:
                self.response, ip = self.cmd_socket.recvfrom(3000)
                print(self.response)
                self.locked = False
            except Exception as e:
                print(e)

    def _receive_video_thread(self):
        packet_data = ""
        while True:
            try:
                res_string, ip = self.video_socket.recvfrom(2048)
                packet_data += res_string
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                    packet_data = ""
            except Exception as e:
                print(e)

    def _h264_decode(self, packet_data):
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                frame = np.fromstring(frame, dtype=np.ubyte, count=len(frame), sep="")
                frame = (frame.reshape((h, ls / 3, 3)))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)
        return res_frame_list

    def send_command(self, cmd, wait=False):
        self.response = None
        self.cmd_socket.sendto(cmd.encode("UTF-8"), self.tello_address)
        print("Command '%s' sent. %f" % (cmd, time.time()))
        if wait:
            self.locked = True
            print("Waiting command '%s' response..." % cmd)
            start_time = time.time()
            while self.locked and time.time() - start_time < 3:
                time.sleep(0.1)

    def do_command(self, wait=False):
        self.send_command("command", wait)

    def do_stream_on(self, wait=False):
        self.send_command("streamon", wait)

    def do_stream_off(self):
        self.send_command("streamoff")

    def get_battery(self, wait=False):
        self.send_command("battery?", wait)

    def do_takeoff(self):
        self.send_command("takeoff")

    def do_land(self):
        self.send_command("land")

    def do_stop(self):
        self.send_command("stop")

    def do_rc(self, a, b, c, d):
        self.send_command("rc %d %d %d %d" % (a, b, c, d))

    def do_find_card(self, index):
        time.sleep(0.5)
        self.send_command("go 0 0 100 30 m%d" % index)
        time.sleep(0.1)
