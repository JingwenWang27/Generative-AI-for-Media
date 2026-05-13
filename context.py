import httpx
from datetime import datetime

# TODO: Insert your own API key here. 
# Personal API key has been removed for security reasons before uploading to GitHub.
OWM_API_KEY = ""
OWM_CITY    = "Bournemouth"

# 天气描述中文映射
CONDITION_MAP = {
    "Clear":        "晴天",
    "Clouds":       "多云",
    "Rain":         "下雨",
    "Drizzle":      "小雨",
    "Thunderstorm": "雷暴",
    "Snow":         "下雪",
    "Mist":         "薄雾",
    "Fog":          "大雾",
    "Haze":         "霾",
}

async def get_weather():
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={OWM_CITY}&appid={OWM_API_KEY}&units=metric"
        )
        async with httpx.AsyncClient(timeout=5) as http:
            r = await http.get(url)
            data = r.json()

        if r.status_code != 200:
            raise ValueError(data.get("message", "API error"))

        condition   = data["weather"][0]["main"]
        description = data["weather"][0]["description"]  # OWM 自带中文（lang参数可选）
        temp        = round(data["main"]["temp"])

        # 用本地映射覆盖（更可控）
        description = CONDITION_MAP.get(condition, description)

        return {"condition": condition, "temp": temp, "description": description, "city": OWM_CITY}


    except Exception as e:
        print(f"[Weather] 获取失败，使用 Mock 数据：{e}")
        return {"condition": "Clear", "temp": 18, "description": "晴天（离线）"}


def get_context(days_no_exercise: int = None):
    from database import get_days_since_exercise
    now = datetime.now()
    return {
        "hour":             now.hour,
        "weekday":          now.strftime("%A"),
        "time_str":         now.strftime("%H:%M"),
        "days_no_exercise": days_no_exercise or get_days_since_exercise()
    }
