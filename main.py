from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import init_db, log_exercise, get_days_since_exercise
from context import get_context, get_weather
from ai_engine import get_ai_response, get_reminder, client, DOUBAO_VISION_MODEL
import sqlite3, os, shutil, uuid, base64, json

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

init_db()
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def init_wardrobe_db():
    conn = sqlite3.connect("wardrobe.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            color TEXT,
            temp_min REAL NOT NULL,
            temp_max REAL NOT NULL,
            image_path TEXT,
            style TEXT,
            material TEXT,
            layerable TEXT,
            warmth REAL
        )
    """)
    conn.commit()
    conn.close()

init_wardrobe_db()

@app.get("/", response_class=HTMLResponse)
async def root():
    return open("index.html").read()

@app.post("/chat")
async def chat(body: dict):
    weather = await get_weather()
    context = get_context()
    reply = await get_ai_response(body["message"], context, weather)
    return {"reply": reply, "weather": weather, "context": context}

@app.get("/remind")
async def remind(days_no_exercise: int = 3, sitting_hours: int = 0):
    weather = await get_weather()
    reminder = await get_reminder(days_no_exercise, sitting_hours, weather)
    return {"reminder": reminder}

@app.post("/log/exercise")
async def log(body: dict):
    log_exercise(body.get("type", "运动"), body.get("duration", 30))
    return {"status": "ok", "message": "运动记录已保存"}

@app.get("/status")
async def status():
    return {
        "days_no_exercise": get_days_since_exercise(),
        "weather": await get_weather()
    }

@app.post("/wardrobe/analyze-image")
async def analyze_clothing_image(image: UploadFile = File(...)):
    contents = await image.read()
    b64 = base64.b64encode(contents).decode("utf-8")
    ext = (image.filename or "jpg").split(".")[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    prompt = """请分析这张衣物图片，严格按以下JSON格式返回，不要有任何多余文字或markdown：
{
  "name": "根据衣物风格生成简洁名字，如'米白宽松卫衣'",
  "category": "只能是以下之一：背心/短袖T恤/T恤/长袖衬衫/卫衣/薄外套/厚外套/羽绒服/上衣/短裤/牛仔裤/厚裤子/裤子",
  "style": "衣物风格，如：休闲/正式/运动/街头/简约/复古",
  "color": "主要颜色",
  "material": "材质，如：棉/涤纶/牛仔/羊毛/羽绒/麻/混纺",
  "layerable": "是否适合叠穿，只能填：是 或 否",
  "warmth": 保暖度数字,
  "temp_min": 适合最低温度数字,
  "temp_max": 适合最高温度数字
}"""
    try:
        response = client.chat.completions.create(
            model=DOUBAO_VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mime};base64,{b64}"
                    }}
                ]
            }],
            max_tokens=600
        )
        result_text = response.choices[0].message.content.strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)
        return result
    except json.JSONDecodeError:
        return {"error": "AI返回格式异常，请手动填写", "raw": result_text}
    except Exception as e:
        return {"error": f"识别失败：{str(e)}"}

@app.get("/wardrobe/list")
async def wardrobe_list(category: str = ""):
    conn = sqlite3.connect("wardrobe.db")
    if category:
        rows = conn.execute(
            "SELECT id,name,category,color,temp_min,temp_max,image_path,style,material,layerable,warmth FROM clothes WHERE category=?",
            (category,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id,name,category,color,temp_min,temp_max,image_path,style,material,layerable,warmth FROM clothes"
        ).fetchall()
    conn.close()
    items = [{
        "id": r[0], "name": r[1], "category": r[2], "color": r[3],
        "temp_min": r[4], "temp_max": r[5], "image_path": r[6],
        "style": r[7], "material": r[8], "layerable": r[9], "warmth": r[10]
    } for r in rows]
    return {"items": items}

@app.post("/wardrobe/add")
async def wardrobe_add(
    name: str = Form(...),
    category: str = Form(...),
    color: str = Form(""),
    temp_min: float = Form(...),
    temp_max: float = Form(...),
    style: str = Form(""),
    material: str = Form(""),
    layerable: str = Form(""),
    warmth: float = Form(0),
    image: UploadFile = File(None)
):
    image_path = None
    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"uploads/{uuid.uuid4().hex}.{ext}"
        with open(filename, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = filename
    conn = sqlite3.connect("wardrobe.db")
    conn.execute(
        "INSERT INTO clothes (name,category,color,temp_min,temp_max,image_path,style,material,layerable,warmth) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (name, category, color, temp_min, temp_max, image_path, style, material, layerable, warmth)
    )
    conn.commit()
    conn.close()
    return {"message": f"✅ {name} 已添加到衣橱"}

@app.get("/wardrobe/recommend")
async def wardrobe_recommend():
    weather = await get_weather()
    temp = weather.get("temp", 20)
    conn = sqlite3.connect("wardrobe.db")
    rows = conn.execute(
        "SELECT id,name,category,color,temp_min,temp_max,image_path,style,material,layerable,warmth FROM clothes"
    ).fetchall()
    conn.close()
    tops_cat    = ["背心","短袖T恤","T恤","长袖衬衫","卫衣","薄外套","厚外套","羽绒服","上衣"]
    bottoms_cat = ["短裤","牛仔裤","厚裤子","裤子"]
    def to_dict(r):
        return {"id":r[0],"name":r[1],"category":r[2],"color":r[3],
                "temp_min":r[4],"temp_max":r[5],"image_path":r[6],
                "style":r[7],"material":r[8],"layerable":r[9],"warmth":r[10]}
    tops    = [to_dict(r) for r in rows if r[2] in tops_cat    and r[4] <= temp <= r[5]]
    bottoms = [to_dict(r) for r in rows if r[2] in bottoms_cat and r[4] <= temp <= r[5]]
    return {
        "temp": temp,
        "tip": f"当前气温 {temp}°C，为你推荐以下穿搭",
        "tops": tops[:2],
        "bottoms": bottoms[:2]
    }

@app.delete("/wardrobe/{item_id}")
async def wardrobe_delete(item_id: int):
    conn = sqlite3.connect("wardrobe.db")
    conn.execute("DELETE FROM clothes WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": "已删除"}

@app.put("/wardrobe/{item_id}")
async def wardrobe_update(
    item_id: int,
    name: str = Form(...),
    category: str = Form(...),
    color: str = Form(""),
    temp_min: float = Form(...),
    temp_max: float = Form(...),
    style: str = Form(""),
    material: str = Form(""),
    layerable: str = Form(""),
    warmth: float = Form(0),
    image: UploadFile = File(None)
):
    conn = sqlite3.connect("wardrobe.db")
    existing = conn.execute("SELECT image_path FROM clothes WHERE id=?", (item_id,)).fetchone()
    if not existing:
        conn.close()
        return {"error": "未找到该衣物"}
    image_path = existing[0]
    if image and image.filename:
        ext = image.filename.split(".")[-1]
        filename = f"uploads/{uuid.uuid4().hex}.{ext}"
        with open(filename, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = filename
    conn.execute(
        "UPDATE clothes SET name=?,category=?,color=?,temp_min=?,temp_max=?,style=?,material=?,layerable=?,warmth=?,image_path=? WHERE id=?",
        (name, category, color, temp_min, temp_max, style, material, layerable, warmth, image_path, item_id)
    )
    conn.commit()
    conn.close()
    return {"message": f"✅ {name} 已更新"}
