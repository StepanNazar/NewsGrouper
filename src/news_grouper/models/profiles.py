import json
from dataclasses import asdict, dataclass

from news_grouper.models.news_source import NewsSource
from news_grouper.news_parsers import NewsParser


@dataclass
class Profile:
    name: str
    description: str
    news_sources: list[NewsSource]
    file_path: str | None = None

    @classmethod
    def load(cls, path: str) -> "Profile":
        """Load a profile from a file."""
        with open(path) as file:
            data = json.load(file)
        for source in data["news_sources"]:
            source["parser"] = NewsParser.get_parser_by_name(source["parser"])
        data["news_sources"] = [NewsSource(**source) for source in data["news_sources"]]
        data["file_path"] = path
        return cls(**data)

    def save(self, path: str | None = None) -> None:
        """
        Save the profile to a file.
        If no path is provided, it will use the file_path attribute.
        """
        path = path or self.file_path
        if path is None:
            raise ValueError("No file path specified for saving the profile.")
        data = asdict(self)
        for source in data["news_sources"]:
            source["parser"] = source["parser"].name
        with open(path, "w") as file:
            json.dump(data, file)
