#!/usr/bin/env python3
# coding=utf-8

import os
import json
from powerschool import PowerSchool
from utils import *
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm, trange


logger.remove()
logger.add(
    lambda msg: tqdm.write(msg, end=""),
    level="DEBUG",
    colorize=True,
)
logger.add("powerschool_connector.log", level="TRACE", rotation="10MB")
# TODO:retention=
load_dotenv()
psUsernameCache: str | None = os.getenv("PS_USERNAME")
psPasswordCache: str | None = os.getenv("PS_PASSWORD")


def requestUserInformation(disableCache=False) -> list:
    if psUsernameCache and psPasswordCache and not disableCache:
        logger.debug("Using cached user information")
        return [psUsernameCache, psPasswordCache]
    else:
        if disableCache:
            logger.debug("User information cache is disabled")
        else:
            logger.warning("Cached user information is invalid, please enter again")
        newUsername: str = input("Enter your Powerschool Username: ").strip()
        newPassword: str = input("Enter your Powerschool Password: ").strip()
        setEnvVar("PS_USERNAME", newUsername)
        setEnvVar("PS_PASSWORD", newPassword)
        logger.info("User information is Cached")
        return [newUsername, newPassword]


logger.debug("PS Connector starting...")
MAX_ATTEMPTS = 3
powerschool: PowerSchool
for attempt in range(MAX_ATTEMPTS):
    if attempt > 0:
        # if it is not the first attempt, then notify the user
        logger.warning(
            f"Login Failed (Attempt:[{attempt+1}/{MAX_ATTEMPTS}]), retrying..."
        )
        disableCache = True  # disable cache since cache is obviously wrong
    else:
        disableCache = False

    try:
        powerschool = PowerSchool(*requestUserInformation(disableCache))
    except Exception as e:
        logger.error(f"Failed to login to Powerschool: {e}")
        if attempt == MAX_ATTEMPTS - 1:
            setEnvVar("PS_USERNAME", "")  # clear the cache .env file
            setEnvVar("PS_PASSWORD", "")
            logger.error("Maximum login attempts, cleaning the cache and exit")
            exit(2)
    else:
        logger.success("Login to Powerschool successfully")
        break

scheduleJson = powerschool.getSchedule()
with open(Path.cwd() / "schedule.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(scheduleJson, ensure_ascii=False))

logger.success(
    'Schedule is generated successfully, please check the "schedule.json" in current directory'
)
