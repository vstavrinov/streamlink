#!/usr/bin/env python

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from os import getenv
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).parents[1].resolve()

MAPPING: Mapping[str, Sequence[str | int]] = {
    "ANDROID": ("android", "standard", "sample_user_agents", "chrome", 0),
    "CHROME": ("chrome", "windows", "sample_user_agents", "standard", 0),
    "CHROME_OS": ("chrome-os", "standard", "sample_user_agents", "x86_64", 0),
    "FIREFOX": ("firefox", "standard", "sample_user_agents", "windows", 0),
    "IE_11": ("internet-explorer", "internet-explorer-windows-10", "sample_user_agents", "standard", 0),
    "IPHONE": ("ios", "standard", "sample_user_agents", "safari", 0),
    "OPERA": ("opera", "standard", "sample_user_agents", "windows", 0),
    "SAFARI": ("safari", "macos", "sample_user_agents", "standard", 0),
}


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update user agents file",
    )
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        default=getenv("WHATISMYBROWSER_API_KEY"),
        help="The whatismybrowser.com API key\nDefault: env.WHATISMYBROWSER_API_KEY",
    )
    parser.add_argument(
        "--file",
        metavar="FILE",
        default=ROOT / "src" / "streamlink" / "session" / "http_useragents.py",
        type=Path,
        help="The user agents module file\nDefault: $GITROOT/src/streamlink/session/http_useragents.py",
    )

    return parser.parse_args()


def main(api_key: str, file: Path):
    if not api_key:
        raise ValueError("Missing API KEY")
    if not file.is_file():
        raise ValueError("Missing user agents file")

    contents = file.read_text(encoding="utf-8")

    try:
        response = requests.request(
            method="GET",
            url="https://api.whatismybrowser.com/api/v2/software_version_numbers/all",
            headers={"X-API-KEY": api_key},
        )
        if response.status_code != 200:
            response.raise_for_status()
        data: Any = response.json()
        result: dict = data and data.get("result") or {}
        if result.get("code") != "success":
            raise ValueError(result.get("message") or "Missing version_data in JSON response")
    except requests.exceptions.RequestException as err:
        raise ValueError("Error while querying API or parsing JSON response") from err

    version_data: dict = data.get("version_data") or {}
    user_agents = {}
    for browser, seq in MAPPING.items():
        obj: Any = version_data
        for item in seq:
            try:
                obj = obj[item]
            except LookupError as err:
                raise ValueError(f"Invalid key: {item} ({seq})") from err

        if not isinstance(obj, str):
            raise ValueError(f"Invalid result: {obj!r} ({seq})")

        user_agents[browser] = obj

    for browser, user_agent in user_agents.items():
        contents = re.sub(
            rf'(?:^|(?<=\n)){re.escape(browser)} = ".*?"\n',
            f'{browser} = "{user_agent}"\n',
            contents,
            count=1,
        )

    file.write_text(contents, encoding="utf-8")


if __name__ == "__main__":
    args = get_args()

    try:
        main(args.api_key, args.file)
    except KeyboardInterrupt:
        sys.exit(130)
