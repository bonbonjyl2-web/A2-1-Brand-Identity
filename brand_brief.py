import os
import json
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# =====================================================================
# 1. Structured Output을 위한 Pydantic 데이터 스키마 정의
# =====================================================================

class ColorDetail(BaseModel):
    """색상의 이름, 16진수 HEX 코드, 그리고 의미에 대한 상세 정보"""
    name: str = Field(description="색상 이름 (예: Sage Green)")
    hex: str = Field(description="색상의 HEX 코드 (예: #8FA89B)")
    description: str = Field(description="해당 브랜드 색상이 의미하는 상징적 가치나 용도에 대한 설명")

class ColorsInfo(BaseModel):
    """브랜드 디자인 시스템을 구성하는 4가지 컬러 팔레트 정보"""
    primary: ColorDetail = Field(description="브랜드의 주조색 (가장 대표적인 색상)")
    secondary: ColorDetail = Field(description="주조색을 뒷받침하는 보조색")
    background: ColorDetail = Field(description="웹사이트나 패키지 디자인의 기본 바탕이 될 배경색")
    accent: ColorDetail = Field(description="버튼이나 강조하고 싶은 부분에 쓰일 포인트(강조) 색상")

class BrandGenerationResult(BaseModel):
    """최종적으로 생성될 브랜드 아이덴티티 정보의 스키마 구조"""
    names: List[str] = Field(description="브랜드명 후보 3~5개")
    slogans: List[str] = Field(description="브랜드 아이덴티티와 방향성을 담은 슬로건 3개")
    story: str = Field(description="브랜드의 탄생 배경, 철학, 지향점을 서술하는 브랜드 스토리")
    colors: ColorsInfo = Field(description="브랜드 디자인에 사용될 대표 컬러 정보")

# =====================================================================
# 2. 브랜드 생성 함수 정의
# =====================================================================

def generate_brand_identity(brief: dict) -> dict:
    """
    브랜드 브리프 정보를 입력받아 OpenAI API를 통해 매력적인 브랜드 아이덴티티를 생성합니다.
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
       - 3개에서 5개 사이로 생성하세요.
       - 발음하기 쉽고, 브랜드 컨셉 및 키워드를 은유적 혹은 함축적으로 나타내는 감각적인 이름이어야 합니다.
    2. 슬로건(slogans):
       - 입에 붙기 쉽고 핵심 가치를 강하게 호소할 수 있는 메인 및 서브 슬로건 형태의 참신한 슬로건 3개를 작성해 주세요.
    3. 브랜드 스토리(story):
       - 타겟 오디언스의 마음을 사로잡을 수 있도록 감성적이고 신뢰감을 주는 스토리텔링 형태로 서술해 주세요.
    4. 브랜드 컬러(colors):
       - 브랜드 컨셉에 맞는 4가지 컬러(Primary, Secondary, Background, Accent)를 제안하고, 각각의 HEX 코드와 선정 이유를 설명해 주세요.
    """
   
    # 4. Structured Output API 호출 (gpt-4o-mini 사용)
    # response_format을 주어 출력을 특정 Pydantic 모델 형태로 정형 데이터 제어합니다.
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문 브랜드 컨설턴트이자 크리에이티브 디렉터입니다."},
            {"role": "user", "content": prompt}
        ],
        response_format=BrandGenerationResult,
        temperature=0.7
    )
   
    # 5. 응답 결과(JSON 문자열)를 파싱하여 파이썬 딕셔너리로 변환하여 반환
    try:
        parsed_obj = response.choices[0].message.parsed
        if hasattr(parsed_obj, "model_dump"):
            result_dict = parsed_obj.model_dump()
        else:
            result_dict = parsed_obj.dict()
        return result_dict
    except Exception as e:
        print(f"파싱 실패: {e}")
        print(f"원본 응답: {response.choices[0].message.content}")
        raise

# =====================================================================
# 3. 함수 사용 예제 코드
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
        brand_identity = generate_brand_identity(brief_data)
        print("====== 생성 결과 ======")
        print(json.dumps(brand_identity, indent=2, ensure_ascii=False))
        
        # 결과를 brand_result.json 파일로 저장합니다.
        result_path = "brand_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(brand_identity, f, indent=2, ensure_ascii=False)
        print(f"\n성공적으로 '{result_path}' 파일에 결과를 저장했습니다.")
    except Exception as e:
        print(f"에러가 발생했습니다: {e}")
        print("\n[알림] API 키를 설정하지 않았다면 프로젝트 루트 폴더에 '.env' 파일을 생성하고")
        print("OPENAI_API_KEY=your_actual_api_key_here")
        print("와 같이 적어넣은 후 다시 실행해 보세요.")
