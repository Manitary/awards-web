from typing import Literal, TypedDict




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
