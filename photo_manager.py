from PIL import Image, ImageDraw
from config import SCENE_PHOTO_PATH, USERS_SCENE_FOLDER
import shutil
import os


def put_point(x, y, img_path = SCENE_PHOTO_PATH, radius=5, color=(255,0,0), opacity=150, save_path=None):
    original_img = Image.open(img_path).convert("RGBA")
    
    # создаём отдельный прозрачный слой 
    circle_layer = Image.new("RGBA", original_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(circle_layer)
    
    # полупрозрачный круг на отдельном слое
    circle_color = (color[0], color[1], color[2], opacity)
    draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)], fill=circle_color)
    
    # обьединяем основной и созданный слои
    result = Image.alpha_composite(original_img, circle_layer)
    
    if save_path is None: save_path = img_path
    result = result.convert('P', palette=Image.ADAPTIVE, colors=256)
    result.save(save_path, compress_level=9, optimize=True)

def get_cords(row, col):
    x = 0
    y = 0

    # колонны от 1 до 7 (лево)
    if col in range(1, 8):
        if row in range(1, 15) or row == 15 and col in range(2, 7):
            x = 72 + ((col - 1) * 100 )
        
        elif row in range(16, 20) and col in range(2, 8): 
            x = 121 + ((col - 2) * 100 )

    # колонны от 8 от 17 (центр)
    elif col in range(8, 18):
        if row in range(1, 14) or row == 19 and col in range(10, 18):
            x = 965 + ((col - 8) * 100 )
        
        elif row == 19 and col in range(10, 18):
            x = 965 + ((col - 9) * 100 )
        
        elif row in range(15, 19) and col in range(11, 18): 
            x = 1114 + ((col - 11) * 100 )

    # колонны от 18 от 24 (право)
    elif col in range(18, 25):
        if row in range(1, 15) or row == 15 and col in range(2, 7):
            x = 2158 + ((col - 18) * 100 )
        
        elif row in range(16, 20) and col in range(19, 25): 
            x = 2207 + ((col - 19) * 100 )
    else: return [0, 0]

    y = 625 + ((row - 1) * 100)
    print('done')
    return [x, y]

# x, y = get_cords(19, 24)
# put_point(x, y, img_path = 'src\scene.png', radius=40, color=(255,0,0), save_path='src\scene1.png')

def create_up_folder(uid): #? up -> User Photos
    if os.path.exists(USERS_SCENE_FOLDER): 
        os.mkdir(f"{USERS_SCENE_FOLDER}\{uid}")
        shutil.copy(SCENE_PHOTO_PATH, f"{USERS_SCENE_FOLDER}\{uid}\scene.png")


def manage_userphotos_folder(uid = 0):
    if uid:
        shutil.rmtree(f"{USERS_SCENE_FOLDER}\{uid}")
    else:
        if os.path.exists(USERS_SCENE_FOLDER): shutil.rmtree(USERS_SCENE_FOLDER)
        os.mkdir(USERS_SCENE_FOLDER)