import sys
from PyQt5 import QtWidgets
from pointing_technique import BubbleCursor


def main():
    app = QtWidgets.QApplication(sys.argv)
    # if len(sys.argv) < 2:
    #     sys.stderr.write("Usage: %s <setup file>\n" % sys.argv[0])  # TODO usage information!
    #     sys.exit(1)

    targets = []  # TODO alle targets/circles übergeben!
    pointing_technique = BubbleCursor(all_targets=targets)
    pointing_technique.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
