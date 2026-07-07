from aiogram.filters.callback_data import CallbackData
from typing import Optional

class EventPaginationCB(CallbackData, prefix="event"):
    action: str
    current_index: int

class MenuCB(CallbackData, prefix="menu"):
    screen: str
    contex: str = "notify"

class FilterCB(CallbackData, prefix="filter"):
    category: str
    action: str
    value: Optional[str] = None
    context: str = "notify"

class SearchActionCB(CallbackData, prefix="search"):
    action: str