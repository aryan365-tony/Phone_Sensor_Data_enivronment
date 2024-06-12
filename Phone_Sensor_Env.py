from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import numpy
import pandas
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class HttpClass(BaseHTTPRequestHandler):
    
    def do_POST(self):
        data_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(data_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            arr=numpy.array(self.filter_data(data))
            gyro = pandas.DataFrame(arr[numpy.where(arr[:, 0] == 'gyroscopeuncalibrated')[0]])
            acc = pandas.DataFrame(arr[numpy.where(arr[:, 0] == 'totalacceleration')[0]])
            mag = pandas.DataFrame(arr[numpy.where(arr[:, 0] == 'magnetometer')[0]])
    
            acc_data = numpy.array([list(item.values()) for item in acc.values[:, 1]])
            mag_data = numpy.array([list(item.values()) for item in mag.values[:, 1]])
            rollD,pitchD,yawD = self.calculate_orientation(acc_data,mag_data)
            app_window.update_orientation(rollD, pitchD, yawD)

        
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'error', 'message': 'Invalid JSON'})
            self.wfile.write(response.encode('utf-8'))

    def filter_data(self, data):
        filter_criteria = {
            'name': ['totalacceleration', 'gyroscopeuncalibrated','magnetometer'],
        }
        
        filtered_data = []
        data=data['payload']
        for item in data:
            if item['name'] in filter_criteria['name']:
                filtered_data.append([item['name'],item['values'],item['time']])
        
        return filtered_data
    
    def calculate_orientation(self, acc_data, mag_data):
        acc_x, acc_y, acc_z = acc_data[:80, 2], acc_data[:80, 1], acc_data[:80, 0]
        mag_x, mag_y, mag_z = mag_data[:80, 2], mag_data[:80, 1], mag_data[:80, 0]

        pitch_acc = numpy.arctan2(acc_y, numpy.sqrt(acc_x**2 + acc_z**2))
        roll_acc = numpy.arctan2(acc_x, numpy.sqrt(acc_y**2 + acc_z**2))

        mag_yh = mag_x * numpy.cos(pitch_acc) + mag_z * numpy.sin(pitch_acc)
        mag_xh = mag_x * numpy.sin(roll_acc) * numpy.sin(pitch_acc) + mag_y * numpy.cos(roll_acc) - mag_z * numpy.sin(roll_acc) * numpy.cos(pitch_acc)
        yaw_mag = numpy.arctan2(-mag_yh, mag_xh)

        roll_deg = numpy.degrees(roll_acc)
        pitch_deg = numpy.degrees(pitch_acc)
        yaw_deg = numpy.degrees(yaw_mag)

        return roll_deg,pitch_deg,yaw_deg

def serverStart(server_class=HTTPServer, handler_class=HttpClass, port=8000):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(OpenGLWidget, self).__init__(parent)
        self.setMinimumSize(800, 600)
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

    def initializeGL(self):
        glClearColor(0.8, 0.8, 0.8, 1.0)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w/h, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -5)
        glRotatef(numpy.mean(self.roll), 1, 0, 0)
        glRotatef(numpy.mean(self.pitch), 0, 1, 0)
        glRotatef(numpy.mean(self.yaw), 0, 0, 1)

        glBegin(GL_QUADS)

        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-1.0, -1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(-1.0, 1.0, 1.0)

        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(1.0, -1.0, -1.0)

        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(-1.0, 1.0, -1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(1.0, 1.0, -1.0)

        glColor3f(1.0, 1.0, 0.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glVertex3f(1.0, -1.0, 1.0)
        glVertex3f(-1.0, -1.0, 1.0)

        glColor3f(1.0, 0.0, 1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glVertex3f(1.0, 1.0, -1.0)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(1.0, -1.0, 1.0)

        glColor3f(0.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(-1.0, -1.0, 1.0)
        glVertex3f(-1.0, 1.0, 1.0)
        glVertex3f(-1.0, 1.0, -1.0)

        glEnd()

    def update_orientation(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Phone Orientation Visualization")
        self.setGeometry(100, 100, 800, 600)

        self.openGLWidget = OpenGLWidget(self)
        self.setCentralWidget(self.openGLWidget)

    def update_orientation(self, roll, pitch, yaw):
        self.openGLWidget.update_orientation(roll, pitch, yaw)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app_window = MainWindow()
    app_window.show()

    server_thread = Thread(target=serverStart)
    server_thread.daemon = True
    server_thread.start()

    sys.exit(app.exec_())
