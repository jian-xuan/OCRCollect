import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import json
import io
from PIL import ImageGrab
import base64

def testOne():
    # 自定义截图区域的坐标和大小
    left = 69
    top = 208
    width = 216
    height = 102

    # 截图
    screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    image_file = 'screenshot.png'
    screenshot.save(image_file)

    # 将截图转换为base64编码
    with io.BytesIO() as buffer:
        screenshot.save(buffer, format="PNG")
        screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # 打印base64编码的字符串
    # print(screenshot_base64)

    url = "http://127.0.0.1:1224/api/ocr"
    data = {
        "base64": screenshot_base64,
        # 可选参数示例
        "options": {
            "data.format": "text",
        }
    }
    headers = {"Content-Type": "application/json"}
    data_str = json.dumps(data)
    response = requests.post(url, data=data_str, headers=headers)
    response.raise_for_status()
    res_dict = json.loads(response.text)
    print(res_dict)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=100) as executor:
        for _ in range(1000):
            futures = executor.submit(testOne)
    # 多线程启动
    # for i in range(100):
    #     testOne()
    #     time.sleep(0.01)