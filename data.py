import itertools
import logging
import uuid
import icalendar as ic
from datetime import datetime, time, timedelta
from utils import *


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter("%(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(level=logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Term:
    name: str = "Term"
    uuid: str = ""
    start: datetime = None
    end: datetime = None
    classDuration: int = 0
    classStartingTime: list[list[int, int]] = []
    cycle: int = -1
    courses: list["Course"] = []

    def __init__(
        self,
        name: str,
        start: datetime,
        end: datetime,
        classDuration: int,
        classStartingTime: list[list[int]],
        cycle: int,
    ) -> None:
        self.name = name
        self.start, self.end = start, end
        self.classDuration = classDuration
        self.classStartingTime = classStartingTime

        if cycle <= 0:
            logger.critical(
                f'Invalid cycle number for "{self.name}", cycle number should be positive integer'
            )
            exit(0)
        else:
            self.cycle = cycle

        self.courses = []
        self.uuid = str(uuid.uuid4())

    def add_course(self, course: "Course") -> None:
        course.setCycle(self.cycle)
        # 将课程对象添加到学生的课程列表中
        self.courses.append(course)

    def __str__(self) -> str:
        return f"Term - {self.uuid}:\n   Start: {self.start}\n   End: {self.end}\n   Class Duration: {self.classDuration} minutes\n   Class Starting Time: {self.classStartingTime}\n   Cycle: {self.cycle}"


class Course:
    name: str = None
    teacher: str = None
    room: str = None
    timetable: list[list[any]] = []
    cycle: int = -1

    def __init__(
        self, name: str, teacher: str, room: str, timetable: list[list[any]], cycle: int
    ) -> None:
        self.name = name
        self.teacher = teacher
        self.room = room
        self.timetable = timetable
        self.cycle = cycle

    def setCycle(self, cycle: int) -> None:
        if self.cycle == -1:
            self.cycle = cycle

    def getCycleDay(self) -> int:
        return self.cycle * 5

    def getDecodeTimetable(self, term: Term) -> list[list[int]]:
        def decode_component(component, maximum):
            abbrDict = {
                "odd": [i for i in range(1, maximum + 1, 2)],
                "even": [i for i in range(2, maximum + 1, 2)],
                "everyday": [i for i in range(1, maximum + 1)],
            }
            if isinstance(component, int):
                if component > self.getCycleDay() or component < 1:
                    logger.critical(
                        f"Invalid schedule file, Error processing {term}.{self.name}.time, {component} is out of range"
                    )
                    exit(0)
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
                            f"Invalid schedule file, Error processing {term}.{self.name}.time, {item} can not be indentified"
                        )
                        exit(0)
                return tmp
            else:
                logger.critical(
                    f"Invalid schedule file, Error processing {term}.{self.name}.time, {component} can not be indentified"
                )
                exit(0)

        def mergeFirstItem(cartesian_product):
            # 创建一个字典来存储合并后的结果
            merged_result = {}

            # 遍历笛卡尔积中的每个元素
            for item in cartesian_product:
                key, value = item
                if value in merged_result:
                    # 如果第二项已存在，则合并第一项
                    merged_result[value].append(key)
                else:
                    # 如果第二项不存在，则创建新的键值对
                    merged_result[value] = [key]

            # 对每个列表中的第一项进行排序，并将结果转换为原始格式
            result = [[sorted(keys), value] for value, keys in merged_result.items()]

            return result

        decodedTimetable = []
        for timestamp in self.timetable:  # [1,2], ["odd",3]
            # 求decodeTimestamp笛卡尔积
            decodedTimetable.extend(
                [
                    list(t)
                    for t in itertools.product(
                        [x for x in decode_component(timestamp[0], self.cycle * 5)],
                        [
                            x - 1
                            for x in decode_component(
                                timestamp[1], len(term.classStartingTime)
                            )
                        ],
                    )
                ]
            )
        return mergeFirstItem(decodedTimetable)

    def eventify(self, term: Term, date: datetime, block: int) -> ic.Event:
        event: ic.Event = ic.Event()
        event.add("summary", self.name)
        event.add("description", f"{self.teacher}\n{self.room}")
        event.add(
            "dtstart",
            datetime.combine(
                date,
                time(
                    term.classStartingTime[block][0],
                    term.classStartingTime[block][1],
                ),
            ),
        )
        event.add(
            "dtend",
            datetime.combine(
                date,
                time(
                    term.classStartingTime[block][0],
                    term.classStartingTime[block][1],
                ),
            )
            + timedelta(minutes=term.classDuration),
        )
        event.add("dtstamp", datetime.now())
        event.add("uid", uuid.uuid4())

        return event


def workdayRange(start: datetime, end: datetime):
    for n in range(int((end - start).days) + 1):
        day = start + timedelta(days=n)
        if day.weekday() < 5:
            yield day


def workday2day(workday: int) -> int:
    fullWeek = workday // 5 if workday % 5 != 0 else workday // 5 - 1
    remain = workday - fullWeek * 5
    return fullWeek * 7 + remain


def getWeekInfo(day: int) -> list[int, int]:
    fullWeek = day // 5 if day % 5 != 0 else day // 5 - 1
    remain = day - fullWeek * 5
    return [remain, fullWeek]


def day2str(remain: int) -> str:
    map: dict = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR"}
    return map[remain]


def generateICS(term: Term, config: dict, mode: str = "rrule") -> bytes:
    mode = mode.lower()
    ics: ic.Calendar = ic.Calendar()
    ics.add("VERSION", "2.0")
    ics.add("PRODID", "iScheduler by @Jinyuan")
    ics.add("CALSCALE", "GREGORIAN")
    ics.add("X-APPLE-CALENDAR-COLOR", parseHexColor(config["color"]))
    ics.add("X-WR-CALNAME", f"{config['name']} - {term.name}")
    ics.add("X-WR-TIMEZONE", "Asia/Shanghai")  # TODO: add time zone support

    if mode == "rrule":

        cnt = term.start.weekday() + 1
        if cnt > 5:
            cnt = 5

        initDay: datetime = term.start - timedelta(days=term.start.weekday())
        for course in term.courses:
            timetable = course.getDecodeTimetable(term)
            # print(timetable)
            for timestamp in timetable:
                for day in timestamp[0]:
                    weekInfo: list[int, int] = getWeekInfo(day)
                    event: ic.Event = course.eventify(
                        term,
                        initDay + timedelta(weeks=weekInfo[1], days=weekInfo[0] - 1),
                        timestamp[1],
                    )
                    if config["alarm"]["enabled"] == True:
                        reminder: ic.Alarm = ic.Alarm()
                        reminder.add("ACTION", "DISPLAY")
                        reminder.add("DESCRIPTION", "提醒事项")
                        reminder.add(
                            "TRIGGER",
                            timedelta(
                                hours=-config["alarm"]["before"][0],
                                minutes=-config["alarm"]["before"][1],
                            ),
                        )
                        event.add_component(reminder)
                    rrule = ic.vRecur(
                        freq="weekly",
                        interval=course.cycle,
                        byday=day2str(weekInfo[0]),
                        until=term.end,
                    )
                    event.add("RRULE", rrule)
                    ics.add_component(event)

    return ics.to_ical()
