from openai import OpenAI
import base64
import json
import re

# TODO: Insert your own API key here. 
# Personal API key has been removed for security reasons before uploading to GitHub.
DOUBAO_API_KEY = ""
DOUBAO_MODEL   = "Doubao-1.5-vision-pro-32k"
DOUBAO_VISION_MODEL = ""

client = OpenAI(
    api_key=DOUBAO_API_KEY,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

def build_prompt(context: dict, weather: dict) -> str:
    return f"""You are HealthMate, a warm health coach.
Time: {context['time_str']}, {context['weekday']}
Weather: {weather['condition']}, {weather['temp']}°C
Days since last exercise: {context['days_no_exercise']}
Reply in Chinese, 2-3 sentences, friendly and specific."""

async def get_ai_response(message: str, context: dict, weather: dict) -> str:
    prompt = build_prompt(context, weather)
    try:
        response = client.chat.completions.create(
            model=DOUBAO_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",   "content": message}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 暂时不可用：{str(e)}"

async def get_reminder(days_no_exercise: int, sitting_hours: int, weather: dict) -> str:
    prompt = f"""你是健康助手，用中文给出一条简短运动提醒（不超过60字）。
天气：{weather['condition']} {weather['temp']}°C，已{days_no_exercise}天未运动，久坐{sitting_hours}小时。"""
    try:
        response = client.chat.completions.create(
            model=DOUBAO_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 暂时不可用：{str(e)}"

async def analyze_food_image(image_bytes: bytes) -> dict:
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model=DOUBAO_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        },
                        {
                            "type": "text",
                            "text": "请识别图片中的食物，用JSON格式返回，不要加任何多余文字：{\"food_name\": \"食物名称\", \"calories\": 卡路里整数, \"protein\": 蛋白质克数, \"carbs\": 碳水克数, \"fat\": 脂肪克数, \"description\": \"简短描述\"}"
                        }
                    ]
                }
            ],
            extra_body={"thinking": {"type": "disabled"}}
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "解析失败", "raw": content}
    except Exception as e:
        return {"error": str(e)}

async def analyze_clothing_image(image_bytes: bytes) -> dict:
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model=DOUBAO_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        },
                        {
                            "type": "text",
                            "text": "请识别图片中的衣物，用JSON格式返回，不要加任何多余文字：{\"clothing_type\": \"衣物类型\", \"color\": \"主要颜色\", \"style\": \"风格\", \"season\": \"适合季节\", \"description\": \"简短描述\"}"
                        }
                    ]
                }
            ],
            extra_body={"thinking": {"type": "disabled"}}
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "解析失败", "raw": content}
    except Exception as e:
        return {"error": str(e)}
