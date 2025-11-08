from enum import Enum


class BronzeTable(str, Enum):
    HTML = "html"
    YOUTUBE = "youtube"
    DISCUSSIONS = "discussions"


class SilverTable(str, Enum):
    SUMMARIES = "summaries"
