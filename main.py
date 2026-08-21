import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# .env 파일 불러오기
load_dotenv()

# API Key 가져오기
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=api_key)


def generate_brand_result():
    """
    브랜드 정보를 AI에게 요청하고
    JSON 형식의 브랜드 결과를 반환합니다.
    """

    prompt = """
다음 조건에 맞는 비건 화장품 브랜드를 기획해주세요.

산업:
뷰티 / 비건 화장품

타깃 고객:
민감성 피부를 가진 20~40대 여성 및
화장품 성분을 꼼꼼히 확인하는 클린뷰티 소비자

핵심 키워드:
순함, 자연주의, 투명함, 힐링, 프리미엄

브랜드 콘셉트:
자연 그대로의 순수한 원료로
피부 본연의 건강함을 되찾아주는 비건 스킨케어

브랜드 컬러:
핑크 베이지를 중심으로 한 자연스럽고 고급스러운 색상

다음 JSON 형식으로만 답변해주세요.

{
  "names": [
    {
      "name": "브랜드명",
      "meaning": "브랜드명의 의미"
    }
  ],
  "slogans": [
    "슬로건 1",
    "슬로건 2",
    "슬로건 3"
  ],
  "story": "브랜드 스토리",
  "colors": {
    "main": "#000000",
    "sub": [
      "#000000",
      "#000000"
    ]
  }
}

주의사항:
- names에는 브랜드명 3개를 제안해주세요.
- 각 브랜드명에는 meaning을 작성해주세요.
- slogans는 3개를 제안해주세요.
- story는 브랜드의 철학과 타깃 고객을 반영해주세요.
- main은 핑크 베이지 계열의 HEX 색상을 사용해주세요.
- sub에는 main과 잘 어울리는 색상 2개를 사용해주세요.
- JSON 이외의 설명은 절대 작성하지 마세요.
"""

    response = client.responses.create(
        model="gpt-5",
        input=prompt
    )

    result_text = response.output_text

    return json.loads(result_text)


if __name__ == "__main__":

    brand_result = generate_brand_result()

    print(json.dumps(
        brand_result,
        ensure_ascii=False,
        indent=2
    ))