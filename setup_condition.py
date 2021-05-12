import random
import sys
import json

WINDOW_HEIGHT = 600
WINDOW_WIDTH = 800


def __create_new_random_coords(max_circle_radius):
    x_pos = random.randint(max_circle_radius, WINDOW_WIDTH-max_circle_radius)
    y_pos = random.randint(max_circle_radius, WINDOW_HEIGHT-max_circle_radius)
    new_coord = (x_pos, y_pos)
    return new_coord


def __create_circle_coordinates(number_of_circles, circle_radius_list):
    coord_list = []
    coord_string = ""
    print(circle_radius_list)
    for circle in range(int(number_of_circles)):
        new_coord = __create_new_random_coords(max(circle_radius_list))
        while new_coord in coord_list:
            new_coord = __create_new_random_coords(max(circle_radius_list))
        coord_list.append(new_coord)
        coord_string += f"({new_coord[0]},{new_coord[1]});"
    print(coord_string)

    coord_string = coord_string[:-1]  # remove last ";" from string
    return coord_string


def __write_config_to_file(number_of_circles, circle_radius, file_name):
    coord_string = __create_circle_coordinates(number_of_circles, circle_radius)
    setup_data_dict = {"numberOfCircles": number_of_circles, "circleRadiusList": circle_radius, "coordinates": coord_string}
    with open(file_name, "w") as file:
        json.dump(setup_data_dict, file)


if __name__ == '__main__':
    # argument1: number of circles
    __number_of_circles = int(sys.argv[1])
    # argument2: circle radius
    __circle_radius_list = list(map(int, sys.argv[2].strip('[]').split(',')))
    # argument3: filename
    __file_name = sys.argv[3]
    __write_config_to_file(__number_of_circles, __circle_radius_list, __file_name)


