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


class Song(TypedDict):
    id: int
    title: str
    created_at: str
    updated_at: str
    deleted_at: str | None


class Video(TypedDict):
    id: int
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
    created_at: str
    updated_at: str
    deleted_at: str | None


class AnimeThemeEntry(TypedDict):
    id: int
    version: int | None
    episodes: str | None
    nsfw: bool
    spoiler: bool
    notes: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None
    videos: list[Video]


class AnimeTheme(TypedDict):
    id: int
    type: Literal["OP", "ED"] | None
    sequence: int | None
    group: str | None
    slug: str
    created_at: str
    updated_at: str
    deleted_at: str | None
    song: Song | None
    animethemeentries: list[AnimeThemeEntry]


class Anime(TypedDict):
    id: int
    name: str
    slug: str
    year: int | None
    season: Literal["Winter", "Spring", "Summer", "Fall"] | None
    synopsis: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None
    animethemes: list[AnimeTheme]
    resources: list[Resource]


class TableEntry(TypedDict):
    name: str
    songname: str | None
    anilist: int | None
    type: str
    # season: Literal['Winter', 'Spring', 'Summer', 'Fall']
    # version: int
    # episodes: str
    link: str


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


def main():
    args = make_parser().parse_args(namespace=Args)
    results = fetch_themes(args.year, args.season)
    anime_list: list[TableEntry] = []
    for anime in results:
        name, season = anime["name"], anime["season"]
        anilist = anime["resources"][0]["external_id"]
        for themes in anime["animethemes"]:
            oped = themes["type"]
            sequence = themes["sequence"]
            song = themes["song"]
            song_name = song.get("title") if song else None
            for entries in themes["animethemeentries"]:
                version, episodes = entries["version"], entries["episodes"]
                for videos in entries["videos"]:
                    link = videos["link"]
                    if "NCBD1080" not in link:
                        ver = str(sequence) if sequence is not None else ""
                        anime_list.append(
                            {
                                "name": name,
                                "songname": song_name,
                                "anilist": anilist,
                                "type": str(oped) + ver,
                                "link": link,
                            }
                        )

    file_name = f"animethemes_{args.year}_{args.season}"
    if args.output == "csv":
        with open(f"{file_name}.csv", "w", encoding="utf-8", newline="") as output_file:
            dict_writer = csv.DictWriter(output_file, anime_list[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(anime_list)
    elif args.output == "json":
        with open(f"{file_name}.json", "w", encoding="utf-8") as output_file:
            json.dump(anime_list, output_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
