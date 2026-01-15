import json
import apscheduler
from apscheduler.triggers.cron import CronTrigger

from apscheduler.schedulers.background import BackgroundScheduler
import logging
from logging.handlers import TimedRotatingFileHandler

from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask, jsonify
import yaml
from PIL import ImageGrab
import base64
import requests
import io
import os
import time
from datetime import datetime


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
    return os.path.join(log_path, "{}_{}.log".format(base_name, today))  # 使用 str.format() 替换 f-string

# 配置 INFO 日志文件
info_handler = TimedRotatingFileHandler(
    get_log_filename("INFO"),
    when="midnight",  # 每天午夜创建新文件
    interval=1,
    backupCount=10,  # 保留最近 10 天的日志
)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
info_handler.addFilter(lambda record: record.levelno == logging.INFO)  # 只记录 INFO 级别的日志
logger.addHandler(info_handler)

# 配置 WARN 日志文件
warn_handler = TimedRotatingFileHandler(
    get_log_filename("WARN"),
    when="midnight",  # 每天午夜创建新文件
    interval=1,
    backupCount=10,  # 保留最近 10 天的日志
)
warn_handler.setLevel(logging.WARNING)
warn_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
warn_handler.addFilter(lambda record: record.levelno == logging.WARNING)  # 只记录 WARN 级别的日志
logger.addHandler(warn_handler)

app = Flask(__name__)
show_log = False

# 全局变量，用于存储截图数据
screenshot_data = {}

def get_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

# @scheduler.scheduled_job('cron', minute='00,10,20,30,40,50', second='20')
def sync_data():
    logger.warning(screenshot_data)

def capture_screenshot(region):
    left, top, width, height = region['left'], region['top'], region['width'], region['height']
    screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    image_file = "images/{}.png".format(region['name'])  # 使用 str.format() 替换 f-string
    image_path = os.path.join(os.getcwd(), "images")
    os.makedirs(image_path, exist_ok=True)
    screenshot.save(image_file)
    with io.BytesIO() as buffer:
        screenshot.save(buffer, format="PNG")
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return region['name'], screenshot_base64

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
        logger.info(" {}".format(result))  # 使用 str.format() 替换 f-string
    if result['code'] == 100:
        res = result['data']
    return res

def update_screenshot_data():
    config = get_config()
    regions = config['regions']
    ocr_url = config['ocr_url']
    global show_log
    show_log = config['show_log']
    for region in regions:
        try:
            region_name, base64_image = capture_screenshot(region)
            result = ocr_screenshot(base64_image, ocr_url)
            logger.info(" 截图结果 {} : {}".format(region_name, result))  # 使用 str.format() 替换 f-string
            screenshot_data[region_name] = result
            time.sleep(0.1)
        except Exception as e:
            logger.error("获取截图失败: {}".format(e))  # 使用 str.format() 替换 f-string
            screenshot_data[region['name']] = -1

@app.route("/screenshot_data", methods=["GET"])
def read_screenshot_data():
    return jsonify(screenshot_data)

if __name__ == '__main__':
    scheduler.add_job(sync_data, CronTrigger(minute='00,10,20,30,40,50', second='20'))
    scheduler.add_job(update_screenshot_data, IntervalTrigger(seconds=30))
    scheduler.start()
    app.run(host="0.0.0.0", port=8000)