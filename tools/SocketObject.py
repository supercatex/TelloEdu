import socket
import time
import cv2
import pickle
import struct


class SocketClient(object):

    def __init__(self, local_ip, local_port, target_ip, target_port):
        self.local_ip = local_ip
        self.local_port = local_port
        self.local_address = (local_ip, local_port)

        self.target_ip = target_ip
        self.target_port = target_port
        self.target_address = (target_ip, target_port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((local_ip, local_port))
        self.socket.connect(self.target_address)
        print(self.socket.recv(1024))

    def __del__(self):
        self.socket.shutdown(1)
        self.socket.close()

    def send_msg(self, msg):
        self.socket.sendto(msg.encode("UTF-8"), self.target_address)
        time.sleep(0.1)

    def send_image(self, image):
        success, image = cv2.imencode(".jpg", image)
        if not success:
            print("JPEG encode failed.")
        else:
            data = pickle.dumps(image, 0)
            size = len(data)
            self.socket.sendall(struct.pack(">L", size) + data)
            # print("JPEG image sent.")

    def receive_image(self):
        data = b""
        payload_size = struct.calcsize(">L")
        while True:
            while len(data) < payload_size:
                data += self.socket.recv(4096)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            while len(data) < msg_size:
                data += self.socket.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            image = pickle.loads(frame_data)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            return image


if __name__ == "__main__":
    sc = SocketClient("127.0.0.1", 8886, "127.0.0.1", 8888)

    camera = cv2.VideoCapture(0)
    while camera.isOpened():
        success, frame = camera.read()
        if not success:
            break

        sc.send_image(frame)
        frame = sc.receive_image()
        cv2.imshow("frame", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    camera.release()
