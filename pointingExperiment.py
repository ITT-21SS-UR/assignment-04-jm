#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time
import pandas as pd
import os
import json


class PointingExperiment(QtWidgets.QWidget):

    def __init__(self, setup_file):
        super().__init__()
        self.__experiment_logger = PointingExperimentLogger()
        self.__participant_id = self.__experiment_logger.get_next_participant_id()
        self.__experiment_started = False
        self.__start_time = None
        self.__pointer_position_list = []
        self.__time_per_target_list = []
        self.__last_target_time = None

        self.__targetList = []
        self.__currentTargetId = 0
        self.__setup_file = setup_file
        self.__setup_dict = self.__setup_file_to_dict(self.__setup_file)
        self.__circle_count = self.__setup_dict["numberOfCircles"]
        self.__circle_radius = int(self.__setup_dict["circleRadius"])

        self.ui = uic.loadUi("pointing.ui", self)
        self.__init_ui()
        self.show()
        self.setMouseTracking(True)

    def __init_ui(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.startExperimentButton.clicked.connect(self.__start_experiment)
        self.ui.closeButton.clicked.connect(lambda: sys.exit(0))
        self.ui.participantIdTextBox.setPlainText(str(self.__participant_id))

    def __setup_file_to_dict(self, setup_file):
        with open(setup_file) as json_file:
            return json.load(json_file)

    def __start_experiment(self):
        self.__participant_id = int(self.ui.participantIdTextBox.toPlainText())
        self.__setup_targets(self.__setup_file)
        self.__start_time = time.time()
        self.__last_target_time = self.__start_time
        self.__experiment_started = True
        self.ui.stackedWidget.setCurrentIndex(2)

    def __read_line_from_file(self, setup_file, line_number) -> str:
        with open(setup_file) as file:
            return file.readlines()[line_number]

    def __setup_targets(self, circle_setup_file):
        new_widget = QWidget()
        new_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        round_button_stylesheet = "border-color: rgb(66, 69, 183); background-color: rgb(53, 132, 228); " \
                                  f"border-style: solid; border-radius: {self.__circle_radius}px;"
        circle_positions = self.__setup_dict["coordinates"].split(";")
        for i in range(len(circle_positions)):
            circle_center = circle_positions[i]
            circle_center = circle_center.replace("(", "")
            circle_center = circle_center.replace(")", "")
            circle_center = circle_center.split(",")
            print(circle_center)
            target = QLabel(new_widget)
            target.setStyleSheet(round_button_stylesheet)
            target.setFixedSize(self.__circle_radius * 2, self.__circle_radius * 2)
            target.move(int(circle_center[0]) - self.__circle_radius, int(circle_center[1]) - self.__circle_radius)
            target.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.__set_label_color(target, Qt.yellow)
            target.setObjectName(f"button_{i}")
            self.__targetList.append(target)
        self.ui.stackedWidget.addWidget(new_widget)

    def mousePressEvent(self, ev):
        if self.__experiment_started:
            if ev.button() == QtCore.Qt.LeftButton:
                self.__mouse_clicked_at(ev.x(), ev.y())

    def mouseMoveEvent(self, ev):
        if self.__experiment_started:
            current_target = self.__targetList[self.__currentTargetId]
            print(f"mousemoveeevent: {ev.x()}, {ev.y()}")
            if self.__check_if_point_inside_circle(ev.x(), ev.y(), current_target.x() + self.__circle_radius,
                                                   current_target.y() + self.__circle_radius, self.__circle_radius):
                print("over target")
                self.__set_label_color(self.__targetList[self.__currentTargetId], Qt.darkRed)
            else:
                self.__set_label_color(self.__targetList[self.__currentTargetId], Qt.blue)

    def __set_label_color(self, label, color):
        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(color)
        label.setGraphicsEffect(color_effect)

    def __mouse_clicked_at(self, pointer_x, pointer_y):
        current_target = self.__targetList[self.__currentTargetId]
        if self.__check_if_point_inside_circle(pointer_x, pointer_y, current_target.x() + self.__circle_radius,
                                               current_target.y() + self.__circle_radius, self.__circle_radius):
            self.__target_clicked(pointer_x, pointer_y)

    def __target_clicked(self, pointer_x, pointer_y):
        self.__set_label_color(self.__targetList[self.__currentTargetId], Qt.green)
        self.__time_per_target_list.append(time.time()-self.__last_target_time)
        self.__pointer_position_list.append((pointer_x, pointer_y))
        if self.__currentTargetId < len(self.__targetList) - 1:
            self.__currentTargetId += 1
            self.__set_label_color(self.__targetList[self.__currentTargetId], Qt.blue)
        else:
            self.__experiment_logger.add_new_log_data(self.__participant_id, 1, self.__pointer_position_list, self.__time_per_target_list, self.__start_time,
                                                      time.time(), 0)

    # https://www.geeksforgeeks.org/check-two-given-circles-touch-intersect/
    def __check_if_circles_touch(self, center_1_x, center_1_y, center_2_x, center_2_y, radius):
        dist_sq = (center_1_x - center_2_x) * (center_1_x - center_2_x) + (center_1_y - center_2_y) * (
                center_1_y - center_2_y)
        rad_sum_sq = (radius + radius) * (radius + radius)
        if dist_sq < rad_sum_sq:
            return True
        return False

    # https://stackoverflow.com/questions/481144/equation-for-testing-if-a-point-is-inside-a-circle
    def __check_if_point_inside_circle(self, point_x, point_y, circle_center_x, circle_center_y, circle_radius):
        if ((point_x - circle_center_x) ** 2 + (point_y - circle_center_y) ** 2) <= circle_radius ** 2:
            return True
        else:
            return False


class PointingExperimentLogger:

    def __init__(self):
        self.__log_file_name = "pointingExperimentLog.csv"
        self.__study_data = self.__init_study_data()

    def __init_study_data(self):
        # check if the file already exists
        if os.path.isfile(self.__log_file_name):
            study_data = pd.read_csv(self.__log_file_name)
        else:
            study_data = pd.DataFrame(
                columns=['timestamp', 'participantID', 'condition',  'pointerPositionsPerTarget', 'timesPerTarget',
                         'startTimeInMS', 'endTimeInMS', 'timeTillFinishedInS', 'missedClickCount'])
        return study_data

    def add_new_log_data(self, participant_id, condition, pointer_position_list, time_per_target_list, start_time,
                         end_time, missed_clicks):
        self.__study_data = self.__study_data.append({'timestamp': time.time(), 'participantID': participant_id,
                                                      'condition': condition, 'pointerPositionsPerTarget': pointer_position_list, 'timesPerTarget':
                                                          time_per_target_list, 'startTimeInMS':
                                                          start_time, 'endTimeInMS': end_time, 'timeTillFinishedInS':
                                                          end_time - start_time, 'missedClickCount': missed_clicks},
                                                     ignore_index=True)
        self.__study_data.to_csv(self.__log_file_name, index=False)

    def get_next_participant_id(self):
        try:
            return self.__study_data["participantID"].max()
        except ValueError:
            return 1

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    try:
        pointing_experiement = PointingExperiment(sys.argv[1])
    except IndexError:
        print("Please enter your setup_file name as parameter, you can generate a ") # TODO with what?

    sys.exit(app.exec_())
