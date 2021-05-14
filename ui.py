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

GRID_COLOUR_A = colour.black
GRID_COLOUR_B = colour.default

WAITING_COLOUR = colour.brightWhite
ONGOING_COLOUR = colour.brightYellow
DONE_COLOUR = colour.brightGreen

WAITING_EXTRA_COLOUR = colour.brightBlack
ONGOING_EXTRA_COLOUR = colour.yellow
DONE_EXTRA_COLOUR = colour.green

TASK_WIDTH = 16

# Project view
class View:
    def __init__(self, project):
        self.project = project
        self.view = WEEK
        self.columnWidth = 7

        # Scrolling offsets
        self.firstDateOffset = 0
        self.firstTask = 0

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

    def updateSize(self):
        rows, columns = os.popen('stty size', 'r').read().split()
        self.height = int(rows)
        self.width = int(columns)

    def toggleView(self):
        self.view = DAY if self.view == WEEK else WEEK

# Writting and cursor
def write(text):
    sys.stdout.write(text)

def clear():
    write('\x1b[2J\x1b[1;1H')

def goto(x, y):
    write(f'\x1b[{y + 1};{x + 1}H')

# Formating
def getBg(bg):
    bg += 40
    return f'\x1b[{bg}m'

def getFg(fg):
    fg += 30
    return f'\x1b[{fg}m'

def setBg(bg):
    write(getBg(bg))

def setFg(fg):
    write(getFg(fg))

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
                write(date.strftime(' %d/%m '))
                date += delta
            else:
                write(' '*view.columnWidth)
            current = view.gridColourB if current == view.gridColourA else view.gridColourA
            setBg(current)
    reset()

def drawTasks(view):
    width = view.width - view.taskWidth
    for i in range(len(view.project.tasks) - view.firstTask):
        task = view.project.tasks[i + view.firstTask]
        y = i*2 + 3
        if y >= view.height:
            break
        goto(1, y)

        # Draw title
        if len(task.title) > view.taskWidth - 2:
            write(task.title[:view.taskWidth - 3])
            write('…')
        else:
            write(task.title)

        # Set colour
        if task.status == WAITING:
            setBg(WAITING_COLOUR)
        elif task.status == ONGOING:
            setBg(ONGOING_COLOUR)
        elif task.status == DONE:
            setBg(DONE_COLOUR)

        # Get extra colour
        if task.status == WAITING:
            extraColour = getBg(WAITING_EXTRA_COLOUR)
        elif task.status == ONGOING:
            extraColour = getBg(ONGOING_EXTRA_COLOUR)
        elif task.status == DONE:
            extraColour = getBg(DONE_EXTRA_COLOUR)

        # Draw block
        blockUnit = 1 if view.view == DAY else 7

        block = ' '*task.length*blockUnit + '$' + ' '*(task.extra*blockUnit - 1)

        start = task.start*blockUnit - view.firstDateOffset*blockUnit
        if start < 0:
            block = block[-start:]
            start = 0
        if start < width:
            if len(block) + start > width:
                block = block[:width - start]

            if '$' in block:
                block = block.replace('$', extraColour + ' ')

            goto(view.taskWidth + start, y)
            write(block)

        '''
        start = task.start - view.firstDateOffset
        goto(max(view.taskWidth + blockUnit*start, view.taskWidth), y)

        lengthFromStart = width + view.firstDateOffset*blockUnit - task.start*blockUnit
        lengthToEnd = task.start*blockUnit - view.firstDateOffset*blockUnit + task.totalLength*blockUnit

        length = min(width, task.length*blockUnit, lengthFromStart, lengthToEnd)
        extra = min(width, task.totalLength*blockUnit, lengthFromStart, lengthToEnd) - length

        write(' '*length)

        # Set colour
        if task.status == WAITING:
            setBg(WAITING_EXTRA_COLOUR)
        elif task.status == ONGOING:
            setBg(ONGOING_EXTRA_COLOUR)
        elif task.status == DONE:
            setBg(DONE_EXTRA_COLOUR)

        write(' '*extra)
        '''

        reset()

if __name__ == '__main__':
    clear()
    while True:
        rows, columns = os.popen('stty size', 'r').read().split()
        rows = int(rows)
        columns = int(columns)

        marginLeft = 0
        drawGrid(colour.cyan, colour.brightCyan, marginLeft, 0, columns - marginLeft, rows, 7)

#╭╮╰╯─│→├▐█▌┤
