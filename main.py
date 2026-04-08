from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram import Dispatcher, Bot, types
from aiogram.types import InputMediaPhoto
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

async def login(message):
    if not user_buffer.get(message.from_id):
        user_buffer[message.from_id] = {
            'ordered_places': [],
            'edit_msg_id': None,
            'prices': [],
            'discount': 0,
            'promocode': None
        }

        user_id_list = db_client.get_column('users', 'user_id')
        if message.from_id in user_id_list and user_buffer[message.from_id]['discount'] and user_buffer[message.from_id]['promocode']:
            user_buffer[message.from_id]['discount'] = db_client.get_data('users', 'discount', 'user_id', message.from_id)[0]['discount']
            user_buffer[message.from_id]['promocode'] = db_client.get_data('users', 'promocode', 'user_id', message.from_id)[0]['promocode']
        elif message.from_id not in user_id_list:
            db_client.insert_data('users', {'user_id': message.from_id, 'username': message.from_user.username})
        
class OrderStage(StatesGroup):
    pre_order = State()
    order = State()

    set_seat = State()
    pay = State()

    set_promocode = State()

async def start(dp):
    manage_userphotos_folder()
    print('started')

@dp.message_handler(commands='start')
async def welcome(message: types.Message):
    await login(message)
    print(user_buffer)

    await bot.send_message(message.from_id, 'Hello World', reply_markup=user_main_menu)

@dp.message_handler(content_types='text')
async def main(message: types.Message):
    await login(message)
    print(user_buffer)

    if message.text == 'Билеты':
        with open(SCENE_PHOTO_PATH, 'rb') as photo:
            user_buffer[message.from_id]['edit_msg_id'] = \
                await bot.send_photo(message.from_id, photo, 'Свободные места:', reply_markup=pre_order_rkm)
        await OrderStage.pre_order.set()

    elif message.text == 'Профиль':
        await bot.send_message(message.from_id, 'some text', reply_markup=profile_rkm)
        
    elif message.text == 'Афиша':
        await bot.send_location(message.from_id, latitude=53.905227, longitude=27.564624)

    elif message.text == 'Промокоды':
        await bot.send_message(message.from_id, 'введите промокод', reply_markup=cancel_rkm)
        await OrderStage.set_promocode.set()

async def stateExit_func(state, uid, message):
    await state.finish()
    del user_buffer[uid]
    manage_userphotos_folder(uid)
    await bot.send_message(message.from_id, 'main_menu', reply_markup=user_main_menu)

@dp.message_handler(state = OrderStage.set_promocode)
async def setPromocode_func(message: types.Message, state: FSMContext):
    await state.update_data(promo = message.text)
    data = await state.get_data()

    if data['promo'] == 'Назад':
        await state.finish()

    elif bool(db_client.get_data('users', 'discount', 'user_id', message.from_id)[0]['discount']):
        await bot.send_message(message.from_id, 'у вас уже есть промокод!')

    elif data['promo'] in db_client.get_column('promocodes', 'name'):
        dis = db_client.get_data('promocodes', 'discount', 'name', data['promo'])[0]['discount']
        db_client.supabase.table('users')\
            .update({'discount': dis, 'promocode': data['promo']})\
            .eq('user_id', message.from_id).execute()

        user_buffer[message.from_id]['discount'] = dis
        user_buffer[message.from_id]['promocode'] = data['promo']
        print(user_buffer)

        await bot.send_message(message.from_id, f'ваша скидка составляет {dis} BYN')

    await bot.send_message(message.from_id, 'main menu...', reply_markup=user_main_menu)
    await state.finish()

@dp.message_handler(state = OrderStage.pre_order)
async def preOrder_func(message: types.Message, state: FSMContext):
    await state.update_data(po_msg = message.text)
    data = await state.get_data()

    if data['po_msg'] == 'Назад':
        await stateExit_func(state, message.from_id, message)
        return

    if user_buffer[message.from_id].get('edit_msg_id'):
        await bot.delete_message(message.from_id, user_buffer[message.from_id]['edit_msg_id'].message_id)

    with open(SCENE_PHOTO_PATH, 'rb') as photo:
            sent_msg = await bot.send_photo(
                message.from_id, photo, 
                'Введите номер ряда и сидения через точку (5.12)\nесли хотите купить 2 и более билета, то введите номера сидений через запятую: (5.12, 5.13, 4.10)'
            )
            user_buffer[message.from_id]['edit_msg_id'] = sent_msg
            await OrderStage.set_seat.set()

@dp.message_handler(state = OrderStage.set_seat)
async def setSeat_func(message: types.Message, state: FSMContext):
    await state.update_data(seats = message.text)
    data = await state.get_data()
    order_msg = ''
    x, y = 0, 0

    valid_message = data['seats'].replace('.', '').replace(',', '').replace(' ', '').isdigit()
    
    if data['seats'] == 'Назад':
        await stateExit_func(state, message.from_id, message)
        return

    elif valid_message:
        create_up_folder(message.from_id)

        for i in data['seats'].split(','):
            si = i.strip().split('.')
            
            if len(si) == 2 and db_client.seat_is_free('places', int(si[0]), si[1]):
                
                user_buffer[message.from_id]['ordered_places'].append(i)
                order_msg += f'\nМесто {si[0]}.{si[1]} свободно'

                x, y = get_cords(int(si[0]), int(si[1]))
                print(x, y)
                put_point(
                    x, y,
                    img_path = f"{USERS_SCENE_FOLDER}\{message.from_id}\scene.png", 
                    radius=40, color=(255,0,255),
                    save_path= f"{USERS_SCENE_FOLDER}\{message.from_id}\scene.png"
                )
            
            else:
                order_msg += f'\nМесто {si[0]}.{si[1]} занято'
                
        try:
            with open(f"{USERS_SCENE_FOLDER}\{message.from_id}\scene.png", 'rb') as n_photo:
                
                await bot.edit_message_media(
                    InputMediaPhoto(
                        n_photo,
                        caption = order_msg
                    ),
                    message.from_id,
                    user_buffer[message.from_id]['edit_msg_id'].message_id,
                )
        except Exception as e:
            with open(f"{USERS_SCENE_FOLDER}\{message.from_id}\scene.png", 'rb') as n_photo:
                new_msg = await bot.send_photo(
                    message.from_id,
                    n_photo,
                    caption=order_msg
                )
                user_buffer[message.from_id]['edit_msg_id'] = new_msg
        
        if len(user_buffer[message.from_id]['ordered_places']) == 0:
            await bot.send_message(message.from_id, 'try again...')
            await OrderStage.set_seat.set()
        else:
            await bot.send_message(message.from_id, f'В вашу корзину добавлено {len(user_buffer[message.from_id]["ordered_places"])} элементов', reply_markup=go_to_payment)
            await OrderStage.pay.set()

    else:
        await bot.send_message(message.from_id, 'try again...')
        await OrderStage.set_seat.set()

@dp.message_handler(state = OrderStage.pay)
async def pay_func(message: types.Message, state: FSMContext):
    await state.update_data(payment_stage = message.text)
    data = await state.get_data()
    price_per_seat = 4000 - ( user_buffer[message.from_id]['discount'] * 100 )

    if data['payment_stage'] == 'Назад':
        await stateExit_func(state, message.from_id, message)
        return

    elif data['payment_stage'] == 'Перейти к оплате':
        #* формируем данные для инвойса
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
        user_buffer[message.from_id]['prices'].clear()
        manage_userphotos_folder(message.from_id)

        with open(SCENE_PHOTO_PATH, 'rb') as photo:
            user_buffer[message.from_id]['edit_msg_id'] =  await bot.send_photo(
                message.from_id, photo, 
                'Введите номер ряда и сидения через точку (5.12)\nесли хотите купить 2 и более билета, то введите номера сидений через запятую: (5.12, 5.13, 4.10)',
                reply_markup=ReplyKeyboardRemove()
            
            )
        await OrderStage.set_seat.set()

@dp.pre_checkout_query_handler(lambda query: True, state='*')
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    print("🔵 Pre-checkout вызван")
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT, state='*')
async def process_successful_payment(message: types.Message, state: FSMContext):
    payment = message.successful_payment
    amount = payment.total_amount / 100

    await message.answer(f"✅ Оплата {amount} {payment.currency} прошла успешно!\nОбязательно сохраните чек выше")

    print("🟢 Успешная оплата")
    print(payment)

    users_data = {'purchased': ' '.join(user_buffer[message.from_id]['ordered_places'])}

    receipt_data = {
        'user_id': message.from_id, 
        'username': message.from_user.username, 
        'amount': int(amount),
        'place': ' '.join(user_buffer[message.from_id]['ordered_places']),
        'payload': payment.invoice_payload,
    }

    if bool(user_buffer[message.from_id]['discount']):
        users_data['bought_with_discount'] = int(amount)
        users_data['promocode'] = user_buffer[message.from_id]['promocode']

        receipt_data['promocode'] = user_buffer[message.from_id]['promocode']
    else: 
        users_data['spent'] = int(amount)

    db_client.update_user_data('users', users_data, message.from_id)
    db_client.insert_data('receipt', receipt_data)
    try: db_client.increment_used_promocodes('name', user_buffer[message.from_id]['promocode'])
    except IndexError: pass

    for i in user_buffer[message.from_id]['ordered_places']:
        si = i.split('.')
        x, y = get_cords(int(si[0]), int(si[1]))
        print('[process_successful_payment]: ', x, y)
        put_point(
            x, y,
            img_path = SCENE_PHOTO_PATH,
            radius=40, color=(255,0,0),
            save_path= SCENE_PHOTO_PATH
        )

        db_client.remove_column('places', i.split('.')[0], i.split('.')[1])

    del user_buffer[message.from_id]
    await state.finish()

    print(user_buffer)

    await bot.send_message(message.from_id, 'main menu...', reply_markup=user_main_menu)

executor.start_polling(dp, on_startup=start)