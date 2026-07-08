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