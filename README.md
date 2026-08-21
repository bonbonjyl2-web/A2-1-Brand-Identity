# 브랜드 아이덴티티 생성기 (A2-1)

------
6조: 팀장-이주연(전체구조 총괄), 지석원( 전체 프로젝트 구조)
          조현정(텍스트 네이밍 슬로건)
          김수정(이미지 컬러 로고)
          임유정( API 키, 결과 통합)
----

브랜드 브리프(JSON)를 입력하면 OpenAI API로 **브랜드명 3개(한글+영문) / 슬로건 3개 / 브랜드 스토리 / 컬러 팔레트**를
생성하고, 그 결과를 바탕으로 **컬러 팔레트 1장 + 로고 시안 9장**을 이미지로 만들어 주는 프로그램입니다.

- 텍스트 생성: OpenAI Structured Outputs (Pydantic 스키마로 출력 형식 고정)
- 이미지 생성: OpenAI Images API (`gpt-image-2`)
- 컬러 팔레트: matplotlib 로컬 렌더링 (API 비용 없음)

저장소: https://github.com/bonbonjyl2-web/A2-1-Brand-Identity

---

## 폴더 구조

```
A2-1-Brand-Identity/
├─ main.py             # 통합 실행 엔트리포인트
├─ brand_brief.py      # 텍스트 생성 모듈  generate_brand_text(brief)
├─ image.py            # 이미지 생성 모듈  generate_logos(brand_result, output_dir)
├─ brand_brief.json    # 입력: 브랜드 브리프
├─ .env                # OpenAI API 키 (커밋 금지)
├─ .env.example        # .env 작성 예시
├─ .gitignore
├─ README.md
└─ output/             # 생성 결과물 저장 폴더
```

---

## 설치

Python 3.12 기준입니다.

```bash
pip install openai python-dotenv pydantic matplotlib
```

## API 키 설정

`.env.example`을 복사해 `.env`를 만들고 발급받은 키를 채웁니다.
API 키는 코드에 하드코딩하지 않고 환경변수 `OPENAI_API_KEY`에서만 읽습니다.

```
OPENAI_API_KEY=sk-...
```

| 환경변수 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | O | — | OpenAI API 키 |
| `OPENAI_MODEL` | X | `gpt-4o-mini` | 텍스트 생성 모델 |
| `OPENAI_IMAGE_MODEL` | X | `gpt-image-2` | 이미지 생성 모델 (실패 시 `gpt-image-1`로 자동 폴백) |

> `.env`는 `.gitignore`에 등록되어 있습니다. **절대 커밋하지 마세요.**

---

## 실행

```bash
python main.py
```

| 옵션 | 설명 |
| --- | --- |
| `--brief <경로>` | 다른 브리프 파일 사용 (기본값: `brand_brief.json`) |
| `--output <경로>` | 결과물 저장 폴더 변경 (기본값: `output/`) |
| `--no-images` | 이미지 생성을 건너뛰고 텍스트만 생성 (비용 절약용) |

개별 모듈만 따로 실행할 수도 있습니다.

```bash
python brand_brief.py    # 텍스트만 생성해서 output/brand_result.json 저장
python image.py          # 저장된 brand_result.json으로 이미지만 생성
```

### 실행 순서

1. `brand_brief.json` 로드
2. 브랜드 텍스트 생성 → `output/brand_result.json` 저장
3. 컬러 팔레트 이미지 생성 (로컬 렌더링)
4. 로고 이미지 9장 생성 (이름 3개 × 시안 3장)

> 4단계는 이미지 9장을 생성하므로 수 분이 걸리고 API 비용이 발생합니다.
> 텍스트만 확인하려면 `--no-images`를 쓰세요.

---

## 생성 결과물

| 파일 | 설명 |
| --- | --- |
| `output/brand_result.json` | 브랜드 텍스트 생성 결과 |
| `output/color_palette.png` | 메인/서브 컬러 팔레트 |
| `output/logo_01_01.png` ~ `logo_01_03.png` | 브랜드명 1번 후보의 로고 시안 3장 |
| `output/logo_02_01.png` ~ `logo_02_03.png` | 브랜드명 2번 후보의 로고 시안 3장 |
| `output/logo_03_01.png` ~ `logo_03_03.png` | 브랜드명 3번 후보의 로고 시안 3장 |

파일명 규칙은 `logo_{이름순번}_{시안순번}.png` 입니다.
시안 3종은 이름마다 동일하게 **① 심볼 마크 ② 워드마크 ③ 엠블럼** 스타일로 생성됩니다.

---

## 입력 형식 (`brand_brief.json`)

| 키 | 타입 | 설명 |
| --- | --- | --- |
| `industry` | str | 산업 분야 |
| `target` | str | 타겟 고객층 |
| `keywords` | list[str] | 브랜드 키워드 |
| `tone` | str | 톤앤매너 |
| `competitors` | list[str] | 경쟁사 |
| `notes` | str | 추가 참고사항 |

```json
{
  "industry": "친환경 화장품",
  "target": "20~30대 여성",
  "keywords": ["자연", "순수", "건강"],
  "tone": "따뜻하고 신뢰감 있는",
  "competitors": ["이니스프리", "아로마티카"],
  "notes": "친환경적이면서 세련된 브랜드 이미지를 지향"
}
```

## 출력 형식 (`output/brand_result.json`)

```json
{
  "names": [
    { "name": "블루밍", "name_en": "Blooming", "meaning": "자연에서 피어나는 아름다움" }
  ],
  "slogans": ["일상에 자연을 담다", "피부가 숨쉬는 순간", "자연 그대로"],
  "story": "브랜드 스토리...",
  "colors": {
    "main": "#2E7D32",
    "sub": ["#81C784", "#E8F5E9"]
  }
}
```

브랜드명은 한글명(`name`)과 영문명(`name_en`)이 한 쌍으로 생성됩니다.
로고에 새겨지는 글자는 판독이 안정적인 영문명을 쓰고, 한글명은 프롬프트에 브랜드 정체성 정보로 함께 전달됩니다.

`names` 3개, `slogans` 3개, `colors.sub` 2개가 항상 보장됩니다.
Pydantic 스키마로 출력을 강제하고, 코드에서 개수를 한 번 더 잘라내기 때문입니다.

---

## 함수 명세

### `generate_brand_text(brief: dict) -> dict` — `brand_brief.py`

- **입력**: 위 브리프 형식의 dict
- **출력**: 위 `brand_result.json` 형식의 dict

### `generate_logos(brand_result: dict, output_dir: str) -> list[str]`  — `image.py`

- **입력**: `generate_brand_text()`의 반환값, 저장할 폴더 경로
- **출력**: 생성된 PNG 경로 목록 9개

```python
["output/logo_01_01.png", "output/logo_01_02.png", ..., "output/logo_03_03.png"]
```

### `generate_color_palette(brand_result: dict, output_dir: str) -> str` — `image.py`

- **출력**: 생성된 `color_palette.png` 경로 (matplotlib으로 1200×520px 렌더링)

생성 장수를 바꾸려면 `image.py` 상단의 상수를 조정하세요.

```python
LOGO_NAME_COUNT = 3     # 로고를 만들 브랜드명 개수
LOGO_VARIANT_COUNT = 3  # 이름당 시안 장수
```

---

## 사용 예시

```python
import json
from brand_brief import generate_brand_text
from image import generate_logos, generate_color_palette

with open("brand_brief.json", encoding="utf-8") as f:
    brief = json.load(f)

result = generate_brand_text(brief)
palette_path = generate_color_palette(result, "output")
logo_paths = generate_logos(result, "output")
```
## 작업 로그 

PS C:\Users\Administrator\Development\A2-1-Brand-Identity> git log
commit d4157115dd4bdd5aa0e8217250ea2570f3335942 (HEAD -> main, origin/main, origin/HEAD)
Author: dbdlf <yujeongdlek@gmail.com>
Date:   Fri Aug 21 16:23:50 2026 +0900

    chore: output 최신 생성 결과물로 갱신

commit b16c341e7dceec94d678ff48fe4697437c823d29
Author: dbdlf <yujeongdlek@gmail.com>
Date:   Fri Aug 21 16:22:55 2026 +0900

    feat: matplotlib 팔레트 렌더링, 한글+영문 브랜드명 동시 생성, gitignore 정리
    
    - generate_color_palette(): Pillow -> matplotlib(Agg 백엔드)로 교체
    - BrandName 스키마에 name_en 추가, 로고 워드마크는 영문명으로 렌더링
    - .gitignore를 Node.js용 항목 제거하고 프로젝트에 필요한 항목만 남김
    - output/: 로고 9장(logo_NN_VV.png) 및 최신 brand_result.json 갱신

commit 65196606ce4d267edeba6cd85e705652c3177609
Author: dbdlf <yujeongdlek@gmail.com>
Date:   Fri Aug 21 16:22:55 2026 +0900

    feat: 브랜드명 3개 x 로고 시안 3장(총 9장) 생성 및 README 추가
    
    - generate_brand_text(brief): 브랜드명 3개 고정, {name, meaning} / {main, sub} 스키마로 변경
    - generate_logos(brand_result, output_dir): 이름별 시안 3장씩 총 9장 생성 (logo_NN_VV.png)
    - generate_color_palette(): Pillow로 컬러 팔레트 로컬 렌더링
    
    - generate_brand_text(brief): 브랜드명 3개 고정, {name, meaning} / {main, sub} 스키마로 변경
    - generate_logos(brand_result, output_dir): 이름별 시안 3장씩 총 9장 생성 (logo_NN_VV.png)
    - generate_color_palette(): Pillow로 컬러 팔레트 로컬 렌더링
    - image.py를 최상위 스크립트에서 함수 모듈로 전환 (import 시 API 호출되던 문제 해결)
    - main.py: flat 구조에 맞게 import 정리, 산출물을 output/ 폴더로 통일
    - README.md 추가, __pycache__ 추적 해제

commit c3cdb4913dc774216f4c883921a60dd7f44c6ad2
Merge: c91a6f7 202781d
Author: haru2014 <mickey1008@naver.com>
Date:   Fri Aug 21 15:13:22 2026 +0900

    Merge branch 'main' of https://github.com/bonbonjyl2-web/A2-1-Brand-Identity
PS C:\Users\Administrator\Development\A2-1-Brand-Identity>            
