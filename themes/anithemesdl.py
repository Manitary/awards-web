import argparse
import csv
import itertools
import json
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Literal

import requests

from .models import Anime


class Season(StrEnum):
    ALL = auto()
    WINTER = auto()
    SPRING = auto()
    SUMMER = auto()
    FALL = auto()


@dataclass
class Args:
    year: int
    season: Season
    output: Literal["csv", "json"]
    no_duplicates: bool


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "year",
        help="The year from which to get OPEDs. Run it multiple times for multiple years.",
    )
    parser.add_argument(
        "--season",
        "-s",
        help="The season from which to get OPEDs.",
        choices=Season,
        default=Season.ALL,
    )
    parser.add_argument(
        "--output",
        "-o",
        help="The output file.",
        choices=["csv", "json"],
        default="csv",
    )
    parser.add_argument(
        "--no-duplicates",
        "-d",
        help="Save the first version of each theme",
        action="store_true",
    )
    return parser


def fetch_themes(
    year: int, season: Season, site: str = "AniList", num_pages: int = 10
) -> list[Anime]:
    results: list[Anime] = []
    for page in range(1, num_pages + 1):
        params = {
            "filter[year]": year,
            "filter[season]": None if season == Season.ALL else season,
            "filter[site]": site,
            "include": "animethemes.animethemeentries.videos,animethemes.song,resources",
            "page[size]": 100,
            "page[number]": page,
        }
        r = requests.get("https://api.animethemes.moe/anime", params=params, timeout=60)
        result = r.json()["anime"]
        if not result:
            break
        results.extend(result)

    return results


def main() -> None:
    args = make_parser().parse_args(namespace=Args)
    results = fetch_themes(args.year, args.season)

    anime_list = [
        {
            "name": anime["name"],
            "songname": themes["song"].get("title") if themes["song"] else None,
            "anilist": anime["resources"][0]["external_id"],
            "type": str(themes["type"])
            + (str(themes["sequence"]) if themes["sequence"] is not None else ""),
            "link": videos["link"],
        }
        for anime in results
        for themes in anime["animethemes"]
        for entries in themes["animethemeentries"]
        for videos in entries["videos"]
        if "NCBD1080" not in videos["link"]
    ]

    if args.no_duplicates:
        anime_list = [
            next(x[1])
            for x in itertools.groupby(
                anime_list, key=lambda a: (a["anilist"], a["type"])
            )
        ]

    with open(
        f"animethemes_{args.year}_{args.season}.{args.output}",
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        if args.output == "csv":
            dict_writer = csv.DictWriter(output_file, anime_list[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(anime_list)
        elif args.output == "json":
            json.dump(anime_list, output_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
