import json
from loguru import logger
from fastapi import FastAPI
from pydantic import BaseModel
import yaml
from PIL import ImageGrab
import base64
import requests
import io
import asyncio
import os
import time

# 日志目录
log_path = "logs"
os.makedirs(log_path, exist_ok=True)

# 配置日志
log_path_error = os.path.join(log_path, "error_{time:YYYY-MM-DD}.log")
logger.add(
    log_path_error,
    rotation="12:00",  # 每天中午 12:00 创建新文件
    retention="5 days",  # 保留最近 5 天的日志
    enqueue=True,  # 异步写入
    level="ERROR",  # 只记录 ERROR 级别及以上的日志
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"  # 日志格式
)

app = FastAPI()
show_log = False
class RegionData(BaseModel):
    name: str
    left: int
    top: int
    width: int
    height: int

# 全局变量，用于存储截图数据
screenshot_data = {}

def get_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

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

def ocr_screenshot(base64_image,url):
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

async def update_screenshot_data():
    while True:
        config = get_config()
        regions = config['regions']
        ocr_url = config['ocr_url']
        global show_log
        show_log = config['show_log']
        for region in regions:
            region_name, base64_image = capture_screenshot(region)
            result = ocr_screenshot(base64_image,ocr_url)
            logger.info(f" 截图结果 {region_name} : {result}")  # 打印OCR结果
            screenshot_data[region_name] = result
            time.sleep(0.1)
        await asyncio.sleep(5)  # 等待5秒

async def start_background_task():
    asyncio.create_task(update_screenshot_data())

@app.get("/screenshot_data")
async def read_screenshot_data():
    return screenshot_data

if __name__ == '__main__':
    import uvicorn
    app.add_event_handler("startup", start_background_task)
    uvicorn.run(app, host="0.0.0.0", port=8000)