#!/usr/bin/env python3
# coding=utf-8

import json
import random
import re
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Generator, Any

from loguru import logger

__all__ = [
    "loadJSON",
    "getRandomHexColor",
    "isHexColor",
    "parseHexColor",
    "extractJSONFromMarkdown",
    "timer",
    "dateRange",
    "getWeekInfo",
    "day2str",
    "setEnvVar",
    "requestValue",
]


def getWeekInfo(day: int) -> list[int, int]:
    fullWeek = day // 5 if day % 5 != 0 else day // 5 - 1
    remain = day - fullWeek * 5
    return [remain, fullWeek]


def day2str(day: int) -> str:
    map: dict = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR"}
    if 1 <= day <= 5:
        return map[day]
    else:
        raise ValueError(f"Invalid day: {day}")


def dateRange(start: datetime, end: datetime) -> Generator[datetime, None, None]:
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{repr(func.__name__)} called, Time consumed {end_time - start_time:.6f}s")
        return result

    return wrapper


def loadJSON(path: Path) -> Any:
    """
    json.load() with proper error handling

    Args:
        path(Path): the file path to load

    Returns:
        any: the parsed JSON data in dict, or error
    """
    try:
        with path.open() as f:
            try:
                data = json.load(f)
                logger.success(f"{f.name} is successfully parsed")
                return data
            except json.JSONDecodeError as e:
                logger.critical(f"Invalid JSON format in {path}")
                raise e
    except FileNotFoundError as e:
        raise e
    except IOError as e:
        logger.critical(f"Permission denied, Try re-run the program by using 'sudo'.")
        raise e
    except Exception as e:
        logger.critical(f"Unexpected error occurred while parsing '{path}'")
        raise e


def getRandomHexColor() -> str:
    """
    Generate a random HEX color code.

    Returns:
        str: A string representing a random HEX color, formatted with a '#' symbol followed by six hexadecimal characters.
    """
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def isHexColor(str) -> bool:
    """
    Identify if a string is a HEX color

    This function checks if the input string represents a hexadecimal color code.
    Hexadecimal color code starts with a '#' and is followed by 6 characters (A-F, a-f, or 0-9).

    Parameters:
    str: The string to be checked

    Returns:
    bool: True if the string is a hexadecimal color code, False otherwise
    """
    if str.startswith("#") and len(str) == 7:
        return True
    return False


def parseHexColor(hexColor: str) -> str:
    """
    Parses a hexadecimal color code.

    This function determines whether to return a random color code, the input color code itself, or the color code with the alpha channel removed.

    Parameters:
    hexColor (str): The input hexadecimal color code, which may include an alpha channel.

    Returns:
    str: The parsed or randomly generated color code.

    Logic Summary:
    1. If the input is "random", return a randomly generated color code.
    2. If the input is a valid full color code, return the input color code.
    3. If the input color code includes an alpha channel, return the color code without the alpha channel.
    4. If the input does not match any of the above conditions, return a randomly generated color code.
    """
    # If the input is "random", return a random color code
    if hexColor.lower() == "random":
        return getRandomHexColor()
    # If the input is a valid color code, return it directly
    elif isHexColor(hexColor):
        return hexColor
    # If the input color code includes an alpha channel, return it without the alpha channel
    elif isHexColor(hexColor[:-2]):
        return hexColor[:-2]  # Remove the alpha channel
    # If the input does not match any of the above conditions, return a random color code
    else:
        tmp = getRandomHexColor()
        logger.error(f"Invalid color code: {hexColor}, using {tmp} instead.")
        return tmp


def extractJSONFromMarkdown(markdown_text):
    """
    Extract JSON content from Markdown text.

    This function uses a regular expression to match JSON code blocks in the Markdown text and extracts their content. It is suitable for processing JSON data embedded within Markdown formatted text.

    Parameters:
    - markdown_text (str): The Markdown formatted text containing JSON data.

    Returns:
    - str: The extracted JSON data as a string. Returns an empty string if no matching JSON code blocks are found.
    """
    pattern = re.compile(r"```json\n(.*?)```", re.DOTALL)
    matches = pattern.findall(markdown_text)
    return "".join(matches)


def setEnvVar(key: str, value: str) -> None:
    key = key.upper()
    path = (Path.cwd() / ".env").resolve()
    try:
        with open(path, "r") as f:
            env = f.readlines()
    except IOError as e:
        logger.critical(f"Permission denied, Try re-run the program by using 'sudo'")
        raise e
    except Exception as e:
        logger.critical(f"Unexpected error occurred while parsing '{f}'")
        raise e

    found = False
    updatedEnv = []
    for line in env:
        if line.startswith(key + "="):
            updatedEnv.append(f'{key}="{value}"\n')
            found = True
        else:
            updatedEnv.append(line)

    if not found:
        updatedEnv.append(f'{key}="{value}"\n')

    try:
        with open(path, "w") as f:
            f.writelines(updatedEnv)
    except IOError as e:
        logger.critical(f"Permission denied, Try re-run the program by using 'sudo'")
        raise e
    except Exception as e:
        logger.critical(f"Unexpected error occurred while parsing '{f}'")
        raise e


def requestValue(prompt: str, type_: type, defaultValue: any = None, unit: str = "") -> any:
    if unit:
        unit = " " + unit
    while True:
        try:
            inputValue = input(f"({defaultValue}{unit}) {prompt}: ").strip()
            if inputValue == "":
                if defaultValue:
                    return defaultValue
                else:
                    raise ValueError("Default value does't not exist")
            inputValue = type_(inputValue)
            return type_(inputValue)
        except (ValueError, TypeError) as e:
            logger.error(f'Invalid input, Required input of "{type_}", Message: {e}')
        except Exception as e:
            logger.error(f'Unexpected exception while requesting value with prompt "{prompt}"')
            raise e


if __name__ == "__main__":
    logger.warning("This module cannot run independently")
