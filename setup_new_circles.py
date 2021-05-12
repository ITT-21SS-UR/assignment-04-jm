import random
import sys
import json

WINDOW_HEIGHT = 600
WINDOW_WIDTH = 800


# https://www.geeksforgeeks.org/check-two-given-circles-touch-intersect/
def __check_if_circles_touch(center_1_x, center_1_y, center_2_x, center_2_y, radius):
    dist_sq = (center_1_x - center_2_x) * (center_1_x - center_2_x) + (center_1_y - center_2_y) * (center_1_y - center_2_y);
    rad_sum_sq = (radius + radius) * (radius + radius)
    if dist_sq < rad_sum_sq:
        return True
    return False


def __create_new_random_coords(circle_radius):
    x_pos = random.randint(0, WINDOW_WIDTH-circle_radius)
    y_pos = random.randint(0, WINDOW_HEIGHT-circle_radius)
    new_coord = (x_pos, y_pos)
    return new_coord


def __create_circle_coordinates(number_of_circles, circle_radius):
    coord_list = []
    coord_string = ""
    for circle in range(int(number_of_circles)):
        new_coord = __create_new_random_coords(circle_radius)
        for coord in coord_list:
            while __check_if_circles_touch(new_coord[0], new_coord[1], coord[0], coord[1], circle_radius):
                print("intersect")
                new_coord = __create_new_random_coords(circle_radius)
        coord_list.append(new_coord)
        coord_string += f"({new_coord[0]},{new_coord[1]});"
    print(coord_string)

    coord_string = coord_string[:-1]  # remove last ";" from string
    return coord_string


def __write_config_to_file(number_of_circles, circle_radius, file_name):
    coord_string = __create_circle_coordinates(number_of_circles, circle_radius)
    setup_data_dict = {"numberOfCircles": number_of_circles, "circleRadius": circle_radius, "coordinates": coord_string}
    with open(file_name, "w") as file:
        json.dump(setup_data_dict, file)


if __name__ == '__main__':
    # argument1: number of circles
    __number_of_circles = int(sys.argv[1])
    # argument2: circle radius
    __circle_radius = int(sys.argv[2])
    # argument3: filename
    __file_name = sys.argv[3]
    __write_config_to_file(__number_of_circles, __circle_radius, __file_name)


