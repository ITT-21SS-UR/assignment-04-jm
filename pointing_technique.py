#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This Bubble Cursor implementation is based on the javascript source code for this demo:
https://filosophy.org/projects/bubbleCursor/.

The "BubbleCursor" technique was originally introduced in:
    Grossman, T., & Balakrishnan, R. (2005, April).
    The bubble cursor: enhancing target acquisition by dynamic resizing of the cursor's activation area.
    In Proceedings of the SIGCHI conference on Human factors in computing systems (pp. 281-290).

Concept:
The main idea behind the "BubbleCursor" is to show a circle-shaped area around the mouse cursor position and to
dynamically resize it based on the distance to the surrounding targets so that only one target (the one that is closest
to the mouse cursor) is selectable at any time (because of the resizing the area ALWAYS contains one selectable target
no matter where the actual cursor is right now). This is done by finding the two closest targets on each mouse move
and calculating the euclidean distances between the target center and mouse position. The containment distance for the
closest target and the intersecting distance for the second closest target are calculated as described in the paper
and the area radius is set to the smaller one of these two distances so the area scales to the minimal necessary size.

This concept makes it far easier for the user to select the correct target in less time than with a normal cursor
because the target is clickable from a greater range (effectively the target area is made bigger than it actually is).

The implementation of the BubbleCursors' ability to morph its area around the closest target if it is not fully
containable by the cursor area without intersecting another target is done by highlighting the currently selected
target with a border. This could be improved in the future to provide a better visual cue for users as shown in the
paper above.


The pointing technique was completely implemented by Michael Meckl.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QMouseEvent, QPainter
from PyQt5.QtCore import Qt
from math import inf, sqrt


class Target(QtWidgets.QWidget):

    def __init__(self, x: int, y: int, size: int):
        super(Target, self).__init__()
        self._x = x
        self._y = y
        self._s = size

        self.selected = False

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def size(self):
        return self._s


class BubbleCursor:

    def __init__(self, all_targets: list, target_size: int, border_size: int = 10):
        super(BubbleCursor, self).__init__()

        self.__target_radius = target_size
        self.__highlight_border_size = border_size
        self.__all_targets = all_targets

        self.__show_highlight = False
        self.__last_x, self.__last_y = None, None  # track the mouse position
        self.__best_target, self.__second_best_target = None, None  # track targets
        self.__distance_current, self.__distance_best, self.__distance_second_best = inf, inf, inf  # and distances
        self.__bubble_radius = None  # the radius of the area around the cursor

    @property
    def selectedTarget(self):
        return self.__best_target

    def onMouseMoved(self, event: QMouseEvent):
        # save the current mouse position to show an area around it later
        self.__last_x = event.x()
        self.__last_y = event.y()

        self._filter(event)

    def _filter(self, mouse_event: QMouseEvent) -> None:
        # reset targets
        self.__best_target = None
        self.__second_best_target = None

        # reset the distances to a large value (infinity), so the algorithm to find the nearest two targets will work
        self.__distance_current, self.__distance_best, self.__distance_second_best = inf, inf, inf

        # find the two closest targets to the mouse pointer
        self._find_nearest_targets(mouse_event.x(), mouse_event.y())
        # self._debug()

        # adjust the bubble size based on the two closest targets intersecting and containment distances;
        # see Grossman & Balakrishnan (2005)
        # TODO (second_)best_target.size statt self.__target_radius, damit dynamische Größe möglich wäre
        containment_distance_best = self.__distance_best + self.__target_radius
        intersecting_distance_second_best = self.__distance_second_best - self.__target_radius
        self.__bubble_radius = min(containment_distance_best, intersecting_distance_second_best)

        if containment_distance_best > intersecting_distance_second_best:
            # morph bubble area to encompass the closest target (i.e. highlight the closest target)
            self.__show_highlight = True

    def _find_nearest_targets(self, pos_x: int, pos_y: int) -> None:
        for i in range(0, len(self.__all_targets)):
            # get the target at position i
            current_target = self.__all_targets[i]
            # get the euclidean distance between mouse position and the current target center
            self.__distance_current = sqrt((current_target.x - pos_x) ** 2 + (current_target.y - pos_y) ** 2)

            if self.__distance_current < self.__distance_best:
                if self.__best_target is not None:
                    # if the closest (i.e. the best) target already exists and a target with a smaller distance is
                    # found, save the currently best target as second best target before overwriting it
                    self.__second_best_target = self.__best_target
                    self.__distance_second_best = self.__distance_best

                # a smaller distance than the best one has been found; replace the best target with the current target
                self.__best_target = current_target
                self.__distance_best = self.__distance_current

            elif self.__distance_current < self.__distance_second_best:
                # if the current distance is at least better (i.e. smaller) than the currently second smallest,
                # update the second best target
                self.__second_best_target = current_target
                self.__distance_second_best = self.__distance_current

    def _debug(self) -> None:
        if self.__best_target is None or self.__second_best_target is None:
            return
        print(f"currentMousePos: x={self.__last_x}, y={self.__last_y}")
        print(f"BestTarget: x={self.__best_target.x}, y={self.__best_target.y}")
        print(f"SecondBestTarget: x={self.__second_best_target.x}, y={self.__second_best_target.y}")
        print("All Targets:", [coords for coords in map(lambda x: [x.x, x.y], self.__all_targets)])

    def onPaintEvent(self, painter: QPainter):
        if self.__last_x is None:
            return  # Return immediately until we have the first mouse coordinates, otherwise it crashes!

        self._draw_bubble_area(painter)

        if self.__show_highlight:
            self._draw_highlight(painter)
            # self.__show_highlight = False  # activate to highlight only when closest target is not fully encompassed

    def _draw_bubble_area(self, painter: QPainter) -> None:
        if self.__bubble_radius is None:
            return

        pen = QtGui.QPen(Qt.NoPen)  # set to NoPen so no outline will be drawn
        painter.setPen(pen)

        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(170, 170, 170, 50))  # fill the area around the cursor with a transparent grey
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        # The actual radius is made a little bit smaller than the calculated one as a small visual improvement so it
        # doesn't seem to touch the second closest target as well.
        # This idea is described in the paper mentioned at the beginning by Grossman & Balakrishnan (2005).
        area_radius = self.__bubble_radius - 2
        # draw a circle around the current mouse position
        painter.drawEllipse(QtCore.QPoint(self.__last_x, self.__last_y), area_radius, area_radius)

    def _draw_highlight(self, painter: QPainter) -> None:
        if self.__best_target is None:
            return

        pen = QtGui.QPen(Qt.NoPen)  # don't draw an outline
        painter.setPen(pen)

        # show a filled border with a slightly transparent gray to create a highlight effect for the current target
        brush = QtGui.QBrush()
        # brush.setColor(QtGui.QColor(120, 255, 120, 80))
        brush.setColor(QtGui.QColor(170, 170, 170, 50))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)

        highlight_radius = self.__target_radius + self.__highlight_border_size
        rect_x = self.__best_target.x
        rect_y = self.__best_target.y
        painter.drawEllipse(QtCore.QPoint(rect_x, rect_y), highlight_radius, highlight_radius)
