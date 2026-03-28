from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram import Dispatcher, Bot, types
from aiogram.utils import executor

from database import DataBase
from keyboards import *
from config import *

from dotenv import load_dotenv
import os


load_dotenv()

user_buffer = {}
storage = MemoryStorage()
bot = Bot(os.getenv('TG_TOKEN'), parse_mode='html')
dp = Dispatcher(bot, storage=storage)

async def login(message, clear = True):
    if not user_buffer.get(message.from_id):
        user_buffer[message.from_id] = {
            'ordered_places': [],
            'edit_msg_id': []
        }

class OrderStage(StatesGroup):
    pre_order = State()
    order = State()

@dp.message_handler(commands='start')
async def welcome(message: types.Message):
    await bot.send_message(message.from_id, 'Hello World', reply_markup=user_main_menu)

@dp.message_handler(content_types='text')
async def main(message: types.Message):
    if message.text == 'Билеты':
        with open(PLACES_PHOTO_PATH, 'rb') as photo:
            user_buffer[message.from_id]['edit_msg_id'] = await bot.send_photo(message.from_id, photo, 'Свободные места:', reply_markup=pre_order_rkm)
        await OrderStage.pre_order.set()

    elif message.text == 'Профиль':
        await bot.send_message(message.from_id, '')
    elif message.text == 'Афиша':
        await bot.send_message(message.from_id, '')
        

@dp.message_handler(state = OrderStage.pre_order)
async def preOrder_func(message: types.Message, state: FSMContext):
    await state.update_data(po_msg = message.text)
    data = await state.get_data()

    await bot.send_message(message.from_id, data)
    await bot.send_message(message.from_id, data['po_msg'])
    
    if data['po_msg'] == 'Купить места':
        pass

executor.start_polling(dp)