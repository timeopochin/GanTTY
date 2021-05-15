import os
import sys
import tty
import termios
import datetime
import signal
import traceback
import pickle
from ui import *
from gantt import *
from keys import *

def draw(view):

    # Clear
    clear()

    # Draw the grid
    drawGrid(view)

    drawTasks(view)

    drawInfo(view)

    # Flush
    sys.stdout.flush()

def process(view, char):

    redraw = True

    if len(view.project.tasks):

        # Needs at least 1 task
        if char == SELECT_UP:
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

        elif char == RENAME_TASK:
            view.renameCurrent(fd, oldSettings)
        elif char == DELETE_TASK:
            view.deleteCurrent(fd, oldSettings)
        elif char == EDIT_TASK:
            view.editCurrent()

    # Can be done with no tasks
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

    elif char == GROW_TASK_TITLE:
        view.growTaskTitle()
    elif char == SHRINK_TASK_TITLE:
        view.shrinkTaskTitle()

    elif char == ADD_TASK:
        view.addTask(fd, oldSettings)

    elif char == WRITE_TO_FILE:
        with open(FILE_NAME, 'wb') as ganttFile:
            pickle.dump(view, ganttFile)
        view.unsavedEdits = False
        drawInfo(view, 'Project saved!')
        sys.stdout.flush()
        redraw = False

    else:
        pass

    if redraw:
        draw(view)

def onResize(view):
    view.updateSize()

    # Fix scrolling
    view.firstTask = min(view.firstTask, len(view.project.tasks) - ((view.height - TASK_Y_OFFSET + 1)//2))
    if view.firstTask < 0:
        view.firstTask = 0

    draw(view)

# Get file name
if len(sys.argv) < 2:
    print('USAGE: gantt <filename>')
    exit()

FILE_NAME = sys.argv[1]

# Setup raw mode
fd = sys.stdin.fileno()
oldSettings = termios.tcgetattr(fd)
tty.setraw(sys.stdin)

endMsg = ''
endClear = False

try:

    try:
        with open(FILE_NAME, 'rb') as ganttFile:
            view = pickle.load(ganttFile)
        if type(view) is not View:
            endMsg = 'Could not read file correctly!'
            raise
        view.unsavedEdits = False
    except (FileNotFoundError, EOFError):
        view = View(Project('Untitled'))
    except pickle.UnpicklingError:
        endMsg = 'Could not read file correctly!'
        raise

    # Redraw on resize
    signal.signal(signal.SIGWINCH, lambda signum, frame: onResize(view))

    # Hide the cursor
    write('\x1b[?25l')

    # Draw the screen
    endClear = True
    draw(view)

    # Read input
    while True:
        char = sys.stdin.read(1)
        if char == QUIT:
            if view.unsavedEdits:
                confirm = getInputText(view, 'About to quit with unsaved edits! Are you sure you want to continue? ', fd, oldSettings)
                if confirm.lower() == 'yes':
                    break
            else:
                break
        process(view, char)

# Avoid breaking the terminal after a crash
except Exception:
    tb = traceback.format_exc()
else:
    tb = ''

# Restore terminal settings
reset()
if endClear:
    clear()
write('\x1b[?25h\n\r')
termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
if endMsg:
    print(endMsg)
else:
    print(tb)
