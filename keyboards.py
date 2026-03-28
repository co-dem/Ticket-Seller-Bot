from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
                          InlineKeyboardMarkup, InlineKeyboardButton

user_main_menu = ReplyKeyboardMarkup(
    keyboard = [
        [KeyboardButton('Билеты')],
        [KeyboardButton('Профиль'), KeyboardButton('Афиша')]
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