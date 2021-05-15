import os
import termios
import tty
import sys
import subprocess
import tempfile
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

GRID_FG = colour.brightWhite
GRID_COLOUR_A = colour.black
GRID_COLOUR_B = colour.default
TODAY_COLOUR = colour.cyan
TODAY_FG_COLOUR = colour.black

# Default colours
DEFAULT_COLOUR = colour.brightWhite

# Normal view colours
DONE_COLOUR = colour.brightGreen
ONGOING_COLOUR = colour.brightBlue
CRITICAL_COLOUR = colour.brightYellow

# Dependency view colours
DEPS_OF_COLOUR = colour.brightGreen

DIRECT_DEPENDENCY_COLOUR = colour.brightRed
DEPENDENCY_COLOUR = colour.brightYellow

DIRECT_DEPENDENT_COLOUR = colour.brightBlue
DEPENDENT_COLOUR = colour.brightCyan

# Other colours
PROMPT_BG_COLOUR = colour.brightWhite
PROMPT_FG_COLOUR = colour.black

INFO_BG_COLOUR = colour.yellow
INFO_FG_COLOUR = colour.black

DEFAULT_TASK_WIDTH = 32
TASK_Y_OFFSET = 4

# Project view
class View:
    def __init__(self, project):
        self.project = project
        self.view = DAY
        self.columnWidth = 7
        self.selectingDeps = False
        self.unsavedEdits = True

        # Scrolling offsets
        self.firstDateOffset = 0
        self.firstTask = 0

        # Cursor
        self.currentTask = 0
        self.inputtingTitle = False

        # Size
        self.updateSize()

        # Defaults
        self.taskWidth = DEFAULT_TASK_WIDTH

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
        self.unsavedEdits = True

    def shrinkCurrent(self):
        if self.current.length > 1:
            self.current.length -= 1
            self.unsavedEdits = True

    def growTaskTitle(self):
        self.taskWidth += 1

    def shrinkTaskTitle(self):
        if self.taskWidth > 0:
            self.taskWidth -= 1

    def toggleDoneCurrent(self):
        if self.current.isDone:
            self.current.setNotDone()
        else:
            self.current.setDone()
        self.unsavedEdits = True

    def selectDeps(self):
        if self.selectingDeps and self.current is self.depsFor:
            self.selectingDeps = False
            return
        self.selectingDeps = True
        self.depsFor = self.current

    def toggleDep(self):
        self.depsFor.toggleDep(self.current)
        self.unsavedEdits = True

    def addTask(self, fd, oldSettings):
        title = getInputText(self, 'Title: ', fd, oldSettings)
        if title:
            self.project.addTask(title)
            self.currentTask = len(self.project.tasks) - 1
            self.unsavedEdits = True

    def renameCurrent(self, fd, oldSettings):
        title = getInputText(self, 'New title: ', fd, oldSettings)
        if title:
            self.current.title = title
            self.unsavedEdits = True

    def deleteCurrent(self, fd, oldSettings):
        confirm = getInputText(self, 'About to delete a task! Are you sure you want to continue? ', fd, oldSettings)
        if confirm.lower() == 'yes':
            self.project.removeTask(self.current)
            self.currentTask -= 1

    def editCurrent(self):
        initialMsg = self.current.description
        if not initialMsg:
            initialMsg = f'== {self.current.title}'
        self.current.description = getEditorInput(initialMsg)
        self.unsavedEdits = True

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

def getTaskColour(view, task):
    if view.selectingDeps:
        if task is view.depsFor:
            return DEPS_OF_COLOUR
        if task in view.depsFor.deps:
            return DIRECT_DEPENDENCY_COLOUR
        if task in view.depsFor.dependents:
            return DIRECT_DEPENDENT_COLOUR
        if view.depsFor.hasDep(task):
            return DEPENDENCY_COLOUR
        if view.depsFor.hasDependent(task):
            return DEPENDENT_COLOUR
        return DEFAULT_COLOUR
    if task.status == DONE:
        return DONE_COLOUR
    if task.status == ONGOING:
        return ONGOING_COLOUR
    if task.status == CRITICAL:
        return CRITICAL_COLOUR
    return DEFAULT_COLOUR

# UI
def drawDate(view, date, isLast = False):
    day = '       '
    if view.view == DAY:
        day = date.strftime('%a')
        if not len(day) % 2:
            day += ' '
        while len(day) < 7:
            day = ' ' + day + ' '
    write(day)
    godown(1)
    goleft(6 if isLast else 7)
    write(date.strftime(' %d/%m '))
    goup(1)

def drawGrid(view):
    date = view.firstDate
    delta = datetime.timedelta(days = 1 if view.view == DAY else 7)
    setFg(GRID_FG)
    for y in range(view.height):
        goto(view.taskWidth, y)
        current = GRID_COLOUR_A
        setBg(current)
        columnCount = (view.width - view.taskWidth)//view.columnWidth
        for i in range(columnCount):
            if y == 1:
                drawDate(view, date, view.taskWidth + i*7 == view.width - 7)
                date += delta
            elif y != 2:
                write(' '*view.columnWidth)
            current = GRID_COLOUR_B if current == GRID_COLOUR_A else GRID_COLOUR_A
            setBg(current)

    # Draw today
    unitBlock = 7 if view.view == DAY else 1
    today = datetime.datetime.now()
    offset = today - datetime.datetime.combine(view.firstDate, datetime.datetime.min.time())
    now = offset.days*unitBlock + (offset.seconds*unitBlock)//(60*60*24)
    if offset.days >= 0 and now <= view.width - view.taskWidth:
        goto(view.taskWidth + now, TASK_Y_OFFSET)
        setBg(TODAY_COLOUR)
        for i in range(view.height - TASK_Y_OFFSET):
            write(' ')
            godown(1)
            goleft(1)

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

    # Draw block
    setFg(colour.black)
    setBg(getTaskColour(view, task))

    blockUnit = 7 if view.view == DAY else 1
    block = ' '*task.length*blockUnit + '▒'*task.extra*blockUnit
    start = task.start*blockUnit - view.firstDateOffset*blockUnit
    if start < 0:
        block = block[-start:]
        start = 0
    if start < width:
        if len(block) + start > width:
            block = block[:width - start]

        goto(view.taskWidth + start, y)
        write(block)

    reset()

def drawTasks(view):
    for i in range(len(view.project.tasks) - view.firstTask):
        drawTask(view, i)

def drawInfo(view, msg = ''):
    goto(0, 0)
    setBg(INFO_BG_COLOUR)
    setFg(INFO_FG_COLOUR)
    if msg:
        write(f' {msg} ')
    elif view.selectingDeps:
        write(f' Selecting dependencies for "{view.depsFor.title}" ')
    reset()

def getInputText(view, msg, fd, oldSettings):
    goto(0, 0)
    setBg(PROMPT_BG_COLOUR)
    setFg(PROMPT_FG_COLOUR)
    write(' '*view.width)
    goto(1, 0)
    write(f'{msg}\x1b[?25h')
    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
    text = input()
    reset()
    tty.setraw(sys.stdin)
    write('\x1b[?25l')
    return text

def getEditorInput(initialMsg):
    editor = os.environ.get('EDITOR', 'vim')
    with tempfile.NamedTemporaryFile('w+', suffix='.adoc') as tf:
        tf.write(initialMsg)
        tf.flush()
        subprocess.call([editor, tf.name])
        write('\x1b[?25l')
        tf.seek(0)
        return tf.read()

#╭╮╰╯─│→├▐█▌┤
