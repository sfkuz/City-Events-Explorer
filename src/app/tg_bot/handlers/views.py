from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from domain.events.entities import Event
from app.tg_bot.handlers.callbacks import EventPaginationCB, MenuCB, FilterCB, SearchActionCB

def render_event_card(event: Event) -> tuple[str, str | None]:
    price_text = f"{event.price} PLN" if event.price else "Bezpłatny"
    date_text = event.start_at.strftime("%d.%m.%Y %H:%M")

    text = (
        f"<b>{event.title}</b>\n\n"
        f"📅Date: {date_text}\n"
        f"📍Location: {event.location or 'not specified'}\n"
        f"🎭Genre: {event.genre or 'not specified'}\n"
        f"🎪Type: {event.event_type or 'not specified'}\n"
        f"💰Price: {price_text}\n"
        f"<a href='{event.url}'>Click here</a>"
    )

    return text, event.cover_image_url

def get_event_pagination_keyboard(current_index: int, total_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text='◀️ Back', callback_data=EventPaginationCB(action='prev', current_index=current_index).pack()))
    if current_index < total_count - 1:
        nav_buttons.append(InlineKeyboardButton(text='▶️ Next', callback_data=EventPaginationCB(action='next', current_index=current_index).pack()))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text='🏠 Go Home', callback_data=MenuCB(screen='main').pack()))

    return builder.as_markup()

def get_main_menu_text_and_kb(user_prefs: dict) -> tuple[str, InlineKeyboardMarkup]:
    notify_icon = '✅' if user_prefs.get('notify') else '❌'

    text = (
        f"<b> Menu </b>\n\n"
        f"🔔 Notifications: {notify_icon}\n"
        f"<i> Configure your filters to receive automatic alerts </i>\n"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="Find Events", callback_data=SearchActionCB(action="setup"))
    builder.button(text="Choose Genre", callback_data=MenuCB(screen="genres", context="notify"))
    builder.button(text="Choose Event Type", callback_data=MenuCB(screen="types", context="notify"))

    notify_btn = "Pause Notifications" if user_prefs.get('notify') else "Resume Notifications"
    builder.button(text=notify_btn, callback_data=FilterCB(category="notify", action="toggle", context="notify"))

    builder.adjust(1)
    return text, builder.as_markup()

def get_search_setup_kb(search_data: dict) -> tuple[str, InlineKeyboardMarkup]:
    genres = ", ".join(search_data.get("genres", [])) or "Any"
    types = ", ".join(search_data.get("types", [])) or "Any"
    date = search_data.get("date_str", "Any Time")

    text = (
        f"🔎 <b>Find Events</b>\n\n"
        f"Choose date, event type and genre by which you want to find events :) \n\n"
        f"📅 Date: {date}\n"
        f"🎭 Genre: {genres}\n"
        f"🎪 Type: {types}\n"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="Choose Date", callback_data=MenuCB(screen="dates", context="search"))
    builder.button(text="Choose Genre", callback_data=MenuCB(screen="genres", context="search"))
    builder.button(text="Choose Event Type", callback_data=MenuCB(screen="types", context="search"))
    builder.button(text="Find Events", callback_data=SearchActionCB(action="find"))
    builder.button(text="Go Home", callback_data=MenuCB(screen="main"))

    builder.adjust(1)
    return text, builder.as_markup()

def det_dates_menu_kb() -> tuple[str, InlineKeyboardMarkup]:
    text = "📅 <b>Choose Date</b>\nWhen do you want to go out?"
    builder = InlineKeyboardBuilder()

    builder.button(text="This weekend", callback_data=FilterCB(category="date", action="set", value="this_weekend", context="search"))
    builder.button(text="Next weekend", callback_data=FilterCB(category="date", action="set", value="next_weekend", context="search"))
    builder.button(text="This month", callback_data=FilterCB(category="date", action="set", value="this_month", context="search"))
    builder.button(text="Own dates", callback_data=FilterCB(category="date", action="set", value="own", context="search"))
    builder.button(text="◀️ Back", callback_data=SearchActionCB(action="setup"))

    builder.adjust(1)
    return text, builder.as_markup()

def get_filter_menu_kb(category: str, available_options: list[str], selected_options: list[str], context: str) -> tuple[str, InlineKeyboardMarkup]:
    title = "Genre" if category == "genre" else "Event type"
    selected_text = ", ".join(selected_options) if selected_options else "None"

    text = f"🏷 <b>{title}</b>\nSelected: {selected_text}\n\nChoose {title.lower()}s:"
    builder = InlineKeyboardBuilder()

    for option in available_options:
        icon = "✅ " if option in selected_options else "⚪"
        builder.button(text=f"{icon}{option}", callback_data=FilterCB(category=category, action="toggle", value=option, context=context))

    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="Select all", callback_data=FilterCB(category=category, action="select_all", context=context).pack()),
        InlineKeyboardButton(text="Clear all", callback_data=FilterCB(category=category, action="clear_all", context=context).pack())
    )

    back_cb = MenuCB(screen="main").pack() if context == "notify" else SearchActionCB(action="setup").pack()
    builder.row(InlineKeyboardButton(text="< Back", callback_data=back_cb))

    return text, builder.as_markup()