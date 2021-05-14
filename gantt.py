WAITING = 0
ONGOING = 1
DONE    = 2
REMOVED = 3

class Project:
    def __init__(self, name):
        self.tasks = []

    def addTask(self, title,
                length = 1,
                earliestStart = 0,
                status = WAITING):
        self.tasks.append(Task(title, self, length, earliestStart, status))

class Task:
    def __init__(self, title, project,
                 length = 1,
                 earliestStart = 0,
                 status = WAITING):

        # Basic attributes
        self.title = title
        self.status = status
        self.length = length
        self.extra = 2
        self.earliestStart = earliestStart

        self.deps = []
        self.project = project

    @property
    def totalLength(self):
        return self.length + self.extra

    @property
    def start(self):
        return self.earliestStart

def requiredBy(required):
    dependents = []
    for task in required.project.tasks:
        if required in task.deps:
            dependents.append(task)
    return dependents
