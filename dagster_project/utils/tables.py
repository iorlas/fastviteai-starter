from enum import Enum


class BronzeTable(str, Enum):
    RAW_HTML = "raw_html"
    RAW_YOUTUBE = "raw_youtube"
    DISCUSSIONS = "discussions"


class SilverTable(str, Enum):
    SUMMARIES = "summaries"
