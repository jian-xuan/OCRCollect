import json
from apscheduler.triggers.cron import CronTrigger

from apscheduler.schedulers.background import BackgroundScheduler
import logging
from logging.handlers import TimedRotatingFileHandler

from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, jsonify
import yaml
from PIL import ImageGrab, Image
import base64
import requests
import io
import os
import time
from datetime import datetime
import numpy as np
import cv2
import pyautogui
import threading


scheduler = BackgroundScheduler()

# 日志目录
log_path = "logs"
os.makedirs(log_path, exist_ok=True)

# 配置日志
logger = logging.getLogger("my_logger")
logger.setLevel(logging.INFO)

# 配置控制台日志
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(console_handler)

# 自定义日志文件名（按天区分）
def get_log_filename(base_name):
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_path, "{}_{}.log".format(base_name, today))

# 配置 INFO 日志文件
info_handler = TimedRotatingFileHandler(
    get_log_filename("INFO"),
    when="midnight",
    interval=1,
    backupCount=10,
)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
info_handler.addFilter(lambda record: record.levelno == logging.INFO)
logger.addHandler(info_handler)

# 配置 WARN 日志文件
warn_handler = TimedRotatingFileHandler(
    get_log_filename("WARN"),
    when="midnight",
    interval=1,
    backupCount=10,
)
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
warn_handler.addFilter(lambda record: record.levelno == logging.WARNING)
logger.addHandler(warn_handler)

app = Flask(__name__)
show_log = False

# 全局变量，用于存储截图数据
screenshot_data = {}

def get_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

def sync_data():
    logger.warning(screenshot_data)

def capture_screenshot(region):
    left, top, width, height = region['left'], region['top'], region['width'], region['height']
    screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    image_file = "images/{}.png".format(region['name'])
    image_path = os.path.join(os.getcwd(), "images")
    os.makedirs(image_path, exist_ok=True)
    screenshot.save(image_file)
    with io.BytesIO() as buffer:
        screenshot.save(buffer, format="PNG")
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return region['name'], screenshot_base64

def capture_all_screenshot():
    bbox = None
    name = "fullscreen"
    screenshot = ImageGrab.grab(bbox=bbox)
    image_file = "images/{}.png".format(name)
    image_path = os.path.join(os.getcwd(), "images")
    os.makedirs(image_path, exist_ok=True)
    screenshot.save(image_file)
    with io.BytesIO() as buffer:
        screenshot.save(buffer, format="PNG")
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return name, screenshot_base64

def ocr_screenshot(base64_image, url):
    data = {
        "base64": base64_image,
        "options": {
            "data.format": "text",
        }
    }
    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(data)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    result = json.loads(response.text)
    res = -1
    if show_log:
        logger.info(" {}".format(result))
    if result['code'] == 100:
        res = result['data']
    return res

def pil_to_cv2(img):
    """将PIL图片转换为OpenCV格式(BGR)"""
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def find_template_opencv(screenshot, template, threshold=0.8):
    """使用OpenCV进行快速模板匹配"""
    try:
        # 转换为OpenCV格式
        screenshot_cv = pil_to_cv2(screenshot)
        template_cv = pil_to_cv2(template)
        
        # 使用归一化相关系数匹配
        result = cv2.matchTemplate(screenshot_cv, template_cv, cv2.TM_CCOEFF_NORMED)
        
        # 获取最佳匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        is_match = max_val >= threshold
        return is_match, max_val, max_loc
    except Exception as e:
        logger.debug("OpenCV匹配失败: {}".format(e))
        return False, 0, None

def find_template_pyautogui(screenshot, template_path, region, confidence=0.8):
    """使用pyautogui进行模板匹配（备用方案）"""
    try:
        # 保存临时截图供pyautogui使用
        temp_screenshot = "images/temp_screenshot.png"
        screenshot.save(temp_screenshot)
        
        # 使用pyautogui在指定区域查找
        pos = pyautogui.locateOnScreen(
            template_path,
            region=region,
            confidence=confidence
        )
        
        if pos:
            return True, 1.0, (pos.left, pos.top)
        return False, 0, None
    except Exception as e:
        logger.debug("pyautogui匹配失败: {}".format(e))
        return False, 0, None

def detect_button_state(button_config):
    """检测按钮状态，优先使用OpenCV快速匹配，失败时回退到pyautogui"""
    threshold = button_config.get('threshold', 0.8)
    timeout = button_config.get('timeout', 3)
    interval = button_config.get('interval', 0.1)
    use_opencv = button_config.get('use_opencv', True)  # 默认使用OpenCV
    
    # 计算region参数（用于pyautogui）
    region = (button_config['left'], button_config['top'],
              button_config['width'], button_config['height'])

    try:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 截取按钮区域
            screenshot = ImageGrab.grab(bbox=(button_config['left'], button_config['top'], 
                                              button_config['left'] + button_config['width'], 
                                              button_config['top'] + button_config['height']))
            
            # 保存截图
            image_file = "images/{}.png".format(button_config['name'])
            screenshot.save(image_file)
            
            on_match = off_match = False
            on_sim = off_sim = 0
            on_pos = off_pos = None
            
            try:
                if use_opencv:
                    # 方法1: 使用OpenCV快速匹配
                    on_image = Image.open(button_config['on_image'])
                    off_image = Image.open(button_config['off_image'])
                    
                    on_match, on_sim, on_pos = find_template_opencv(screenshot, on_image, threshold)
                    off_match, off_sim, off_pos = find_template_opencv(screenshot, off_image, threshold)
                    
                    match_method = "OpenCV"
                else:
                    # 方法2: 使用pyautogui匹配
                    on_match, on_sim, on_pos = find_template_pyautogui(
                        screenshot, button_config['on_image'], region, threshold
                    )
                    off_match, off_sim, off_pos = find_template_pyautogui(
                        screenshot, button_config['off_image'], region, threshold
                    )
                    
                    match_method = "pyautogui"
                
                logger.info("按钮 {} 搜索 [{}] - 开: {:.2%} at {}, 关: {:.2%} at {}".format(
                    button_config['name'], 
                    match_method,
                    on_sim, on_pos if on_pos else "N/A",
                    off_sim, off_pos if off_pos else "N/A"
                ))
                
                # 判断状态
                if on_match or off_match:
                    if on_sim > off_sim:
                        logger.info("按钮 {} 匹配到开状态 [{}] (相似度: {:.2%})".format(
                            button_config['name'], match_method, on_sim))
                        return 1
                    else:
                        logger.info("按钮 {} 匹配到关状态 [{}] (相似度: {:.2%})".format(
                            button_config['name'], match_method, off_sim))
                        return 0
                
            except Exception as e:
                logger.debug("匹配失败: {}".format(e))
            
            time.sleep(interval)
        
        logger.warning("按钮 {} 在 {} 秒内未匹配到任何状态".format(button_config['name'], timeout))
        return -1
    except Exception as e:
        logger.error("按钮检测失败: {}".format(e))
        return -1


def update_screenshot_data():
    config = get_config()
    regions = config['regions']
    buttons = config.get('buttons', [])
    ocr_url = config['ocr_url']
    global show_log
    show_log = config['show_log']
    for region in regions:
        try:
            region_name, base64_image = capture_screenshot(region)
            result = ocr_screenshot(base64_image, ocr_url)
            logger.info(" 截图结果 {} : {}".format(region_name, result))
            screenshot_data[region_name] = result
            time.sleep(0.1)
        except Exception as e:
            logger.error("获取截图失败: {}".format(e))
            screenshot_data[region['name']] = -1

    for button in buttons:
        try:
            result = detect_button_state(button)
            logger.info(" 按钮状态 {} : {}".format(button['name'], result))
            screenshot_data[button['name']] = result
            time.sleep(0.1)
        except Exception as e:
            logger.error("检测按钮失败: {}".format(e))
            screenshot_data[button['name']] = -1

    name, base64_image = capture_all_screenshot()
    screenshot_data['image'] = base64_image

@app.route("/screenshot_data", methods=["GET"])
def read_screenshot_data():
    return jsonify(screenshot_data)

def run_initial_task():
    """在后台线程中执行初始任务"""
    time.sleep(2)  # 等待API服务器启动
    logger.info("启动时立即执行一次数据更新...")
    try:
        update_screenshot_data()
    except Exception as e:
        logger.error("初始任务执行失败: {}".format(e))

if __name__ == '__main__':
    scheduler.add_job(sync_data, CronTrigger(minute='00,10,20,30,40,50', second='20'))
    scheduler.add_job(update_screenshot_data, IntervalTrigger(seconds=30))
    scheduler.start()
    
    # 在后台线程中执行初始任务，不阻塞API服务器启动
    initial_thread = threading.Thread(target=run_initial_task, daemon=True)
    initial_thread.start()
    
    app.run(host="0.0.0.0", port=8000)
