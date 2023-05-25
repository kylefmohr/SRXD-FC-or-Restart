from PIL import ImageGrab, Image, ImageOps
import time
from skimage.metrics import structural_similarity as ssim
import numpy as np
from pynput.keyboard import Key, Controller


keyboard = Controller()
ssim_cutoff = 0.75



def load_settings():
    current_line = None
    imported_resolution_width, imported_resolution_height, imported_hud_style, imported_hud_distance, restart_upon = 0, 0, "default", 0, "pfc"
    with open("settings.ini", 'r') as f:
        while current_line != "":
            current_line = f.readline()
            if "Resolution" in current_line:
                try:
                    current_line = f.readline().lower()
                    imported_resolution_width = int(current_line.split("x")[0].strip())
                    imported_resolution_height = int(current_line.split("x")[1].strip())
                except ValueError:
                    print("Invalid resolution in settings.json, please make sure it's formatted like: 1920x1080")
                    exit(1)
            elif "HUD Style" in current_line:
                imported_hud_style = f.readline().strip().lower()
                if imported_hud_style not in ["default", "angled"]:
                    print("Invalid HUD style in settings.json, please make sure it's either 'default' or 'angled'")
                    exit(1)
            elif "HUD Distance" in current_line:
                try:
                    imported_hud_distance = int(f.readline().strip())
                    if imported_hud_distance < 0 or imported_hud_distance > 100:
                        print("Invalid HUD distance in settings.json, please make sure it's a number between 0 and 100")
                        exit(1)
                except ValueError:
                    print("Invalid HUD distance in settings.json, please make sure it's a number between 0 and 100")
                    exit(1)
            elif "Restart upon losing..." in current_line:
                restart_upon = f.readline().strip().lower()
                if restart_upon not in ["pfc", "fc"]:
                    print("Invalid 'restart upon losing...' in settings.json, please make sure it's either 'PFC' or 'FC'")
                    exit(1)
    settings_tuple = (imported_resolution_width, imported_resolution_height, imported_hud_style, imported_hud_distance, restart_upon)
    return settings_tuple


def get_bounding_box(settings):
    # imported_resolution_width, imported_resolution_height, imported_hud_style, imported_hud_distance = settings
    if settings[2] == "angled" and settings[3] == 0:
        resolution = 826 * (settings[0] / 2560), 623 * (settings[1] / 1440)
        bounding_box = resolution[0], resolution[1], resolution[0] + 96 * (settings[0] / 2560), resolution[1] + 120 * (settings[1] / 1440)
        return bounding_box
    else:
        print("Currently, only angled HUDs and 0 HUD distance are supported. Please change your in-game settings as well as settings.ini")


if __name__ == "__main__":
    settings = load_settings()
    print(settings)
    bounding_box = get_bounding_box(settings)
    print(bounding_box)
    restart_setting = settings[4]
    pfc = np.array(Image.open("gpfc.png").convert("LA")) # greyscale PFC
    fc = np.array(Image.open("gfc.png").convert("LA")) # greyscale FC
    # verify that the bounding box is the same size as the images, else resize the images
    if bounding_box[2] - bounding_box[0] != fc.shape[1] or bounding_box[3] - bounding_box[1] != fc.shape[0]:
        fc.resize((int(bounding_box[2] - bounding_box[0]), int(bounding_box[3] - bounding_box[1])))
        pfc.resize((int(bounding_box[2] - bounding_box[0]), int(bounding_box[3] - bounding_box[1])))
        print("Resized images to fit bounding box")
    while True:
        time.sleep(5)  # TODO: Delete this
        img = np.array(ImageGrab.grab(bbox=bounding_box).convert('LA'))
        structural_similarity_pfc = ssim(img, pfc, channel_axis=2)
        if restart_setting == "pfc":
            structural_similarity = structural_similarity_pfc
        else:
            structural_similarity_fc = ssim(img, fc, channel_axis=2)
            structural_similarity = max(structural_similarity_fc, structural_similarity_pfc)

        while structural_similarity > ssim_cutoff:
            time.sleep(1)
            img = np.array(ImageGrab.grab(bbox=bounding_box).convert('LA'))
            structural_similarity_pfc = ssim(img, pfc, channel_axis=2)
            if restart_setting == "pfc":
                structural_similarity = structural_similarity_pfc
            else:
                structural_similarity_fc = ssim(img, fc, channel_axis=2)
                structural_similarity = max(structural_similarity_fc, structural_similarity_pfc)

        keyboard.press(Key.esc)
        keyboard.release(Key.esc)
        time.sleep(0.2)
        keyboard.press('r')
        keyboard.release('r')
        print(structural_similarity)
        time.sleep(5)