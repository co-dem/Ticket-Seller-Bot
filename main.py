from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram import Dispatcher, Bot, types
# from aiogram.types import InputMediaPhoto
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils import executor

from database import DataBase
from photo_manager import *
from keyboards import *
from config import *

from dotenv import load_dotenv
from datetime import datetime
import os


load_dotenv()

PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')
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
            'prices': []
        }

class OrderStage(StatesGroup):
    pre_order = State()
    order = State()

    set_seat = State()
    pay = State()

async def start(dp):
    manage_userphotos_folder()
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

    if message.text == 'Назад':
        await state.finish()
        manage_userphotos_folder()

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

    if message.text == 'Назад':
        await state.finish()
        manage_userphotos_folder()

    '''
    из сообщения "1.1, 1.2" убираем необходимые символы оставляя только цифры
    если в сообщении остаются только цифры, то мы можем предпологать, что это
    кординаты сиденья, юзер передал боту правильные значени для проверки в бд
    '''
    valid_message = data['seats'].replace('.', '').replace(',', '').replace(' ', '').isdigit()

    if valid_message:
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

    else:
        await bot.send_message(message.from_id, 'try again...')

@dp.message_handler(state = OrderStage.pay)
async def pay_func(message: types.Message, state: FSMContext):
    await state.update_data(payment_stage = message.text)
    data = await state.get_data()
    price_per_seat = 4000

    if data['payment_stage'] == 'Назад':
        await state.finish()
        manage_userphotos_folder()

    if data['payment_stage'] == 'Перейти к оплате':

        # формируем данные для инвойса
        user_buffer[message.from_id]['prices'].clear()
        total_amount = price_per_seat * len(user_buffer[message.from_id]['ordered_places'])

        seats_str = ', '.join(user_buffer[message.from_id]['ordered_places'])

        user_buffer[message.from_id]['prices'].append(
            LabeledPrice( label=f'Билеты на места: {seats_str}', amount=total_amount )

        )
        unique_payload = f"tickets_{message.from_id}_{int(datetime.now().timestamp())}"

        print(f"Отправляем инвойс: {user_buffer[message.from_id]['prices']}")
        await bot.send_invoice(
            chat_id=message.chat.id,
            title="Покупка билетов",
            description=f"Билеты на места: {seats_str}",
            payload=unique_payload,
            provider_token=PROVIDER_TOKEN,
            currency="BYN",
            prices=user_buffer[message.from_id]['prices'],
            start_parameter="buy_tickets",
            need_name=True,
            need_phone_number=True,
            need_email=False,
        )

    elif data['payment_stage'] == 'Выбрать места заново':
        user_buffer[message.from_id]['ordered_places'].clear()
        user_buffer[message.from_id]['prices'].clear()  # Очищаем и цены
        await bot.send_message(message.from_id, 'Введите номера мест заново (например: 5.12, 5.13)')
        await OrderStage.set_seat.set()

@dp.pre_checkout_query_handler(lambda query: True, state='*')
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    print("🔵 Pre-checkout вызван")
    
    # проверка на корректную сумму платежа
    if pre_checkout_query.total_amount <= 0:
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Сумма платежа некорректна. Попробуйте снова."
        )
        return
    
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT, state='*')
async def process_successful_payment(message: types.Message):
    print("🟢 Успешная оплата")
    payment = message.successful_payment
    amount = payment.total_amount / 100
    await message.answer(f"✅ Оплата {amount} {payment.currency} прошла успешно!\nОбязательно сохраните чек выше")

executor.start_polling(dp, on_startup=start)