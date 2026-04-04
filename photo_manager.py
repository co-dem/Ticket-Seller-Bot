from PIL import Image, ImageDraw
from config import SCENE_PHOTO_PATH, USERS_SCENE_FOLDER
import shutil
import os

'''
нужно сделать функции чтобы когда юзер выбирал ряд, эта
функция подсвечивала весь ряд жёлтым

и ещё функцию чтобы когда юзер выбирал место, она выделяла
только это место жёлтым

'''

def select_func(row: int, column: int):
    base = Image.open(SCENE_PHOTO_PATH).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 0, 1))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((12,12), fill=(255, 255, 0))
    out = Image.alpha_composite(base, overlay)
    out.convert("RGB").save(USERS_SCENE_FOLDER) 

# select_func(1, 1)

def clear_user_photos():
    # удалить папку с содержимым
    if os.path.exists(USERS_SCENE_FOLDER): shutil.rmtree(USERS_SCENE_FOLDER)

    # создать папку заново
    os.mkdir(USERS_SCENE_FOLDER)

# clear_user_photos()