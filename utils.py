import json
import random
import re
from pathlib import Path
from loguru import logger

__all__ = [
    "loadJSON",
    "getRandomHexColor",
    "isHexColor",
    "parseHexColor",
    "extractJSONFromMarkdown",
]


def loadJSON(path: Path) -> any:
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
            except json.JSONDecodeError:
                logger.critical(f"Invalid JSON format in {path}")
            exit(0)
    except FileNotFoundError as e:
        logger.critical(e)
    except IOError as e:
        logger.critical(
            f"{e}\nPermission denied, Try re-run the program by using 'sudo'."
        )
    except Exception as e:
        logger.critical(f"Unknown error occurred while parsing '{path}'\n{e}")
    exit(0)


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
    从Markdown文本中提取JSON代码块。

    该函数通过正则表达式匹配Markdown文本中的JSON代码块，并将它们提取出来。
    Markdown中，JSON代码块通常被```json ```包围。

    参数:
    markdown_text (str): 包含JSON代码块的Markdown文本。

    返回:
    str: 所有提取出的JSON代码块内容的字符串，连接在一起。
    """
    pattern = re.compile(r"```json\n(.*?)```", re.DOTALL)
    matches = pattern.findall(markdown_text)
    return "".join(matches)
