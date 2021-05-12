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
from pointing_technique import BubbleCursor, Target
import math

'''We split the work on this assignment as follows:
    We planned our study together.
    Johannes Lorper implemented the experiment from task 4.1 and our setup helper "setup_condition.py. 
    Michael Meckl implemented the pointing technique
'''


class PointingExperiment(QtWidgets.QWidget):

    def __init__(self, setup_file, use_pointing_technique):
        super().__init__()
        self.__experiment_logger = PointingExperimentLogger()
        self.__participant_id = self.__experiment_logger.get_next_participant_id()
        self.__experiment_started = False
        self.__custom_pointing_technique_active = use_pointing_technique
        self.__start_time = None

        self.__target_label_list = []
        self.__all_targets = []
        self.__setup_file = setup_file
        self.__setup_dict = self.__setup_file_to_dict(self.__setup_file)
        self.__circle_count = self.__setup_dict["numberOfCircles"]
        self.__condition_list = self.__setup_dict["circleRadiusList"]
        self.__counter_balanced_condition_list = []  # will be set on experiment start
        self.__condition_count = len(self.__counter_balanced_condition_list)
        self.__current_condition_id = 0

        self.ui = uic.loadUi("pointing.ui", self)
        self.__init_ui()
        self.show()
        self.setMouseTracking(True)

    def __init_ui(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.startExperimentButton.clicked.connect(self.__start_experiment)
        self.ui.closeButton.clicked.connect(lambda: sys.exit(0))
        self.ui.participantIdTextBox.setPlainText(str(self.__participant_id))

    def __get_balanced_condition_list(self, condition_list, participant_id):
        condition_count = len(condition_list)

        # First we need to create a balanced latin square according to our number of conditions:
        # https://medium.com/@graycoding/balanced-latin-squares-in-python-2c3aa6ec95b9
        balanced_order = [[((j // 2 + 1 if j % 2 else condition_count - j // 2) + i) % condition_count + 1 for j in
                           range(condition_count)] for i in range(condition_count)]
        if condition_count % 2:  # Repeat reversed for odd n
            balanced_order += [seq[::-1] for seq in balanced_order]
        order_for_participant = balanced_order[participant_id % condition_count]

        # Now we will reorder our conditions-list with the balanced-latin-square order we created above
        # https://stackoverflow.com/questions/2177590/how-can-i-reorder-a-list/2177607
        for i in range(len(order_for_participant)):
            order_for_participant[i] -= 1

        return [condition_list[i] for i in order_for_participant]

    def __setup_file_to_dict(self, setup_file):
        with open(setup_file) as json_file:
            return json.load(json_file)

    def __start_experiment(self):

        self.__currentTargetId = 0
        self.__target_label_list = []
        self.__all_targets = []
        self.__pointer_position_list = []
        self.__time_per_target_list = []
        self.__miss_click_count = 0

        self.__participant_id = int(self.ui.participantIdTextBox.toPlainText())
        self.__counter_balanced_condition_list = self.__get_balanced_condition_list(self.__condition_list,
                                                                                    self.__participant_id)
        self.__setup_targets()
        self.__start_time = time.time()
        self.__last_target_time = self.__start_time
        self.__move_mouse_to_top_left_corner()
        self.__experiment_started = True

        self.ui.stackedWidget.setCurrentIndex(self.__current_condition_id + 2)
        self.__set_label_color(self.__target_label_list[self.__currentTargetId], Qt.blue)
        if self.__custom_pointing_technique_active == 1:
            self._setup_pointing_technique()

    def __move_mouse_to_top_left_corner(self):
        QtGui.QCursor.setPos(0, 0)

    def _setup_pointing_technique(self):

        self.__pointing_technique = BubbleCursor(all_targets=self.__all_targets, target_size=self.__circle_radius)

    def __read_line_from_file(self, setup_file, line_number) -> str:
        with open(setup_file) as file:
            return file.readlines()[line_number]

    def __setup_targets(self):
        self.__circle_radius = self.__counter_balanced_condition_list[self.__current_condition_id]
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

            target_label = QLabel(new_widget)
            target_label.setStyleSheet(round_button_stylesheet)
            target_label.setFixedSize(self.__circle_radius * 2, self.__circle_radius * 2)

            # x and y need to be the top left coordinates of the rectangle that is styled as a circle to position
            # it correctly; because of this we subtract the radius from both to get the top left coordinates
            x_pos_rect = int(circle_center[0]) - self.__circle_radius
            y_pos_rect = int(circle_center[1]) - self.__circle_radius
            target_label.move(x_pos_rect, y_pos_rect)
            target_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            # target_label.setAttribute(Qt.WA_MacShowFocusRect, on=False)
            self.__set_label_color(target_label, Qt.yellow)
            target_label.setObjectName(f"button_{i}")
            self.__target_label_list.append(target_label)
            target = Target(int(circle_center[0]), int(circle_center[1]), self.__circle_radius)
            self.__all_targets.append(target)
        self.ui.stackedWidget.addWidget(new_widget)

    def mousePressEvent(self, ev):
        if self.__experiment_started:
            if ev.button() == QtCore.Qt.LeftButton:
                if self.__custom_pointing_technique_active == 1:
                    current_target = self.__all_targets[self.__currentTargetId]
                    currently_selected_target = self.__pointing_technique.selectedTarget
                    if current_target == currently_selected_target:
                        self.__target_clicked(ev.x(), ev.y())
                    else:
                        self.__miss_click_count += 1
                else:
                    current_target = self.__target_label_list[self.__currentTargetId]
                    if self.__check_if_point_inside_circle(ev.x(), ev.y(), current_target.x() + self.__circle_radius,
                                                           current_target.y() + self.__circle_radius,
                                                           self.__circle_radius):
                        self.__target_clicked(ev.x(), ev.y())
                    else:
                        self.__miss_click_count += 1

    def mouseMoveEvent(self, ev):
        if self.__experiment_started:
            if self.__custom_pointing_technique_active == 1:
                self.__pointing_technique.onMouseMoved(ev)
            self.update()
            current_target = self.__target_label_list[self.__currentTargetId]
            if self.__check_if_point_inside_circle(ev.x(), ev.y(), current_target.x() + self.__circle_radius,
                                                   current_target.y() + self.__circle_radius, self.__circle_radius):
                self.__set_label_color(self.__target_label_list[self.__currentTargetId], Qt.darkRed)
            else:
                self.__set_label_color(self.__target_label_list[self.__currentTargetId], Qt.blue)

    def __set_label_color(self, label, color):
        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(color)
        label.setGraphicsEffect(color_effect)

    def __mouse_clicked_at(self, pointer_x, pointer_y):
        current_target = self.__targetList[self.__currentTargetId]

    def __target_clicked(self, pointer_x, pointer_y):
        click_time = time.time()
        self.__set_label_color(self.__target_label_list[self.__currentTargetId], Qt.yellow)
        self.__time_per_target_list.append(click_time - self.__last_target_time)
        self.__pointer_position_list.append((pointer_x, pointer_y))
        if self.__currentTargetId < len(self.__target_label_list) - 1:
            self.__currentTargetId += 1
            self.__set_label_color(self.__target_label_list[self.__currentTargetId], Qt.blue)
        else:
            self.__experiment_logger.add_new_log_data(self.__participant_id, self.__current_condition_id,
                                                      self.__pointer_position_list, self.__time_per_target_list,
                                                      self.__start_time, click_time, self.__miss_click_count,
                                                      self.__custom_pointing_technique_active == 1)
            if self.__current_condition_id < len(self.__condition_list) - 1:
                self.__current_condition_id += 1
                self.__start_experiment()
            else:
                self.ui.stackedWidget.setCurrentIndex(1)
                self.__experiment_started = False

        self.__last_target_time = click_time

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

    def paintEvent(self, event: QPaintEvent):
        if self.__experiment_started and self.__custom_pointing_technique_active == 1:
            # The QPainter code MUST be in the paintEvent if inheriting from a QWidget!
            # (alternatively a pixmap() could be used as a custom canvas for drawing)
            painter = QtGui.QPainter()
            painter.begin(self)
            self.__pointing_technique.onPaintEvent(painter)
            # self.__custom_pointing_technique_active = False
            painter.end()


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
                columns=['timestamp', 'participantID', 'condition', 'pointerPositionsPerTarget', 'timesPerTargetInS',
                         'startTimeAsUnix', 'endTimeAsUnix', 'timeTillFinishedInS', 'missedClickCount',
                         'bubblePointingTechnique'])
        return study_data

    def add_new_log_data(self, participant_id, condition, pointer_position_list, time_per_target_list, start_time,
                         end_time, missed_clicks, bubble_pointing_active):

        self.__study_data = self.__study_data.append({'timestamp': time.time(), 'participantID': participant_id,
                                                      'condition': condition,
                                                      'pointerPositionsPerTarget': pointer_position_list,
                                                      'timesPerTargetInS':
                                                          time_per_target_list, 'startTimeAsUnix':
                                                          start_time, 'endTimeAsUnix': end_time, 'timeTillFinishedInS':
                                                          end_time - start_time, 'missedClickCount': missed_clicks,
                                                      'bubblePointingTechnique': bubble_pointing_active},
                                                     ignore_index=True)
        self.__study_data.to_csv(self.__log_file_name, index=False)
        with open(self.__log_file_name) as file:
            print(file.readlines()[-1])

    def get_next_participant_id(self):
        if not math.isnan(self.__study_data["participantID"].max()):
            return self.__study_data["participantID"].max() + 1
        else:
            return 1


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    try:
        setup_file_arg = sys.argv[1]
    except IndexError:
        print("Please enter your setup_file name as parameter, you can generate one with setup_condition.py")
        sys.exit(app.exec_())
    try:
        use_pointing_technique_arg = int(sys.argv[2])
    except:
        print("Please enter if you want to use a pointing technique as second parameter (0=No, 1=Yes)")
        sys.exit(app.exec_())
    pointing_experiment = PointingExperiment(setup_file_arg, use_pointing_technique_arg)

    sys.exit(app.exec_())
