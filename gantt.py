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
        if self.end == self.project.end:
            return CRITICAL
        for dependent in self.dependents:
            if not dependent.extra:
                return CRITICAL
        return ONGOING

    @property
    def extra(self):
        if len(self.dependents):
            extra = -1
            for dependent in self.dependents:
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

    @property
    def dependents(self):
        return [task for task in self.project.tasks if self in task.deps]

    def hasDependent(self, task):
        for dependent in self.dependents:
            if dependent == task or dependent.hasDependent(task):
                return True
        return False

    def hasDep(self, task):
        for dep in self.deps:
            if dep == task or dep.hasDep(task):
                return True
        return False

    def setDep(self, newDep):
        if newDep == self or newDep.hasDep(self) or self.hasDep(newDep):
            return False
        for dep in newDep.deps:
            if self.hasDep(dep):
                self.removeDep(dep)
        for dependent in self.dependents:
            if dependent.hasDep(newDep):
                dependent.removeDep(newDep)
        self.deps.append(newDep)
        return True

    def removeDep(self, oldDep):
        if oldDep in self.deps:
            del self.deps[self.deps.index(oldDep)]

    def toggleDep(self, toggle):
        if self.hasDep(toggle):
            self.removeDep(toggle)
        else:
            self.setDep(toggle)
