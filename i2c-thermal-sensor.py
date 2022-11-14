#!/usr/bin/python3
from adafruit_mlx90614 import MLX90614
from board import SCL, SDA
from busio import I2C
from datetime import datetime
from PyQt5.QtCore import QEventLoop, QThread, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from pyqtgraph import AxisItem, mkPen, PlotWidget
import sys

mlx = MLX90614(I2C(SCL, SDA, frequency=100000))

datapoints = 60
interval = 5


class DataCaptureThread(QThread):
    def __init__(self, plotWidget):
        QThread.__init__(self)
        self.plotWidget = plotWidget

        dt = datetime.now()
        self.x = list(map(lambda i: datetime.timestamp(dt) + (i * interval), range(datapoints * -1 + 1, 1)))
        self.y1 = [22.0] * datapoints
        self.y2 = [22.0] * datapoints

        redPen = mkPen(color=(255, 0, 0), width=2)
        greenPen = mkPen(color=(0, 255, 0), width=2)
        self.object = self.plotWidget.plot(self.x, self.y1, name='Object', pen=redPen)
        self.ambient = self.plotWidget.plot(self.x, self.y2, name='Ambience', pen=greenPen)

        self.dataCollectionTimer = QTimer()
        self.dataCollectionTimer.moveToThread(self)
        self.dataCollectionTimer.timeout.connect(self.captureSensorData)

    def captureSensorData(self):
        self.x = self.x[1:] + [datetime.timestamp(datetime.now())]
        try:
            objectTemp = mlx.object_temperature
            ambientTemp = mlx.ambient_temperature
            self.y1 = self.y1[1:] + [objectTemp]
            self.y2 = self.y2[1:] + [ambientTemp]
            print(f"{datetime.now()}: Object: {objectTemp:.2f} °C, Ambience: {ambientTemp:.2f} °C", flush=True)
        except OSError as e:
            print(e, flush=True)
            self.y1 = self.y1[1:] + self.y1[-1]
            self.y2 = self.y2[1:] + self.y2[-1]
        self.object.setData(self.x, self.y1)
        self.ambient.setData(self.x, self.y2)

    def run(self):
        self.dataCollectionTimer.start(interval * 1000)
        loop = QEventLoop()
        loop.exec_()


class TimeAxisItem(AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        return [datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("I²C Thermal Sensor")

        self.plotWidget = PlotWidget(
            labels={'left': 'Temperature (°C)'},
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        self.plotWidget.addLegend()
        self.plotWidget.showGrid(x=True, y=True)
        self.setCentralWidget(self.plotWidget)

        self.dataCaptureThread = DataCaptureThread(plotWidget=self.plotWidget)
        self.dataCaptureThread.start()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

