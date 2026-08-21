import base64
import os

from dotenv import load_dotenv
from openai import OpenAI


# .env 파일 불러오기
load_dotenv()

# API Key 가져오기
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

# OpenAI 클라이언트
client = OpenAI(api_key=api_key)


# 이미지 생성
response = client.images.generate(
    model="gpt-image-2",
    prompt="""
Create a premium vegan skincare product advertising image.

Visual concept:
A sophisticated Korean clean beauty brand,
soft pink beige color palette,
natural ingredients,
gentle and healing atmosphere,
minimal and elegant cosmetic packaging,
premium but affordable feeling,
warm natural lighting,
soft shadows,
clean ivory background.

Target audience:
Modern women in their 20s and 30s.

No people.
No famous brands.
No existing logos.
Professional cosmetic advertising photography.
""",
    size="1024x1024",
    quality="medium",
    output_format="png",
    n=1
)


# 생성된 이미지 데이터 가져오기
image_data = response.data[0].b64_json

# Base64 → 이미지 파일로 변환
image_bytes = base64.b64decode(image_data)

# output 폴더에 저장
output_path = "output/test_image.png"

with open(output_path, "wb") as f:
    f.write(image_bytes)

print("이미지 생성 완료!")
print(f"저장 위치: {output_path}")