#!/usr/bin/env python3
# coding=utf-8

import itertools
import uuid
import icalendar as ic
from loguru import logger
from datetime import datetime, time, timedelta
from utils import *


class Location:
    name: str
    latitude: float | str
    longitude: float | str

    def __init__(self, name, latitude, longitute) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitute

    def __str__(self) -> str:
        return f"[{self.name}]: ({self.latitude}, {self.longitude})"


class Term:
    name: str
    uuid: str
    start: datetime
    end: datetime
    duration: int
    timetable: list[list[int, int]]
    cycle: int
    courses: list["Course"]

    def __init__(
        self,
        name: str,
        start: datetime,
        end: datetime,
        duration: int,
        timetable: list[list[int]],
        cycle: int,
    ) -> None:
        self.name = name
        self.start, self.end = start, end
        self.duration = duration
        self.timetable = timetable

        if cycle <= 0:
            logger.critical(
                f'Invalid cycle number for "{self.name}", cycle number should be positive integer'
            )
            exit(0)
        else:
            self.cycle = cycle

        self.courses = []
        self.uuid = str(uuid.uuid4())

    def addCourse(self, course: "Course") -> None:
        course.setCycle(self.cycle)  # set the cycle number of the course instance
        self.courses.append(course)  # add course instance into the term instance

    def __str__(self) -> str:
        return f"Term - {self.uuid}:\n   Start: {self.start}\n   End: {self.end}\n   Class Duration: {self.duration} minutes\n   Timetable: {self.timetable}\n   Cycle: {self.cycle}"


class Course:
    name: str
    teacher: str
    location: str | Location
    index: list[list[any]]
    cycle: int

    def __init__(
        self,
        name: str,
        teacher: str,
        location: str | Location,
        index: list[list[any]],
        cycle: int,
    ) -> None:
        self.name = name
        self.teacher = teacher
        self.location = location
        self.index = index
        self.cycle = cycle

    def setCycle(self, cycle: int) -> None:
        if (
            self.cycle == -1
        ):  # set the cycle number according to the term instance only if the cycle number of course is not defined
            self.cycle = cycle

    def getCycleDay(self) -> int:
        return self.cycle * 5

    def getDecodedIndex(self, term: Term) -> list[list[int]]:

        def decode_component(component: list | str | int, maximum: int):
            """
            Decode a component of a schedule.

            This function decodes a given component into a list of corresponding numbers based on the predefined dictionary.
            The component can be an integer, a string abbreviation, or a list containing integers and string abbreviations.

            Parameters:
            - component: The component to be decoded, can be an integer, a string, or a list.
            - maximum: The maximum value that the component can represent.

            Returns:
            - Returns a list of decoded numbers corresponding to the input component.
            """
            # Define a dictionary for different types of abbreviations, mapping to the corresponding number list
            abbrDict = {
                "odd": [i for i in range(1, maximum + 1, 2)],  # List of odd days
                "even": [i for i in range(2, maximum + 1, 2)],  # List of even days
                "everyday": [i for i in range(1, maximum + 1)],  # List of all days
            }

            # If the component is an integer, check if it is within the valid range
            if isinstance(component, int):
                if component > self.getCycleDay() or component < 1:
                    logger.critical(
                        f"Invalid schedule file, Error processing {term}.{self.name}.time, {component} is out of range"
                    )
                    exit(0)
                return [component]

            # If the component is a string abbreviation, convert it to the corresponding number list
            elif isinstance(component, str):
                return abbrDict[component.lower()]

            # If the component is a list, process each item in the list
            elif isinstance(component, list):
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

            # If the component is of an unsupported type, output an error message and exit
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

        product = []
        for timestamp in self.index:  # [1,2], ["odd",3]
            # 求decodeTimestamp笛卡尔积
            product.extend(
                [
                    list(t)
                    for t in itertools.product(
                        [x for x in decode_component(timestamp[0], self.cycle * 5)],
                        [
                            x - 1
                            for x in decode_component(timestamp[1], len(term.timetable))
                        ],
                    )
                ]
            )
        return mergeFirstItem(product)

    def eventify(self, term: Term, date: datetime, block: int) -> ic.Event:
        event: ic.Event = ic.Event()
        event.add("summary", self.name)
        event.add("description", f"{self.teacher}\n{self.location}")
        event.add(
            "dtstart",
            datetime.combine(
                date,
                time(
                    term.timetable[block][0],
                    term.timetable[block][1],
                ),
            ),
        )
        event.add(
            "dtend",
            datetime.combine(
                date,
                time(
                    term.timetable[block][0],
                    term.timetable[block][1],
                ),
            )
            + timedelta(minutes=term.duration),
        )
        event.add("dtstamp", datetime.now())
        event.add("uid", uuid.uuid4())

        return event


def getWeekInfo(day: int) -> list[int, int]:
    fullWeek = day // 5 if day % 5 != 0 else day // 5 - 1
    remain = day - fullWeek * 5
    return [remain, fullWeek]


def day2str(remain: int) -> str:
    map: dict = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR"}
    return map[remain]


def generateICS(term: Term, config: dict) -> bytes:
    ics: ic.Calendar = ic.Calendar()
    ics.add("VERSION", "2.0")
    ics.add("PRODID", "iScheduler by @Jinyuan")
    ics.add("CALSCALE", "GREGORIAN")
    ics.add("X-APPLE-CALENDAR-COLOR", parseHexColor(config["color"]))
    ics.add("X-WR-CALNAME", f"{config['name']} - {term.name}")
    ics.add("X-WR-TIMEZONE", "Asia/Shanghai")  # TODO: add time zone support

    initDay: datetime = term.start - timedelta(days=term.start.weekday())
    for course in term.courses:
        timetable = course.getDecodedIndex(term)
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
                )  # TODO: work around, try to merge some rrule which are in the same week
                logger.debug(f"Adding {course.name} with rrule:{rrule}")
                event.add("RRULE", rrule)
                ics.add_component(event)

    return ics.to_ical()
