import os
import sys
import tty
import termios
import datetime
import signal
import traceback
from ui import *
from gantt import *

DAY_WEEK_TOGGLE = 'w'

PAN_UP = 'I'
PAN_DOWN = 'T'
PAN_LEFT = 'r'
PAN_RIGHT = 's'

PAN_TOP = 'g'
PAN_BOTTOM = 'G'
PAN_START = 'R'

SELECT_UP = 'i'
SELECT_DOWN = 't'

GROW_TASK = '+'
SHRINK_TASK = '-'

TOGGLE_DONE_OR_DEP = ' '
TOGGLE_SELECT_DEPS = 'd'

ADD_TASK = 'a'
EDIT_TASK = 'e'


def draw(view):

    # Clear
    clear()

    # Draw the grid
    drawGrid(view)

    drawTasks(view)

    # Flush
    sys.stdout.flush()

def process(view, char):

    if char == DAY_WEEK_TOGGLE:
        view.toggleView()

    elif char == PAN_RIGHT:
        view.panRight()
    elif char == PAN_LEFT:
        view.panLeft()
    elif char == PAN_UP:
        view.panUp()
    elif char == PAN_DOWN:
        view.panDown()

    elif char == PAN_TOP:
        view.firstTask = 0
    elif char == PAN_BOTTOM:
        view.firstTask = len(view.project.tasks) - ((view.height - 2)//2)
        if view.firstTask < 0:
            view.firstTask = 0
    elif char == PAN_START:
        view.firstDateOffset = 0

    elif char == SELECT_UP:
        view.selectUp()
    elif char == SELECT_DOWN:
        view.selectDown()

    elif char == GROW_TASK:
        view.growCurrent()
    elif char == SHRINK_TASK:
        view.shrinkCurrent()

    elif char == TOGGLE_DONE_OR_DEP:
        if view.selectingDeps:
            view.toggleDep()
        else:
            view.toggleDoneCurrent()

    elif char == TOGGLE_SELECT_DEPS:
        view.selectDeps()

    #elif char == ADD_TASK:
        #view.addTask()

    else:
        pass

    draw(view)

def onResize(view):
    view.updateSize()

    # Fix scrolling
    view.firstTask = min(view.firstTask, len(view.project.tasks) - ((view.height - TASK_Y_OFFSET + 1)//2))
    if view.firstTask < 0:
        view.firstTask = 0

    draw(view)

if __name__ == '__main__':

    # Setup raw mode
    fd = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin)

    try:

        # Create the project and view
        project = Project('Example project')
        project.startDate = datetime.date(2021, 5, 12)
        project.addTask('Task 0', 1, 0)
        project.addTask('Task 1', 1, 0)
        project.addTask('Task 2', 1, 0)
        project.addTask('Task 3', 1, 0)
        project.addTask('Task 4', 1, 0)
        project.addTask('Task 5', 1, 0)
        project.addTask('Task 6', 1, 0)
        project.addTask('Task 7', 1, 0)
        project.addTask('Task 8', 1, 0)
        project.addTask('Task 9', 1, 0)
        project.addTask('Task 10', 1, 0)
        project.addTask('Task 11', 1, 0)
        project.addTask('Task 12', 1, 0)
        project.addTask('Task 13', 1, 0)
        project.addTask('Task 14', 1, 0)
        project.addTask('Task 15', 1, 0)
        project.addTask('Task 16', 1, 0)
        project.addTask('Task 17', 1, 0)

        view = View(project)

        # Redraw on resize
        signal.signal(signal.SIGWINCH, lambda signum, frame: onResize(view))

        # Hide the cursor
        write('\x1b[?25l')

        # Draw the screen
        draw(view)

        # Read input
        while True:
            char = sys.stdin.read(1)
            if char == 'q':
                break
            process(view, char)

    # Avoid breaking the terminal after a crash
    except Exception:
        tb = traceback.format_exc()
    else:
        tb = ''

    # Restore terminal settings
    reset()
    clear()
    write('\x1b[?25h\n\r')
    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
    print(tb)
