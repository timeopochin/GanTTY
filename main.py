import os
import sys
import tty
import termios
import datetime
import signal
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
    elif char == PAN_UP:
        if view.firstTask > 0:
            view.firstTask -= 1
    elif char == PAN_DOWN:
        if view.firstTask < len(view.project.tasks) - ((view.height - 2)//2):
            view.firstTask += 1
    elif char == PAN_LEFT:
        view.firstDateOffset -= 1 if view.view == WEEK else 7
        if view.firstDateOffset < 0:
            view.firstDateOffset = 0
    elif char == PAN_RIGHT:
        view.firstDateOffset += 1 if view.view == WEEK else 7
    elif char == PAN_TOP:
        view.firstTask = 0
    elif char == PAN_BOTTOM:
        view.firstTask = len(view.project.tasks) - ((view.height - 2)//2)
    elif char == PAN_START:
        view.firstDateOffset = 0
    else:
        pass

    draw(view)

    sys.stdout.flush()

def onResize(view):
    view.updateSize()

    # Fix scrolling
    view.firstTask = min(view.firstTask, len(view.project.tasks) - ((view.height - 2)//2))

    draw(view)

if __name__ == '__main__':

    # Setup raw mode
    fd = sys.stdin.fileno()
    oldSettings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin)

    try:

        # Create the project and view
        project = Project('Example project')
        project.startDate = datetime.date.today()
        project.addTask('Task 1', 1, 0, DONE)
        project.addTask('Task 2', 2, 0, DONE)
        project.addTask('Task 3', 3, 0, DONE)
        project.addTask('Task 4', 4, 0, DONE)
        project.addTask('Task 1', 1, 10, DONE)
        project.addTask('Task 2', 2, 10, DONE)
        project.addTask('Task 3', 3, 10, DONE)
        project.addTask('Task 4', 4, 10, DONE)
        project.addTask('Task 1', 1, 20, DONE)
        project.addTask('Task 2', 2, 20, DONE)
        project.addTask('Task 3', 3, 20, DONE)
        project.addTask('Task 4', 4, 20, DONE)
        project.addTask('Task 1', 1, 30, DONE)
        project.addTask('Task 2', 2, 30, DONE)
        project.addTask('Task 3', 3, 30, DONE)
        project.addTask('Task 4', 4, 30, DONE)

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
    except Exception as e:
        print(e, end = '\n\r')

    # Restore terminal settings
    clear()
    write('\x1b[?25h\n\r')
    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
