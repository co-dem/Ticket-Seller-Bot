from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram import Dispatcher, Bot, types
from aiogram.types import InputMediaPhoto
from aiogram.utils import executor

from database import DataBase
from photo_manager import *
from keyboards import *
from config import *

from dotenv import load_dotenv
import os


load_dotenv()

db_client = DataBase(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
user_buffer = {}
storage = MemoryStorage()
bot = Bot(os.getenv('TG_TOKEN'), parse_mode='html')
dp = Dispatcher(bot, storage=storage)

async def login(message, clear = True):
    if not user_buffer.get(message.from_id):
        user_buffer[message.from_id] = {
            'ordered_places': [],
            'edit_msg_id': None,
        }

class OrderStage(StatesGroup):
    pre_order = State()
    order = State()

    set_seat = State()
    pay = State()

async def start(dp):
    clear_user_photos()
    print('started')

@dp.message_handler(commands='start')
async def welcome(message: types.Message):
    await login(message)

    await bot.send_message(message.from_id, 'Hello World', reply_markup=user_main_menu)

@dp.message_handler(content_types='text')
async def main(message: types.Message):
    if message.text == 'Билеты':
        with open(SCENE_PHOTO_PATH, 'rb') as photo:
            user_buffer[message.from_id]['edit_msg_id'] = \
                await bot.send_photo(message.from_id, photo, 'Свободные места:', reply_markup=pre_order_rkm)
        await OrderStage.pre_order.set()

    elif message.text == 'Профиль':
        await bot.send_message(message.from_id, '')
    elif message.text == 'Афиша':
        await bot.send_location(message.from_id, latitude=53.905227, longitude=27.564624)
        
'''
может лучше сделать выбор места по координатам?
[просить юзера самому вводить номер ряда и места в одном сообщении]
если сделать так, то можно будет очень легко покупать два и более мест
за один заказ. Плюс это должно сильно уменьшить нагрузку на сервак
'''
@dp.message_handler(state = OrderStage.pre_order)
async def preOrder_func(message: types.Message, state: FSMContext):
    await state.update_data(po_msg = message.text)
    data = await state.get_data()

    # TODO: cancel func here
    if data['po_msg'] == 'Назад': return

    await bot.delete_message(message.from_id, user_buffer[message.from_id]['edit_msg_id'].message_id)

    with open(SCENE_PHOTO_PATH, 'rb') as photo:
        user_buffer[message.from_id]['edit_msg_id'] =  await bot.send_photo(
            message.from_id, photo, 'Введите номер ряда и сидения через точку (5.12)\nесли хотите купить 2 и более билета, то введите номера сидений через запятую: (5.12, 5.13, 4.10)'
        )
        await OrderStage.set_seat.set()

@dp.message_handler(state = OrderStage.set_seat)
async def setSeat_func(message: types.Message, state: FSMContext):
    await state.update_data(seats = message.text)
    data = await state.get_data()
    order_msg = ''

    for i in data['seats'].split(','):
        si = i.split('.') #? si - Seat Info
        if db_client.seat_is_free('places', int(si[0]), int(si[1])):
            user_buffer[message.from_id]['ordered_places'].append(i)
            order_msg += f'\nМесто {si[0]}.{si[1]} свободно'
        else:
            order_msg += f'\nМесто {si[0]}.{si[1]} занято'
        
    await bot.send_message(message.from_id, order_msg)
    await bot.send_message(message.from_id, f'В вашу корзину добавлено {len(user_buffer[message.from_id]["ordered_places"])} элементов', reply_markup=go_to_payment)
    await OrderStage.pay.set()

@dp.message_handler(state = OrderStage.pay)
async def pay_func(message: types.Message, state: FSMContext):
    await state.update_data(payment_stage = message.text)
    data = await state.get_data()

    if message.text == 'Назад': return

    if message.text == 'Перейти к оплате':
        pass
    
    elif message.text == 'Выбрать места заново':
        pass

executor.start_polling(dp, on_startup=start)