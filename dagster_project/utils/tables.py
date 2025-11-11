from enum import Enum


class BronzeTable(str, Enum):
    HTML = "html"
    YOUTUBE = "youtube"
    YOUTUBE_DOWNLOADS = "youtube_downloads"
    DISCUSSIONS = "discussions"


class SilverTable(str, Enum):
    SUMMARIES = "summaries"
