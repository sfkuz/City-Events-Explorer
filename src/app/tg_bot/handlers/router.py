from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import logging
from datetime import datetime

from app.tg_bot.utils import resolve_dates
from application.events.service import EventService
from app.tg_bot.handlers.callbacks import EventPaginationCB, MenuCB, SearchActionCB, FilterCB
from app.tg_bot.handlers.states import SearchEventState
from app.tg_bot.handlers.views import (
    render_event_card, get_event_pagination_keyboard,
    get_main_menu_text_and_kb, get_filter_menu_kb,
    get_search_setup_kb, get_dates_menu_kb
)

main_router = Router()

logger = logging.getLogger(__name__)

AVAILABLE_GENRES = [
    'jazz', 'pop', 'rock/punk', 'muzyka poważna',
    'muzyka elektroniczna', 'muzyka filmowa',
    'muzyka alternatywna', 'hip-hop',
    'festiwal muzyczny', 'blues/soul'
]
AVAILABLE_TYPES = [
    'koncerty', 'imprezy rozrywkowe'
]

mock_user_db: dict[int, dict] = {}
def get_user_prefs(user_id: int) -> dict:
    if user_id not in mock_user_db:
        mock_user_db[user_id] = {'notify': True, 'genres': [], 'types': []}
    return mock_user_db[user_id]

@main_router.message(Command('start', 'menu'))
async def show_main_menu(message: Message, state: FSMContext):
    await state.clear()
    prefs = get_user_prefs(message.from_user.id)
    text, markup = get_main_menu_text_and_kb(prefs)
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

@main_router.callback_query(MenuCB.filter(F.screen == 'main'))
async def go_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    prefs = get_user_prefs(callback.from_user.id)
    text, markup = get_main_menu_text_and_kb(prefs)

    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@main_router.callback_query(SearchActionCB.filter(F.action == 'setup'))
async def setup_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchEventState.setup)
    search_data = await state.get_data()
    text, markup = get_search_setup_kb(search_data)

    if isinstance(callback.message, Message):
        await callback.message.delete()
        await callback.message.answer(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@main_router.callback_query(MenuCB.filter(F.screen.in_(['genres', 'types'])))
async def open_filters(callback: CallbackQuery, callback_data: MenuCB, state: FSMContext):
    category = 'genre' if callback_data.screen == 'genres' else 'type'
    available_list = AVAILABLE_GENRES if category == 'genre' else AVAILABLE_TYPES

    if callback_data.context == 'search':
        data = await state.get_data()
        selected = data.get(callback_data.screen, [])
    else:
        prefs = get_user_prefs(callback.from_user.id)
        selected = prefs[callback_data.screen].copy()

    text, markup = get_filter_menu_kb(category, available_list, selected, callback_data.context)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@main_router.callback_query(MenuCB.filter(F.screen == 'dates'))
async def open_dates(callback: CallbackQuery):
    text, markup = get_dates_menu_kb()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@main_router.callback_query(FilterCB.filter())
async def handle_filters(callback: CallbackQuery, callback_data: FilterCB, state: FSMContext):
    if callback_data.category == "notify" and callback_data.action == "toggle":
        prefs = get_user_prefs(callback.from_user.id)
        prefs["notify"] = not prefs["notify"]

        text, markup = get_main_menu_text_and_kb(prefs)

        if isinstance(callback.message, Message):
            await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
        await callback.answer("Notification settings have been changed")
        return

    if callback_data.category == "date" and callback_data.value == "own":
        await state.set_state(SearchEventState.waiting_for_dates)
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                "📅 <b>Entering your own dates</b>\n\n"
                "Please enter the date range strictly in the format <b>DD.MM.YYYY - DD.MM.YYYY</b>\n"
                "<i>(e.g.: 04.10.2026 - 16.12.2026)</i>:",
                parse_mode="HTML"
            )
        await callback.answer()
        return

    if callback_data.category == "date":
        display_name = (callback_data.value or "").replace("_", " ").title()

        await state.update_data(date_value=callback_data.value, date_str=display_name)
        search_data = await state.get_data()
        text, markup = get_search_setup_kb(search_data)
        if isinstance(callback.message, Message):
            await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
        return

    list_key = "genres" if callback_data.category == "genre" else "types"
    available_list = AVAILABLE_GENRES if callback_data.category == "genre" else AVAILABLE_TYPES

    if callback_data.context == "search":
        data = await state.get_data()
        current_list = data.get(list_key, [])
    else:
        prefs = get_user_prefs(callback.from_user.id)
        current_list = prefs[list_key].copy()

    if callback_data.action == "toggle":
        if callback_data.value in current_list:
            current_list.remove(callback_data.value)
        else:
            current_list.append(callback_data.value)
    elif callback_data.action == "select_all":
        current_list = available_list.copy()
    elif callback_data.action == "clear_all":
        current_list = []

    if callback_data.context == "search":
        await state.update_data({list_key: current_list})
    else:
        prefs[list_key] = current_list

    text, markup = get_filter_menu_kb(callback_data.category, available_list, current_list, callback_data.context)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@main_router.message(SearchEventState.waiting_for_dates)
async def process_own_dates(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Please send the dates in text")
        return

    user_text = message.text

    try:
        parts = [p.strip() for p in user_text.split('-')]
        if len(parts) != 2:
            raise ValueError('invalid format')

        start_str, end_str = parts

        start_date = datetime.strptime(start_str, '%d.%m.%Y')
        end_date = datetime.strptime(end_str, '%d.%m.%Y')

        if end_date < start_date:
            await message.answer('The end date cannot be less than the start date. Try again! e.g. 04.10.2026 - 16.12.2026')
            return
    except ValueError:
        await message.answer('Invalid format. Please write date in this format: DD.MM.YYYY - DD.MM.YYYY (e.g. 04.10.2026 - 16.12.2026)')
        return

    await state.update_data(
        date_value='own',
        date_str=f'{start_str}-{end_str}',
        date_from=start_date.isoformat(),
        date_to=end_date.isoformat()
    )

    await state.set_state(SearchEventState.setup)

    search_data = await state.get_data()
    text, markup = get_search_setup_kb(search_data)
    await message.answer(text=text, reply_markup=markup, parse_mode='HTML')

@main_router.message(Command('events'))
async def show_events_cmd(message: Message, state: FSMContext, event_service: EventService):
    await state.update_data(current_view='today')

    events = await event_service.get_events_for_today()

    if not events:
        await message.answer("There are no events for today.")
        return

    text, photo_url = render_event_card(events[0])
    markup = get_event_pagination_keyboard(current_index=0, total_count=len(events))

    if photo_url:
        await message.answer_photo(photo=photo_url, caption=text, reply_markup=markup, parse_mode='HTML')
    else:
        await message.answer(text=text, reply_markup=markup, parse_mode='HTML')

@main_router.callback_query(SearchActionCB.filter(F.action == 'find'))
async def execute_search(callback: CallbackQuery, state: FSMContext, event_service: EventService):
    search_data = await state.get_data()

    genres = search_data.get('genres', [])
    types = search_data.get('types', [])

    date_val = search_data.get('date_value')
    custom_from = search_data.get('date_from')
    custom_to = search_data.get('date_to')

    date_from, date_to = resolve_dates(date_val, custom_from, custom_to)

    events = await event_service.search_events(
        genres=genres if genres else None,
        types=types if types else None,
        date_from=date_from,
        date_to=date_to
    )

    if not events:
        await callback.answer('Nothing found matching your filters 😔', show_alert=True)
        return

    await state.update_data(current_view='search')

    text, photo_url = render_event_card(events[0])
    markup = get_event_pagination_keyboard(current_index=0, total_count=len(events))

    if isinstance(callback.message, Message):
        await callback.message.delete()
        if photo_url:
            await callback.message.answer_photo(photo=photo_url, caption=text, reply_markup=markup, parse_mode='HTML')
        else:
            await callback.message.answer(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()

@main_router.callback_query(EventPaginationCB.filter())
async def paginate_events(callback: CallbackQuery, callback_data: EventPaginationCB, state: FSMContext, event_service: EventService):
    user_data = await state.get_data()
    current_view = user_data.get('current_view', 'today')

    if current_view == 'search':
        date_from, date_to = resolve_dates(
            user_data.get('date_value'),
            user_data.get('date_from'),
            user_data.get('date_to')
        )
        events = await event_service.search_events(
            genres=user_data.get('genres', []) or None,
            types=user_data.get('types', []) or None,
            date_from=date_from,
            date_to=date_to
        )
    else:
        events = await event_service.get_events_for_today()

    if not events:
        await callback.answer('Nothing found matching your filters.', show_alert=True)
        return

    new_index = callback_data.current_index
    if callback_data.action == 'next':
        new_index += 1
    elif callback_data.action == 'prev':
        new_index -= 1

    if new_index < 0 or new_index >= len(events):
        await callback.answer('this is the end of the list', show_alert=True)
        return

    text, photo_url = render_event_card(events[new_index])
    markup = get_event_pagination_keyboard(current_index=new_index, total_count=len(events))

    if isinstance(callback.message, Message):
        await callback.message.delete()
        if photo_url:
            await callback.message.answer_photo(photo=photo_url, caption=text, reply_markup=markup, parse_mode='HTML')
        else:
            await callback.message.answer(text=text, reply_markup=markup, parse_mode='HTML')
    await callback.answer()