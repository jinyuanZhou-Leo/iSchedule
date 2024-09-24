#!/usr/bin/env python3
# coding=utf-8

import os
import sys
from loguru import logger
from tqdm import tqdm, trange
from pathlib import Path
from datetime import datetime
from utils import *
from data import Term, Course, generateICS

VERSION = "2.0"

logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), format="{level}: <level>{message}</level>", level="INFO", colorize=True)
logger.info(f"iSchedule {VERSION}")

# read files
config: dict = loadJSON(Path.cwd() / "config.json")  # Program configuration
schedulePath: Path = Path.cwd() / "schedule.json"
if not os.path.exists(
    schedulePath
):  # schedule file with default file name is not found
    tmp: str = input("ENTER the schedule file path: ").strip()
    if (tmp.startswith("'") and tmp.endswith("'")) or (
        tmp.startswith('"') and tmp.endswith('"')
    ):
        tmp = tmp[1:-1]  # remove quotes
    schedulePath = Path(tmp)
schedule: dict = loadJSON(schedulePath)


# parse schedule file into objects
terms: list[Term] = []
for termName, termData in schedule.items():
    tmp: Term = Term(
        termName,
        datetime(*termData["start"]),
        datetime(*termData["end"]),
        termData["duration"],
        termData["timetable"],
        termData["cycle"],
    )
    terms.append(tmp)
    for courseName, courseData in termData["courses"].items():
        courseCycle: int = -1
        if courseData.get("cycle") is not None:
            courseCycle = int(courseData["cycle"])

        tmp.addCourse(
            Course(
                courseName,
                courseData["teacher"],
                courseData["location"],
                courseData["index"],
                courseCycle,
            )
        )

print("\n")

# parse config file
config["name"] = (
    config["name"]
    if config["name"] != ""
    else f"Schedule-{datetime.now().strftime('%X-%Y.%m.%d')}"
)


for i in trange(len(terms), desc="Total: "):
    ics = generateICS(terms[i], config)
    try:
        with open(f"{config['name']} - {terms[i].name}.ics", "wb") as f:
            f.write(ics)
    except Exception as e:
        logger.error(
            f"[{i+1} of {len(terms)}] Failed to generate ICS file - {config["name"]} - {terms[i].name}.ics"
        )
        if isinstance(e,IOError):
            logger.critical(f"{e}: Permission denied, Try re-run the program by using 'sudo'.")
        else:
            logger.critical(f"Unknown error occurred while creating file.")
        exit(0)
    else:
        logger.success(
            f"[{i+1} of {len(terms)}] Successfully generated ICS file - {config["name"]} - {terms[i].name}.ics"
        )

print("\n")
logger.info("To import the ICS file, drag the generated ICS file into your calendar app")
