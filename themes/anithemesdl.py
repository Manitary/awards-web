import argparse
import csv
import json
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Literal, TypedDict

import requests


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


class Entry(TypedDict):
    id: int
    created_at: str
    updated_at: str
    deleted_at: str | None


Resource = TypedDict(
    "Resource",
    {
        "id": int,
        "link": str | None,
        "external_id": int | None,
        "site": str | None,
        "as": str | None,
        "created_at": str,
        "updated_at": str,
        "deleted_at": str | None,
    },
)


class Song(Entry):
    title: str


class Video(Entry):
    basename: str
    filename: str
    path: str
    size: int
    mimetype: str
    resolution: int | None
    nc: bool
    subbed: bool
    lyrics: bool
    uncen: bool
    source: Literal["WEB", "RAW", "BD", "DVD", "VHS", "LD"] | None
    overlap: Literal["None", "Transition", "Over"]
    tags: str
    link: str


class AnimeThemeEntry(Entry):
    version: int | None
    episodes: str | None
    nsfw: bool
    spoiler: bool
    notes: str | None
    videos: list[Video]


class AnimeTheme(Entry):
    type: Literal["OP", "ED"] | None
    sequence: int | None
    group: str | None
    slug: str
    song: Song | None
    animethemeentries: list[AnimeThemeEntry]


class Anime(Entry):
    name: str
    slug: str
    year: int | None
    season: Literal["Winter", "Spring", "Summer", "Fall"] | None
    synopsis: str | None
    animethemes: list[AnimeTheme]
    resources: list[Resource]


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
