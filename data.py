from datetime import datetime


def roundUpToNearestXMultiples(n: int, x: int):
    if n % x == 0:
        return n
    else:
        return n + (x - n % x)


class Term:
    start = datetime.now()
    end = datetime.now()
    classDuration = 0
    classStartingTime = []
    cycle = 0
    courses = []

    def __init__(self, start, end, classDuration: int, classStartingTime, cycle=1):
        self.start = datetime(start[0], start[1], start[2])
        self.end = datetime(end[0], end[1], end[2])
        self.classDuration = int(classDuration)
        self.classStartingTime = classStartingTime
        self.cycle = 5 * cycle  # TODO:判断是否报错
        #!!! 不在构造器方法内初始化的类参数会被该类所有实例共享
        self.courses = []

    def __str__(self):
        return f"Start:{self.start}\nEnd:{self.end}\nClassDuration:{self.classDuration}mins\nclassStartingTime:{self.classStartingTime}"

    def addCourse(self, course):
        self.courses.append(course)
        course.attachTo(self)  # mutally bonding 双向绑定
        course.decode()

    def calculateCycle(self):
        maxDayNumber = 0
        for course in self.courses:
            tmp = 0
            for i in range(len(course.time)):
                if course.time[i][0] > tmp:
                    tmp = course.time[i][0]
            if tmp > maxDayNumber:
                maxDayNumber = tmp

        self.cycle = roundUpToNearestXMultiples(maxDayNumber, 5)
        return True

    def getCycle(self):
        return self.cycle


class Course:
    name = ""
    teacher = ""
    timetable = []
    decodedTimetable = []
    room = ""
    term = 0

    def __init__(self, name: str, teacher: str, time, room):
        self.name = name
        self.teacher = teacher
        self.room = room
        self.timetable = time
        #!!! 不在构造器方法内初始化的类参数会被该类所有实例共享
        self.decodedTimetable = []
        self.term = 0

    def decode(self):  #!Turn to private?
        for i in range(len(self.timetable)):
            if type(self.timetable[i][0]) == str:
                odd = False
                even = False
                if self.timetable[i][0].lower() == "everyday":
                    odd = True
                    even = True
                elif self.timetable[i][0].lower() == "odd":
                    odd = True
                elif self.timetable[i][0].lower() == "even":
                    even = True
                else:
                    pass  # TODO:报错

                for j in range(1, self.term.cycle + 1):  # 解码 everyday, odd, even
                    if j % 2 != 0:  # odd
                        if odd:
                            tmp = self.decodeBlock([j, self.timetable[i][1]])
                            for item in tmp:
                                self.decodedTimetable.append(item)
                    else:  # even
                        if even:
                            tmp = self.decodeBlock([j, self.timetable[i][1]])
                            for item in tmp:
                                self.decodedTimetable.append(item)

            else:
                tmp = self.decodeBlock(self.timetable[i])
                for item in tmp:
                    self.decodedTimetable.append(item)

        for i in range(len(self.decodedTimetable)):
            self.decodedTimetable[i][0] -= 1
            self.decodedTimetable[i][1] -= 1

    def decodeBlock(self, item):  #!Turn to private?
        if isinstance(item[1], list):
            tmp = []
            for i in range(len(item[1])):
                tmp.append([item[0], item[1][i]])
            return tmp
        elif isinstance(item[1], int):
            return [item]  # if item is a day number
        else:
            return False  # TODO:报错

    def isOn(self, day: int):
        for i in range(len(self.decodedTimetable)):
            if self.decodedTimetable[i][0] == day:
                return True
        return False

    def getBlock(self, day: int):
        for i in range(len(self.decodedTimetable)):
            if self.decodedTimetable[i][0] == day:
                return self.decodedTimetable[i][1]
        return -1  # if there is no class on that day

    def attachTo(self, term: Term):
        if term.__class__.__name__ == "Term":
            self.term = term
            return (
                True  # if the course is successfully attached to the term, return True
            )
        else:
            # TODO:报错:参数必须为Term类型
            return False

    def __str__(self):
        return f"{self.name}\n   Teacher: {self.teacher}\n   Time: {self.timetable}\n   Room: {self.room}"
