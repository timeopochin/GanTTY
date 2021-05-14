import os
import sys
import datetime
from gantt import *

# Colours
class colour:
    black = 0
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magenta = 5
    cyan = 6
    white = 7
    default = 9
    brightBlack = 60
    brightRed = 61
    brightGreen = 62
    brightYellow = 63
    brightBlue = 64
    brightMagenta = 65
    brightCyan = 66
    brightWhite = 67

DAY = 0
WEEK = 1

TASK_BG_COLOUR = colour.default

CURRENT_TASK_BG_COLOUR = colour.magenta
CURRENT_TASK_FG_COLOUR = colour.brightWhite

GRID_COLOUR_A = colour.black
GRID_COLOUR_B = colour.default

DONE_COLOUR = colour.brightCyan
ONGOING_COLOUR = colour.brightBlue
WAITING_COLOUR = colour.brightWhite

DONE_EXTRA_COLOUR = colour.cyan
ONGOING_EXTRA_COLOUR = colour.blue
WAITING_EXTRA_COLOUR = colour.brightBlack

CRITICAL_COLOUR = colour.brightYellow

TASK_WIDTH = 16
TASK_Y_OFFSET = 4

# Project view
class View:
    def __init__(self, project):
        self.project = project
        self.view = WEEK
        self.columnWidth = 7
        self.selectingDeps = False

        # Scrolling offsets
        self.firstDateOffset = 0
        self.firstTask = 0

        # Cursor
        self.currentTask = 0

        # Size
        self.updateSize()

        # Defaults
        self.gridColourA = GRID_COLOUR_A
        self.gridColourB = GRID_COLOUR_B
        self.taskWidth = TASK_WIDTH

    @property
    def firstDate(self):
        delta = datetime.timedelta(days = self.firstDateOffset)
        return self.project.startDate + delta

    @property
    def current(self):
        return self.project.tasks[self.currentTask]

    def updateSize(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        self.height = int(rows)
        self.width = int(columns)

    def toggleView(self):
        self.view = DAY if self.view == WEEK else WEEK

    def panLeft(self):
        self.firstDateOffset -= 1 if self.view == DAY else 7
        if self.firstDateOffset < 0:
            self.firstDateOffset = 0

    def panRight(self):
        self.firstDateOffset += 1 if self.view == DAY else 7

    def panUp(self):
        if self.firstTask > 0:
            self.firstTask -= 1

    def panDown(self):
        if self.firstTask < len(self.project.tasks) - ((self.height - TASK_Y_OFFSET + 1)//2):
            self.firstTask += 1

    def selectUp(self):
        if self.currentTask > 0:
            self.currentTask -= 1

    def selectDown(self):
        if self.currentTask < len(self.project.tasks) - 1:
            self.currentTask += 1

    def growCurrent(self):
        self.current.length += 1

    def shrinkCurrent(self):
        if self.current.length > 1:
            self.current.length -= 1

    def toggleDoneCurrent(self):
        self.current.isDone = not self.current.isDone

    def selectDeps(self):
        if self.selectingDeps:
            self.selectingDeps = False
            return
        self.selectingDeps = True
        self.depsFor = self.current

    def toggleDep(self):
        #if self.
        self.depsFor.setDep(self.currentTask)

# Writting and cursor
def write(text):
    sys.stdout.write(text)

def clear():
    write('\x1b[2J\x1b[1;1H')

def goto(x, y):
    write(f'\x1b[{y + 1};{x + 1}H')

def goleft(n):
    write(f'\x1b[{n}D')

def goright(n):
    write(f'\x1b[{n}C')

def goup(n):
    write(f'\x1b[{n}A')

def godown(n):
    write(f'\x1b[{n}B')

# Formating
def getBg(bg):
    bg += 40
    return f'\x1b[{bg}m'

def getFg(fg):
    fg += 30
    return f'\x1b[{fg}m'

def setBg(bg):
    bg = getBg(bg)
    write(bg)
    return bg

def setFg(fg):
    fg = getFg(fg)
    write(fg)
    return fg

def reset():
    write('\x1b[39;49m')

# UI
def drawGrid(view):
    date = view.firstDate
    delta = datetime.timedelta(days = 1 if view.view == DAY else 7)
    for y in range(view.height):
        goto(view.taskWidth, y)
        current = view.gridColourA
        setBg(current)
        for i in range((view.width - view.taskWidth)//view.columnWidth):
            if y == 1:
                day = '       '
                if view.view == DAY:
                    day = date.strftime('%a')
                    if not len(day) % 2:
                        day += ' '
                    while len(day) < 7:
                        day = ' ' + day + ' '
                write(day)
                godown(1)
                goleft(7)
                write(date.strftime(' %d/%m '))
                goup(1)
                date += delta
            elif y != 2:
                write(' '*view.columnWidth)
            current = view.gridColourB if current == view.gridColourA else view.gridColourA
            setBg(current)
    reset()

def drawTask(view, i):
    task = view.project.tasks[i + view.firstTask] #
    y = i*2 + TASK_Y_OFFSET #
    if y >= view.height:
        return

    width = view.width - view.taskWidth

    # Draw title
    goto(0, y)

    taskText = ' ' + task.title
    if len(task.title) > view.taskWidth - 2:
        taskText = taskText[:view.taskWidth - 3] + '…'
    else:
        taskText += ' '*(view.taskWidth - len(task.title) - 1)
    if i + view.firstTask == view.currentTask: #
        setBg(CURRENT_TASK_BG_COLOUR)
        setFg(CURRENT_TASK_FG_COLOUR)
        taskText += ' '*width

    write(taskText)

    # Set colour
    if task.status == WAITING:
        blockColour = setBg(WAITING_COLOUR)
    elif task.status == ONGOING:
        blockColour = setBg(ONGOING_COLOUR)
    elif task.status == DONE:
        blockColour = setBg(DONE_COLOUR)
    elif task.status == CRITICAL:
        blockColour = setBg(CRITICAL_COLOUR)

    if view.selectingDeps:
        if task in view.depsFor.deps:
            blockColour = setBg(colour.brightRed)

    # Get extra colour
    extraColour = ''
    if task.status == WAITING:
        extraColour = getBg(WAITING_EXTRA_COLOUR)
    elif task.status == ONGOING:
        extraColour = getBg(ONGOING_EXTRA_COLOUR)
    elif task.status == DONE:
        extraColour = getBg(DONE_EXTRA_COLOUR)

    # Draw block
    blockUnit = 7 if view.view == DAY else 1

    block = ' '*task.length*blockUnit + '$'*task.extra*blockUnit

    start = task.start*blockUnit - view.firstDateOffset*blockUnit
    if start < 0:
        block = block[-start:]
        start = 0
    if start < width:
        if len(block) + start > width:
            block = block[:width - start]

        block = block.replace('$', extraColour + ' ', 1).replace('$', ' ')

        goto(view.taskWidth + start, y)
        write(block)

    reset()

def drawTasks(view):
    for i in range(len(view.project.tasks) - view.firstTask):
        drawTask(view, i)

#╭╮╰╯─│→├▐█▌┤
