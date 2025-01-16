import json
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from flask import Flask, jsonify
import yaml
from PIL import ImageGrab
import base64
import requests
import io
import os
import time

scheduler = BackgroundScheduler()
# 日志目录
log_path = "logs"
os.makedirs(log_path, exist_ok=True)

# 配置日志
# 配置 INFO 日志文件
log_path_info = os.path.join(log_path, "INFO_{time:YYYY-MM-DD}.log")
logger.add(
    log_path_info,
    rotation="12:00",  # 每天中午 12:00 创建新文件
    retention="10 days",  # 保留最近 10 天的日志
    enqueue=True,  # 异步写入
    level="INFO",  # 只记录 INFO 级别及以上的日志
    filter=lambda record: record["level"].name == "INFO",  # 只记录 INFO 级别的日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"  # 日志格式
)

# 配置 WARN 日志文件
log_path_warn = os.path.join(log_path, "data_{time:YYYY-MM-DD}.log")
logger.add(
    log_path_warn,
    rotation="12:00",  # 每天中午 12:00 创建新文件
    retention="10 days",  # 保留最近 10 天的日志
    enqueue=True,  # 异步写入
    level="WARNING",  # 只记录 WARN 级别及以上的日志
    filter=lambda record: record["level"].name == "WARNING",  # 只记录 WARN 级别的日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"  # 日志格式
)

app = Flask(__name__)
show_log = False

# 全局变量，用于存储截图数据
screenshot_data = {}

def get_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config

@scheduler.scheduled_job('cron', minute='00,10,20,30,40,50', second='20')
def sync_data():
    logger.warning(screenshot_data)

def capture_screenshot(region):
    left, top, width, height = region['left'], region['top'], region['width'], region['height']
    screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    image_file = f"images/{region['name']}.png"
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
        logger.info(f" {result}")
    if result['code'] == 100:
        res = result['data']
    return res

def update_screenshot_data():
    while True:
        config = get_config()
        regions = config['regions']
        ocr_url = config['ocr_url']
        global show_log
        show_log = config['show_log']
        for region in regions:
            try:
                region_name, base64_image = capture_screenshot(region)
                result = ocr_screenshot(base64_image, ocr_url)
                logger.info(f" 截图结果 {region_name} : {result}")  # 打印OCR结果
                screenshot_data[region_name] = result
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"获取截图失败: {e}")
        time.sleep(5)  # 等待5秒

@app.route("/screenshot_data", methods=["GET"])
def read_screenshot_data():
    return jsonify(screenshot_data)

if __name__ == '__main__':
    scheduler.start()
    import threading
    threading.Thread(target=update_screenshot_data, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)