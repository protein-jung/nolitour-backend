from pydantic import BaseModel


class AdminStats(BaseModel):
    total_playgrounds: int
    pending_playgrounds: int
    total_users: int
    total_comments: int
