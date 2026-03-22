# -*- coding: utf-8 -*-
"""
微信测试号天气推送 - GitHub Actions 版本
每天定时推送天气、穿衣建议、纪念日提醒
"""

import requests
import datetime
import random
import os

# ========== 配置（从环境变量读取） ==========
QWEATHER_KEY = os.environ.get("QWEATHER_KEY")
WECHAT_APPID = os.environ.get("WECHAT_APPID")
WECHAT_SECRET = os.environ.get("WECHAT_SECRET")
TEMPLATE_ID = os.environ.get("TEMPLATE_ID")
OPENID = os.environ.get("OPENID")
CITY = os.environ.get("CITY", "铜仁")
ANNIVERSARY_DATE = os.environ.get("ANNIVERSARY_DATE", "2019-04-17")

# ========== 小文案库 ==========
LOVE_NOTES = [
    "今天也要开心呀，我一直在~",
    "天气有变化，记得照顾好自己哦！",
    "想你了，今天也要好好吃饭~",
    "不管天气怎样，心情都要美美的！",
    "每天醒来第一件事，就是想你~",
    "今天也要元气满满哦！",
    "你的笑容是最好的天气~",
    "注意保暖，别让我担心~",
    "工作再忙也要记得喝水休息~",
    "你是我的小太阳，每天都闪闪发光~",
    "今天也要被我爱着哦~",
    "有你的每一天都是好天气~",
    "爱你，是我每天最重要的事~",
    "天气在变，爱你的心永远不变~"
]

# ========== 穿衣建议 ==========
def get_clothing_tips(temp_min, temp_max, weather):
    avg_temp = (temp_min + temp_max) / 2
    tips = []
    
    if avg_temp >= 30:
        tips.append("天气炎热，穿轻薄透气的衣服")
    elif avg_temp >= 25:
        tips.append("天气较热，建议穿短袖短裤")
    elif avg_temp >= 20:
        tips.append("温度适宜，薄外套+长袖即可")
    elif avg_temp >= 15:
        tips.append("有点凉，建议加件外套")
    elif avg_temp >= 10:
        tips.append("天气偏冷，穿毛衣或厚外套")
    elif avg_temp >= 5:
        tips.append("天气寒冷，注意保暖，穿羽绒服")
    else:
        tips.append("非常寒冷，务必穿厚羽绒服、戴围巾手套")
    
    if "雨" in weather:
        tips.append("记得带伞☔")
    if "雪" in weather:
        tips.append("注意路滑❄")
    if "晴" in weather:
        tips.append("适合外出晒太阳☀")
    
    return "；".join(tips)

# ========== 获取微信access_token ==========
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_SECRET}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
        else:
            print(f"获取access_token失败: {data}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

# ========== 获取和风天气 ==========
def get_weather():
    try:
        # 获取城市ID
        loc_url = f"https://geoapi.qweather.com/v2/city/lookup?location={CITY}&key={QWEATHER_KEY}"
        loc_resp = requests.get(loc_url, timeout=10)
        loc_data = loc_resp.json()
        
        if loc_data.get("code") != "200":
            print(f"获取城市ID失败: {loc_data}")
            return None
        
        location_id = loc_data["location"][0]["id"]
        city_name = loc_data["location"][0]["name"]
        
        # 获取天气
        weather_url = f"https://devapi.qweather.com/v7/weather/3d?location={location_id}&key={QWEATHER_KEY}"
        weather_resp = requests.get(weather_url, timeout=10)
        weather_data = weather_resp.json()
        
        if weather_data.get("code") != "200":
            print(f"获取天气失败: {weather_data}")
            return None
        
        today = weather_data["daily"][0]
        
        return {
            "city": city_name,
            "weather": today["textDay"],
            "temp_min": int(today["tempMin"]),
            "temp_max": int(today["tempMax"]),
            "wind": f"{today['windDir']}{today['windScale']}级"
        }
    except Exception as e:
        print(f"获取天气异常: {e}")
        return None

# ========== 计算纪念日 ==========
def get_anniversary_info():
    try:
        anniversary = datetime.datetime.strptime(ANNIVERSARY_DATE, "%Y-%m-%d")
        today = datetime.datetime.now()
        days = (today - anniversary).days
        
        next_ann = datetime.datetime(today.year, anniversary.month, anniversary.day)
        if next_ann < today:
            next_ann = datetime.datetime(today.year + 1, anniversary.month, anniversary.day)
        days_to_next = (next_ann - today).days
        
        return f"恋爱第{days}天，距下次纪念日还有{days_to_next}天"
    except:
        return "纪念日计算错误"

# ========== 发送微信模板消息 ==========
def send_template_message(token, data):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
    
    payload = {
        "touser": OPENID,
        "template_id": TEMPLATE_ID,
        "data": {
            "date": {
                "value": datetime.datetime.now().strftime("%Y年%m月%d日"),
                "color": "#173177"
            },
            "city": {
                "value": data["city"],
                "color": "#173177"
            },
            "weather": {
                "value": f"{data['weather']}，{data['wind']}",
                "color": "#FF6B6B"
            },
            "temp": {
                "value": f"{data['temp_min']}~{data['temp_max']}℃",
                "color": "#FF9500"
            },
            "tips": {
                "value": data["tips"],
                "color": "#34C759"
            },
            "anniversary": {
                "value": data["anniversary"],
                "color": "#FF2D55"
            },
            "note": {
                "value": data["note"],
                "color": "#AF52DE"
            }
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        
        if result.get("errcode") == 0:
            print("✅ 消息发送成功！")
            return True
        else:
            print(f"❌ 消息发送失败: {result}")
            return False
    except Exception as e:
        print(f"发送异常: {e}")
        return False

# ========== 主函数 ==========
def main():
    print("=" * 50)
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌤 开始执行天气推送...")
    
    # 检查配置
    if not all([QWEATHER_KEY, WECHAT_APPID, WECHAT_SECRET, TEMPLATE_ID, OPENID]):
        print("❌ 配置不完整，请检查环境变量")
        return
    
    # 1. 获取天气
    print("🌤 获取天气数据...")
    weather = get_weather()
    if not weather:
        print("❌ 获取天气失败")
        return
    print(f"   ✅ {weather['city']} | {weather['weather']} | {weather['temp_min']}~{weather['temp_max']}℃")
    
    # 2. 穿衣建议
    tips = get_clothing_tips(weather["temp_min"], weather["temp_max"], weather["weather"])
    
    # 3. 纪念日
    anniversary = get_anniversary_info()
    
    # 4. 随机文案
    note = random.choice(LOVE_NOTES)
    
    # 5. 获取token
    print("🔑 获取access_token...")
    token = get_access_token()
    if not token:
        return
    
    # 6. 发送
    print("📤 发送模板消息...")
    send_template_message(token, {
        "city": weather["city"],
        "weather": weather["weather"],
        "temp_min": weather["temp_min"],
        "temp_max": weather["temp_max"],
        "tips": tips,
        "anniversary": anniversary,
        "note": note
    })
    
    print("=" * 50)

if __name__ == "__main__":
    main()
