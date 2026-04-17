from datetime import datetime
import re
import json
import logging
import os

from utils.fileStreams import getFileJsonStream
from utils.utils import FileProgressLog


def filter_posts_by_keywords(file_path: str, keywords_input=[]):
    file_size = os.stat(file_path).st_size
    logging.info(f"File size: {file_size:,} bytes")
    created = None
    file_lines = 0
    matched_lines = 0
    bad_lines = 0
    file_bytes_processed = 0

    result = []
    search_keys = ["title", "selftext"]

    with open(file_path, "rb") as f:
        jsonStream = getFileJsonStream(file_path, f)
        if jsonStream is None:
            print(f"Skipping unknown file {file_path}")
            return None
        progressLog = FileProgressLog(file_path, f)
        for line in jsonStream:
            progressLog.onRow()
            try:
                # obj = json.loads(line)
                obj = line
                matched_keywords = []
                for keyword in keywords_input:
                    pattern = rf"\b{re.escape(keyword)}\b"
                    if keyword == "OLD":
                        if any(re.search(pattern, obj[key]) for key in search_keys):
                            matched_keywords.append(keyword)
                    else:
                        if any(re.search(pattern, obj[key].lower()) for key in search_keys):
                            # if any(keyword in obj[key].lower() for key in search_keys):
                            matched_keywords.append(keyword)
                if matched_keywords:
                    obj['extraction_keywords'] = matched_keywords
                    result.append(obj)
                    matched_lines += 1
                if not keywords_input:
                    result.append(obj)
                    matched_lines += 1

                created = datetime.fromtimestamp(int(obj['created_utc']))

            except (KeyError, json.JSONDecodeError) as err:
                bad_lines += 1
            file_lines += 1
            if file_lines % 50000 == 0:
                print(
                    f" | {created.strftime('%Y-%m-%d %H:%M:%S')} : {file_lines:,} : {matched_lines:,} : {bad_lines:,}")

        progressLog.logProgress("\n")

        logging.info(
            f"Complete : {file_lines:,} : {matched_lines:,} : {bad_lines:,} : {file_bytes_processed:,} : {(file_bytes_processed / file_size) * 100:.0f}%")
        return result