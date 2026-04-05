from PIL import Image, ImageDraw
from config import SCENE_PHOTO_PATH, USERS_SCENE_FOLDER
import shutil
import os

def put_point(img_path = SCENE_PHOTO_PATH, x, y, radius=5, color=(255,0,0), opacity=150, save_path=None):
    original_img = Image.open(img_path).convert("RGBA")
    
    # создаём отдельный прозрачный слой 
    circle_layer = Image.new("RGBA", original_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(circle_layer)
    
    # круг с прозрачностью на отдельном слое
    circle_color = (color[0], color[1], color[2], opacity)
    draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)], fill=circle_color)
    
    # обьединяем оба слоя
    result = Image.alpha_composite(original_img, circle_layer)
    
    if save_path is None: save_path = img_path
    
    result.save(save_path)

# put_point(x=275, y=635, radius=40, color=(255,0,0))

def manage_userphotos_folder(uid = 0):
    if uid:
        shutil.rmtree(f"{USERS_SCENE_FOLDER}\{uid}")
    else:
        if os.path.exists(USERS_SCENE_FOLDER): shutil.rmtree(USERS_SCENE_FOLDER)
        os.mkdir(USERS_SCENE_FOLDER)