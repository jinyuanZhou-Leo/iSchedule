#!/usr/bin/env python3
# coding=utf-8
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from tqdm import tqdm, trange

from data import Location, Term, Course, Holiday, generateICS
from utils import *

VERSION = "3.2.5"
# CLI Arguments Def
cliArgumentParser = argparse.ArgumentParser(description="iSchedule")
cliArgumentParser.add_argument("-v", "--version", action="store_true", help="显示版本")
cliArgumentParser.add_argument("-nl", "--nolog", action="store_true", help="不显示警告与提示信息")
cliArgumentParser.add_argument("-c", "--config", type=str, help="配置文件路径")
cliArgumentParser.add_argument("-s", "--schedule", type=str, help="JSON时间配置文件路径")
cliArgumentParser.add_argument("-o", "--output", type=str, help="输出目录")
cliArgs = cliArgumentParser.parse_args()
if cliArgs.version:  # show version information and exit
    print(f"iSchedule {VERSION}")
    exit(0)

config: dict = {}
cliConfig: dict[str, Any] = {
    "logLevel": "ERROR" if cliArgs.nolog else "INFO",
    "configPath": (Path(cliArgs.config) if cliArgs.config else Path.cwd() / "config.json").resolve(),
    "schedulePath": (Path(cliArgs.schedule) if cliArgs.schedule else Path.cwd() / "schedule.json").resolve(),
    "outputPath": (Path(cliArgs.output) if cliArgs.output else Path.cwd()).resolve(),
}
config.update(cliConfig)

# initialize logger
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), level=config["logLevel"], colorize=True)
logger.info(f"iSchedule {VERSION}")

config.update(loadJSON(config["configPath"]))
if not os.path.exists(config["schedulePath"]):
    # fall back when default path is not exists.
    logger.warning(f"{config["schedulePath"]} does not exist")
    config["schedulePath"] = Path(input("ENTER the schedule file path: ").strip("\"'")).resolve()
schedule: dict[dict] = loadJSON(config["schedulePath"])

# parse schedule file into objects
terms: list[Term] = []
for termName, termData in schedule.items():
    tmp: Term = Term(
        name=termName,
        start=datetime(*termData["start"]),
        end=datetime(*termData["end"]),
        duration=termData["duration"],
        timetable=termData["timetable"],
        cycle=termData["cycle"],
    )
    terms.append(tmp)
    for courseName, courseData in termData["courses"].items():
        # Term.addCourse() will automatically set the cycle to the course's cycle if it is provided
        courseCycle: int | None = None
        courseLocation: str | Location | None
        if courseData.get("cycle") is not None:
            logger.warning(
                f'Exceptional cycle "{courseData["cycle"]}" is provided in "{termName}.{courseName}" and this will OVERRIDE the default cycle. If you see this warning UNKNOWINGLY, please remove the "cycle" field under "{termName}.courses.{courseName}"'
            )

            courseCycle = int(courseData["cycle"])
        if courseData.get("location"):
            if isinstance(courseData["location"], tuple) or isinstance(courseData["location"], list):
                courseLocation = Location(*courseData["location"])
            elif isinstance(courseData["location"], str):
                courseLocation = Location(name=courseData["location"])
            else:
                logger.warning(f"Invalid 'location' is provided in \"{termName}.{courseName}\"")
                courseLocation = None

        tmp.addCourse(
            Course(
                name=courseName,
                teacher=courseData["teacher"],
                location=courseLocation,
                index=courseData["index"],
                cycle=courseCycle,
            )
        )

    if termData.get("holidays") is not None:
        for holidayName, holidayData in termData["holidays"].items():
            tmp.addHoliday(
                Holiday(
                    name=holidayName,
                    type=holidayData["type"],
                    date=[datetime(*x) for x in holidayData["date"]],
                    compensations=(
                        [[datetime(*x[0]), x[1]] for x in holidayData["compensation"]]
                        if holidayData.get("compensation")
                        else None
                    ),
                )
            )

print("\n")

# parse userConfig file
config["name"] = config["name"] if config["name"] != "" else f"Schedule-{datetime.now().strftime('%X-%Y.%m.%d')}"

for i in trange(len(terms), desc="Total: "):
    try:
        ics = generateICS(terms[i], config)
        config["outputPath"] = (config["outputPath"] / f"{config['name']} - {terms[i].name}.ics").resolve()
        with open(config["outputPath"], "wb") as f:
            f.write(ics)
    except Exception as e:
        logger.error(f"[{i + 1} of {len(terms)}] Failed to generate ICS file - {config["name"]} - {terms[i].name}.ics")
    else:
        logger.success(
            f"[{i + 1} of {len(terms)}] Successfully generated ICS file - {config["name"]} - {terms[i].name}.ics"
        )

print("\n")
logger.info("To import the ICS file, drag the generated ICS file into your calendar app")
