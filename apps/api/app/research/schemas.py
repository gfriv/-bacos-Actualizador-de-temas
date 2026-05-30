from pydantic import BaseModel, HttpUrl


class SearchResult(BaseModel):
    title: str
    url: HttpUrl | str
    snippet: str = ""
    source: str = ""

    def as_markdown(self) -> str:
        text = f"- [{self.title}]({self.url})"
        if self.snippet:
            text += f": {self.snippet}"
        return text
