from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from application.events.service import EventService
from app.tg_bot.handlers.callbacks import EventPaginationCB, MenuCB, SearchActionCB, FilterCB
from app.tg_bot.handlers.states import SearchEventState
from app.tg_bot.handlers.views import (
    render_event_card, get_event_pagination_keyboard,
    get_main_menu_text_and_kb, get_filter_menu_kb,
    get_search_setup_kb, get_dates_menu_kb
)

main_router = Router()

AVAILABLE_GENRES = [
    'jazz', 'pop', 'rock/punk', 'muzyka poważna',
    'muzyka elektroniczna', 'muzyka filmowa',
    'muzyka alternatywna', 'hip-hop',
    'festiwal muzyczny', 'blues/soul'
]
AVAILABLE_TYPES = [
    'koncerty', 'spektakle', 'kulinaria',
    'imprezy rozrywkowe', 'imprezy okolicznościowe',
    'wystawy, spotkania', 'sport, rekreacja',
    'tragi, konferencje', 'film, kino'
]

mock_user_db = {}
def get_user_prefs(user_id: int) -> dict:
    if user_id not in mock_user_db:
        mock_user_db[user_id] = {'notify': True, 'genres': [], 'types': []}
    return mock_user_db[user_id]

@main_router.message(Command('start', 'menu'))
async def show_main_menu(message: Message, state: FSMContext):
    pass

@main_router.callback_query(MenuCB.filter(F.screen == 'main'))
async def go_home(callback: CallbackQuery, state: FSMContext):
    pass

@main_router.callback_query(SearchActionCB.filter(F.action == 'setup'))
async def setup_search(callback: CallbackQuery, state: FSMContext):
    pass

@main_router.callback_query(MenuCB.filter(F.screen.in_(['genres', 'types'])))
async def open_filters(callback: CallbackQuery, callback_data: MenuCB, state: FSMContext):
    pass

@main_router.callback_query(MenuCB.filter(F.screen == 'dates'))
async def open_dates(callback: CallbackQuery):
    pass

@main_router.callback_query(FilterCB.filter())
async def handle_filters(callback: CallbackQuery, callback_data: FilterCB, state: FSMContext):
    pass

@main_router.message(SearchEventState.waiting_for_dates)
async def process_own_dates(message: Message, state: FSMContext):
    pass

@main_router.callback_query(SearchActionCB.filter(F.action == 'find'))
async def execute_search(callback: CallbackQuery, state: FSMContext, event_service: EventService):
    pass