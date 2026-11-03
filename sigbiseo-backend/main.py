from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import base64
import requests
import json
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.post("/api/v1/plant-care/analyze")
async def analyze_plant(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lon: float = Form(...)
):
    try:
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API 키가 설정되지 않았습니다.")

        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        prompt_text = """
        당신은 전문 식물 관리사(식비서)입니다.
        첨부된 식물 이미지를 정확히 식별하고, 해당 '식물 종의 고유 생장 특성' 및 '상태'에 맞춰 7일간의 주간 맞춤 케어 플랜을 작성해주세요.

        [주의사항]
        - 절대로 일반적인 공통 문구를 돌려쓰지 마세요.
        - 식물의 수분 요구량, 광량, 잎 청소, 통풍 필요성에 따라 7일간의 행동 요령(action)을 구체적으로 다르게 작성하세요.

        반드시 아래의 정확한 JSON 구조로만 답변하세요:
        {
          "species": "식물 이름 (한글 및 학명)",
          "health_score": 85,
          "status_summary": "현재 식물 상태 요약 한 줄",
          "location_advice": "이 식물 종 특성에 따른 베란다/실내 최적 위치 추천 문구",
          "weekly_plan": [
            {"day": "Day 1 (오늘)", "title": "작업 제목", "action": "이 식물 종에 특화된 1일차 관리 행동"},
            {"day": "Day 2", "title": "작업 제목", "action": "이 식물 종에 특화된 2일차 관리 행동"},
            {"day": "Day 3", "title": "작업 제목", "action": "이 식물 종에 특화된 3일차 관리 행동"},
            {"day": "Day 4", "title": "작업 제목", "action": "이 식물 종에 특화된 4일차 관리 행동"},
            {"day": "Day 5", "title": "작업 제목", "action": "이 식물 종에 특화된 5일차 관리 행동"},
            {"day": "Day 6", "title": "작업 제목", "action": "이 식물 종에 특화된 6일차 관리 행동"},
            {"day": "Day 7", "title": "작업 제목", "action": "이 식물 종에 특화된 7일차 관리 행동"}
          ]
        }
        """

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        gpt_res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()
        
        if "choices" not in gpt_res:
            raise HTTPException(status_code=500, detail="GPT API 응답 오류")

        ai_data = json.loads(gpt_res['choices'][0]['message']['content'])

        weather_data = {
            "temperature": "16.5",
            "humidity": "52",
            "sky_status": "맑음"
        }

        result = {
            "plant_analysis": {
                "species": ai_data.get("species", "알 수 없는 식물"),
                "health_score": ai_data.get("health_score", 80),
                "status_summary": ai_data.get("status_summary", "상태 정보 분석 완료.")
            },
            "weather_info": weather_data,
            "care_plan": {
                "location_advice": ai_data.get("location_advice", "☀️ 식물 특성에 맞는 광량을 확보해 주세요."),
                "weekly_plan": ai_data.get("weekly_plan", [])
            }
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))