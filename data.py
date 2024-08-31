from datetime import datetime


class Course:
    name = ""
    teacher = ""
    time = []
    room = ""

    def __init__(self, name, teacher, time, room):
        self.name = name
        self.teacher = teacher

        for i in range(len(time)):
            time[i][0] -= 1  # 1-7 -> 0-6
            time[i][1] -= 1
        self.time = time

        self.room = room

    def isOn(self, day):
        for i in range(len(self.time)):
            if self.time[i][0] == day:
                return True
        return False

    def getBlock(self, day):
        for i in range(len(self.time)):
            if self.time[i][0] == day:
                return self.time[i][1]
        return -1  # if there is no class on that day

    def __str__(self):
        return f"{self.name}\n   Teacher: {self.teacher}\n   Time: {self.time}\n   Room: {self.room}"


class Term:
    start = datetime.now()
    end = datetime.now()
    classDuration = 0
    classInfo = []

    def __init__(self, start, end, classDuration, classInfo):
        self.start = datetime(start[0], start[1], start[2])
        self.end = datetime(end[0], end[1], end[2])
        self.classDuration = int(classDuration)
        self.classInfo = classInfo

    def __str__(self):
        return f"Start:{self.start}\nEnd:{self.end}\nClassDuration:{self.classDuration}mins\nClassInfo:{self.classInfo}"
