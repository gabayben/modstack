from typing import NotRequired, TypedDict

class RedditQuery(TypedDict):
    subreddit: NotRequired[list[str]]
    search_query: NotRequired[str]