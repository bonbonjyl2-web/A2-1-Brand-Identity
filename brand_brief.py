import os
import json
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# 사용할 모델 (.env에서 OPENAI_MODEL로 변경 가능)
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =====================================================================
# 1. Structured Output을 위한 Pydantic 데이터 스키마 정의
# =====================================================================

class BrandName(BaseModel):
    """브랜드명 후보 하나와 그 이름에 담긴 의미"""
    name: str = Field(description="브랜드명 후보 (예: Blooming)")
    meaning: str = Field(description="이름에 담긴 의미나 유래 (예: 자연에서 피어나는 아름다움)")

class BrandColors(BaseModel):
    """브랜드 컬러 팔레트 (메인 1색 + 서브 2색)"""
    main: str = Field(description="브랜드 메인 컬러의 HEX 코드 (예: #2E7D32)")
    sub: List[str] = Field(description="메인 컬러를 뒷받침하는 서브 컬러 HEX 코드 2개 (예: [#81C784, #E8F5E9])")

class BrandGenerationResult(BaseModel):
    """최종적으로 생성될 브랜드 아이덴티티 정보의 스키마 구조"""
    names: List[BrandName] = Field(description="브랜드명 후보 3개")
    slogans: List[str] = Field(description="브랜드 아이덴티티와 방향성을 담은 슬로건 3개")
    story: str = Field(description="브랜드의 탄생 배경, 철학, 지향점을 서술하는 브랜드 스토리")
    colors: BrandColors = Field(description="브랜드 디자인에 사용될 대표 컬러 정보")

# =====================================================================
# 2. 브랜드 텍스트 생성 함수 정의
# =====================================================================

def generate_brand_text(brief: dict) -> dict:
    """
    브랜드 브리프 정보를 입력받아 OpenAI API를 통해 매력적인 브랜드 아이덴티티를 생성합니다.

    Args:
        brief (dict): industry / target / keywords / tone / competitors / notes 키를 갖는 딕셔너리
                      (target_audience, concept 라는 이름으로 넣어도 인식합니다)

    Returns:
        dict: {
            "names": [{"name": "...", "meaning": "..."}, ...],   # 3개
            "slogans": ["...", "...", "..."],                    # 3개
            "story": "브랜드 스토리 본문...",
            "colors": {"main": "#RRGGBB", "sub": ["#RRGGBB", "#RRGGBB"]}
        }
    """
    # 1. API 키 확인 (환경변수 또는 .env 파일에 OPENAI_API_KEY가 등록되어 있어야 합니다)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            "시스템 환경변수 혹은 현재 디렉터리의 .env 파일에 API 키를 설정해주세요."
        )

    # 2. OpenAI Client 초기화
    client = OpenAI(api_key=api_key)

    # 3. 프롬프트 작성
    prompt = f"""
    당신은 전문 브랜드 컨설턴트이자 크리에이티브 디렉터입니다.
    제공된 [브랜드 브리프]를 분석하여 매력적인 브랜드 아이덴티티 후보군을 도출해 주세요.

    [브랜드 브리프]
    - 산업군(Industry): {brief.get('industry', 'N/A')}
    - 타겟 오디언스(Target Audience): {brief.get('target', brief.get('target_audience', 'N/A'))}
    - 브랜드 키워드(Keywords): {', '.join(brief.get('keywords', []))}
    - 톤앤매너(Tone & Manner): {brief.get('tone', 'N/A')}
    - 경쟁사(Competitors): {', '.join(brief.get('competitors', []))}
    - 추가 참고사항(Notes): {brief.get('notes', brief.get('concept', 'N/A'))}

    [생성 가이드라인]
    1. 브랜드명(names):
       - 정확히 3개만 생성하세요.
       - 발음하기 쉽고, 브랜드 컨셉 및 키워드를 은유적 혹은 함축적으로 나타내는 감각적인 이름이어야 합니다.
       - 각 이름마다 그 이름에 담긴 의미(meaning)를 한 문장으로 설명해 주세요.
       - 경쟁사와 뚜렷이 구별되는 이름이어야 하며, 경쟁사 이름을 그대로 쓰지 마세요.
    2. 슬로건(slogans):
       - 정확히 3개를 작성하세요.
       - 입에 붙기 쉽고 핵심 가치를 강하게 호소할 수 있는 참신한 문장이어야 합니다.
    3. 브랜드 스토리(story):
       - 타겟 오디언스의 마음을 사로잡을 수 있도록, 브리프의 톤앤매너에 맞춰 서술해 주세요.
    4. 브랜드 컬러(colors):
       - 브랜드 컨셉에 맞는 메인 컬러 1개(main)와 서브 컬러 2개(sub)를 제안해 주세요.
       - 반드시 '#RRGGBB' 형식의 6자리 HEX 코드로만 작성하세요.

    브랜드명을 제외한 모든 텍스트는 한국어로 작성해 주세요.
    """

    # 4. Structured Output API 호출
    # response_format에 Pydantic 모델을 주어 출력을 정형 JSON으로 제어합니다.
    response = client.chat.completions.parse(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "당신은 전문 브랜드 컨설턴트이자 크리에이티브 디렉터입니다."},
            {"role": "user", "content": prompt}
        ],
        response_format=BrandGenerationResult,
        temperature=0.7
    )

    # 5. 파싱된 결과를 파이썬 딕셔너리로 변환하여 반환
    parsed_obj = response.choices[0].message.parsed
    if parsed_obj is None:
        # 안전 필터에 걸리거나 응답이 중간에 끊긴 경우
        raise RuntimeError(
            f"모델이 구조화된 결과를 반환하지 않았습니다. "
            f"원본 응답: {response.choices[0].message.content}"
        )

    result_dict = parsed_obj.model_dump()

    # 6. 개수 규격(이름 3개, 슬로건 3개, 서브컬러 2개)을 코드에서 한 번 더 보정
    result_dict["names"] = result_dict["names"][:3]
    result_dict["slogans"] = result_dict["slogans"][:3]
    result_dict["colors"]["sub"] = result_dict["colors"]["sub"][:2]

    return result_dict


# 이전 버전 함수명으로 작성된 코드와의 호환을 위한 별칭
generate_brand_identity = generate_brand_text


# =====================================================================
# 3. 함수 사용 예제 코드 (이 파일만 단독 실행했을 때 동작)
# =====================================================================
if __name__ == "__main__":
    # 기본 테스트용 브리프 데이터
    test_brief = {
        "industry": "친환경 화장품",
        "target": "20~30대 여성",
        "keywords": ["자연", "순수", "건강"],
        "tone": "따뜻하고 신뢰감 있는",
        "competitors": ["이니스프리", "아로마티카"],
        "notes": "친환경적이면서 세련된 브랜드 이미지를 지향"
    }

    # brand_brief.json 파일이 있으면 불러와서 사용하고, 없으면 test_brief를 사용합니다.
    json_path = "brand_brief.json"
    brief_data = test_brief
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                brief_data = json.load(f)
            print(f"'{json_path}' 파일에서 브리프 데이터를 성공적으로 로드했습니다.")
        except Exception as e:
            print(f"'{json_path}' 파일을 읽는 중 오류가 발생하여 기본 테스트 데이터를 사용합니다: {e}")
    else:
        print(f"'{json_path}' 파일이 존재하지 않아 기본 테스트 데이터를 사용합니다.")

    print("브랜드 아이덴티티 생성 중...\n")
    try:
        brand_identity = generate_brand_text(brief_data)
        print("====== 생성 결과 ======")
        print(json.dumps(brand_identity, indent=2, ensure_ascii=False))

        # 결과를 output/brand_result.json 파일로 저장합니다.
        os.makedirs("output", exist_ok=True)
        result_path = os.path.join("output", "brand_result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(brand_identity, f, indent=2, ensure_ascii=False)
        print(f"\n성공적으로 '{result_path}' 파일에 결과를 저장했습니다.")
    except Exception as e:
        print(f"에러가 발생했습니다: {e}")
        print("\n[알림] API 키를 설정하지 않았다면 프로젝트 루트 폴더에 '.env' 파일을 생성하고")
        print("OPENAI_API_KEY=your_actual_api_key_here")
        print("와 같이 적어넣은 후 다시 실행해 보세요.")
