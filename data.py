import itertools
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
        course.attach_to(self)  # mutally bonding 双向绑定
        course.decode()
        return True


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

    def decode(self):
        print(f"timetable:{self.timetable}")

        def decode_component(component, maximum):
            abbrDict = {
                "odd": [i for i in range(1, maximum + 1, 2)],
                "even": [i for i in range(2, maximum + 1, 2)],
                "everyday": [i for i in range(1, maximum + 1)],
            }
            if isinstance(component, int):
                return [component]
            elif isinstance(component, str):
                return abbrDict[component.lower()]

            elif isinstance(component, list):  # [10,"odd"]
                tmp = []
                for item in component:
                    if isinstance(item, int):
                        tmp.append(item)
                    elif isinstance(item, str):
                        tmp.extend(abbrDict[item.lower()])
                    else:
                        logger.critical(
                            f"Invalid schedule file, Error processing {self.term}.{self.name}.time, {item} can not be indentified"
                        )
                        exit(0)
                return tmp
            else:
                logger.critical(
                    f"Invalid schedule file, Error processing {self.term}.{self.name}.time, {component} can not be indentified"
                )
                exit(0)

        for timestamp in self.timetable:  # [1,2], ["odd",3]
            # 求decodeTimestamp笛卡尔积
            self.decodedTimetable.extend(
                [
                    list(t)
                    for t in itertools.product(
                        [
                            x - 1
                            for x in decode_component(timestamp[0], self.term.cycle)
                        ],
                        [
                            x - 1
                            for x in decode_component(
                                timestamp[1], len(self.term.classStartingTime)
                            )
                        ],
                    )
                ]
            )

        print(f"decoded:{self.decodedTimetable}")

    def get_block(self, day: int):
        blockList = []
        for i in range(len(self.decodedTimetable)):
            if self.decodedTimetable[i][0] == day:
                blockList.append(self.decodedTimetable[i][1])

        if blockList:
            return blockList
        else:
            return False  # if there is no class on that day

    def attach_to(self, term: Term):
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
