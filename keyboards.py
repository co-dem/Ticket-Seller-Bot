from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
                          InlineKeyboardMarkup, InlineKeyboardButton

user_main_menu = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Билеты')],
        [KeyboardButton('Профиль'), KeyboardButton('Афиша')]
    ], resize_keyboard = True
)

profile_rkm = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Промокоды')]
    ], resize_keyboard = True
)

pre_order_rkm = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Купить места')],
        [KeyboardButton('Назад')]
    ], resize_keyboard = True
)

afisha_rkm = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Локация')]
    ], resize_keyboard = True
)

go_to_payment = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Перейти к оплате')],
        [KeyboardButton('Выбрать места заново')],
        [KeyboardButton('Назад')]
    ], resize_keyboard = True
)

cancel_rkm = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Назад')]
    ], resize_keyboard = True
)

'''
[
    {'id': 1, 'free_column': '1, 2, 3, 4, 5, 6, 7, 8', 'free_row': 1}, 
    {'id': 2, 'free_column': '1, 2, 3, 4, 5, 6, 7, 8', 'free_row': 2}, 
    {'id': 3, 'free_column': '1, 2, 3, 4, 5, 6, 7, 8', 'free_row': 3}, 
    {'id': 4, 'free_column': '1, 2, 3, 4, 5, 6, 7, 8', 'free_row': 4}, 
    {'id': 5, 'free_column': '1, 2, 3, 4, 5, 6, 7, 8', 'free_row': 5}
]
'''