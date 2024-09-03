import logging
from datetime import datetime


# initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter("%(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()  # for logging in CLI
stream_handler.setLevel(level=logging.INFO)  # log level
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def roundUpToNearestXMultiples(n: int, x: int):
    if n % x == 0:
        return n
    else:
        return n + (x - n % x)


class Term:
    name = ""
    start = datetime.now()
    end = datetime.now()
    classDuration = 0
    classStartingTime = []
    cycle = -1
    courses = []

    def __init__(
        self, name: str, start, end, classDuration: int, classStartingTime, cycle: int
    ):
        self.name = name
        self.start = datetime(start[0], start[1], start[2])
        self.end = datetime(end[0], end[1], end[2])
        self.classDuration = int(classDuration)
        self.classStartingTime = classStartingTime

        if type(cycle) != int or cycle <= 0:
            logger.critical(
                f'Invalid cycle number for "{self.name}", please explicitly give a cycle number in schedule json file'
            )
            exit(0)
        else:
            self.cycle = 5 * cycle

        #!!! 不在构造器方法内初始化的类参数会被该类所有实例共享
        self.courses = []

    def __str__(self):
        return f"{self.name}:\n   Start:{self.start}\n   End:{self.end}\n   ClassDuration:{self.classDuration}mins\n   classStartingTime:{self.classStartingTime}"

    def addCourse(self, course):
        self.courses.append(course)
        course.attachTo(self)  # mutally bonding 双向绑定
        course.decode()


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
                    logger.error(
                        f"Invalid course timestamp in schedule file. Please check its format"
                    )
                    logger.error(
                        "Hint: The first parameter of single timestamp can only be 'odd', 'even' or 'everyday'."
                    )
                    pass

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

        # print(f"name:{self.name} - decoded:{self.decodedTimetable}")

    def decodeBlock(self, item):  #!Turn to private?
        if isinstance(item[1], list):
            tmp = []
            for i in range(len(item[1])):
                tmp.append([item[0], item[1][i]])
            return tmp
        elif isinstance(item[1], int):
            return [item]  # if item is a day number
        else:
            logger.error(
                f"Invalid course timestamp in schedule file. Please check its format"
            )
            return False

    def isOn(self, day: int):
        for i in range(len(self.decodedTimetable)):
            if self.decodedTimetable[i][0] == day:
                return True
        return False

    def getBlock(self, day: int):
        blockList = []
        for i in range(len(self.decodedTimetable)):
            if self.decodedTimetable[i][0] == day:
                blockList.append(self.decodedTimetable[i][1])

        if blockList:
            return blockList
        else:
            return False  # if there is no class on that day

    def attachTo(self, term: Term):
        if term.__class__.__name__ == "Term":
            self.term = term
            return (
                True  # if the course is successfully attached to the term, return True
            )
        else:
            logger.error(
                "Invalid parameter: only Term instances can be attached to Course"
            )
            return False

    def __str__(self):
        return f"{self.name}\n   Teacher: {self.teacher}\n   Time: {self.timetable}\n   Room: {self.room}"
