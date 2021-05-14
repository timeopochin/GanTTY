DONE = 0
ONGOING = 1
WAITING = 2
CRITICAL = 3
#REMOVED = 4

class Project:
    def __init__(self, name):
        self.tasks = []

    def addTask(self, title,
                length = 1,
                earliestStart = 0,
                isDone = False):
        self.tasks.append(Task(title, self, length, earliestStart, isDone))

    @property
    def end(self):
        return max(task.end for task in self.tasks)

class Task:
    def __init__(self, title, project,
                 length = 1,
                 earliestStart = 0,
                 isDone = False):

        # Basic attributes
        self.title = title
        self.isDone = isDone
        self.length = length
        self.earliestStart = earliestStart

        self.deps = []
        self.project = project

    @property
    def status(self):
        if self.isDone:
            return DONE
        for dep in self.deps:
            if not dep.isDone:
                return WAITING
        return ONGOING if self.extra else CRITICAL

    @property
    def extra(self):
        dependents = getDependents(self)
        if len(dependents):
            extra = -1
            for dependent in dependents:
                if dependent.start - self.end < extra or extra == -1:
                    extra = dependent.start - self.end
        else:
            extra = self.project.end - self.end
        return extra

    @property
    def totalLength(self):
        return self.length + self.extra

    @property
    def end(self):
        return self.start + self.length

    @property
    def start(self):
        start = self.earliestStart
        for dep in self.deps:
            if start < dep.end:
                start = dep.end
        return start

    def hasDep(self, task):
        for dep in self.deps:
            if dep == task or dep.hasDep(task):
                return True
        return False

    def setDep(self, index):
        newDep = self.project.tasks[index]
        if newDep == self or newDep.hasDep(self) or self.hasDep(newDep):
            return False
        self.deps.append(newDep)
        return True

    def removeDep(self, index):
        dep = self.project.tasks[index]
        if dep in self.deps:
            del self.deps[self.deps.index(dep)]

def getDependents(required):
    dependents = []
    for task in required.project.tasks:
        if required in task.deps:
            dependents.append(task)
    return dependents
