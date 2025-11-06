from enum import Enum


class BronzeTable(str, Enum):
    RAW_HTML = "raw_html"
    RAW_YOUTUBE = "raw_youtube"
    DISCUSSIONS = "discussions"


class SilverTable(str, Enum):
    EXTRACTED_CONTENT = "extracted_content"
    SUMMARIES = "summaries"
    DISCUSSIONS = "discussions"
