**Project:** HealthMate — A Multimodal Generative AI Prototype for Personalised Lifestyle Media
**Author:** Jingwen Wang
**File Source:** `ai_engine.py`
**Date:** May 2026

---

## Prompt 1 — AI Advisor (Conversational Lifestyle Coach)

**Function:** Generates a short, context-aware lifestyle response based on the user's current time, weather, and exercise history.
**Location:** `ai_engine.py` → `build_prompt()` + `get_ai_response()`
**Model:** Doubao-1.5-vision-pro-32k (Volcano Engine Ark API)
**Call Type:** Text-only chat completion

**System Prompt (dynamically constructed):**
```
You are HealthMate, a warm health coach.
Time: {time_str}, {weekday}
Weather: {weather_condition}, {temp}°C
Days since last exercise: {days_no_exercise}
Reply in Chinese, 2-3 sentences, friendly and specific.
```

**User Prompt:**
```
[User's free-text message, e.g. "今天适合运动吗？"]
```

**Example Output:**
```
今天天气晴朗，气温适宜，非常适合户外运动！
你已经3天没有运动了，建议今晚去散步30分钟，
既能放松心情，也能帮助消耗热量。加油！
```

**Design Notes:**
- Context package (time, weekday, weather, exercise gap) is injected into the system prompt at runtime
- Response is capped at 2–3 sentences to keep output concise
- The advisor is **stateless** — no long-term chat history is preserved, reducing privacy risk
- Language is fixed to Chinese for target user consistency

---

## Prompt 2 — Sedentary / Exercise Reminder

**Function:** Generates a short behavioural nudge based on sedentary hours and days without exercise.
**Location:** `ai_engine.py` → `get_reminder()`
**Model:** Doubao-1.5-vision-pro-32k
**Call Type:** Text-only chat completion

**User Prompt (dynamically constructed):**
```
你是健康助手，用中文给出一条简短运动提醒（不超过60字）。
天气：{weather_condition} {temp}°C，
已{days_no_exercise}天未运动，久坐{sitting_hours}小时。
```

**Example Output:**
```
你已久坐4小时，3天没运动啦！
现在天气晴好，出去走走吧，哪怕10分钟也很有效果！
```

**Design Notes:**
- Output is strictly limited to 60 Chinese characters to avoid over-generation
- Framed as a **general behavioural nudge**, not medical advice
- No system prompt used — single user-turn call to keep it lightweight
- Weather context is injected to make the reminder feel situationally relevant

---

## Prompt 3 — Food Image Analysis

**Function:** Identifies food items from an uploaded image and returns structured nutritional metadata.
**Location:** `ai_engine.py` → `analyze_food_image()`
**Model:** Doubao-1.5-vision-pro-32k (Vision)
**Call Type:** Multimodal — image (base64) + text prompt

**User Prompt:**
```
请识别图片中的食物，用JSON格式返回，不要加任何多余文字：
{
  "food_name": "食物名称",
  "calories": 卡路里整数,
  "protein": 蛋白质克数,
  "carbs": 碳水克数,
  "fat": 脂肪克数,
  "description": "简短描述"
}
```

**Image Input:** JPEG image encoded as base64, passed via `data:image/jpeg;base64,{b64}`

**Example Output:**
```json
{
  "food_name": "番茄炒蛋",
  "calories": 180,
  "protein": 8,
  "carbs": 12,
  "fat": 10,
  "description": "家常菜，营养均衡，热量适中"
}
```

**Design Notes:**
- Prompt explicitly instructs the model to return **only JSON**, no markdown or explanation
- `re.search(r'\{.*\}', content, re.DOTALL)` is used as a fallback parser in case the model wraps output in extra text
- `"thinking": {"type": "disabled"}` is passed in `extra_body` to suppress chain-of-thought output and reduce latency
- If JSON parsing fails, the system returns `{"error": "解析失败", "raw": content}` for debugging

---

## Prompt 4 — Clothing Image Analysis

**Function:** Identifies garment attributes from an uploaded image and returns structured wardrobe metadata.
**Location:** `ai_engine.py` → `analyze_clothing_image()`
**Model:** Doubao-1.5-vision-pro-32k (Vision)
**Call Type:** Multimodal — image (base64) + text prompt

**User Prompt:**
```
请识别图片中的衣物，用JSON格式返回，不要加任何多余文字：
{
  "clothing_type": "衣物类型",
  "color": "主要颜色",
  "style": "风格",
  "season": "适合季节",
  "description": "简短描述"
}
```

**Image Input:** JPEG image encoded as base64, passed via `data:image/jpeg;base64,{b64}`

**Example Output:**
```json
{
  "clothing_type": "针织毛衣",
  "color": "米白色",
  "style": "休闲",
  "season": "秋冬",
  "description": "宽松版型，适合日常穿搭"
}
```

**Design Notes:**
- Same structured JSON extraction pattern as food analysis
- Output is displayed in an **editable form** before saving — users can correct any inaccurate attributes
- Fallback to manual entry if JSON parsing fails, preserving the human-in-the-loop design
- `"thinking": {"type": "disabled"}` suppresses reasoning output for cleaner JSON responses

---

## Critical Reflection on Prompt Design

| **Prompt** | **What Worked Well** | **Limitations Observed** |
|---|---|---|
| AI Advisor | Context injection produced relevant, natural responses | Stateless design limits long-term personalisation |
| Sedentary Reminder | Concise, non-medical framing achieved consistently | Generic output; lacks individual preference awareness |
| Food Image Analysis | JSON schema enforced structured output reliably | Nutritional values are estimates, not clinically verified |
| Clothing Image Analysis | Category and colour recognition accurate in good lighting | Material and warmth attributes remain subjective and uncertain |

**Overall Design Principle:** All prompts in HealthMate are designed to constrain model output to structured, reviewable formats. This reflects the project's core argument that generative AI should function as an assistive layer — not an autonomous decision-maker.

---
---

