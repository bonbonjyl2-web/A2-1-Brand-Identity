"""브랜드 아이덴티티 생성기 - 통합 실행 엔트리포인트.

brand_brief.json을 읽어 브랜드 텍스트를 생성하고, 그 결과로 컬러 팔레트와
로고 3종을 output 폴더에 저장합니다.

사용법:
    python main.py                       # brand_brief.json 사용, 전체 생성
    python main.py --brief other.json    # 다른 브리프 파일 사용
    python main.py --no-images           # 텍스트(brand_result.json)만 생성
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from brand_brief import generate_brand_text
from image import generate_color_palette, generate_logos

# 프로젝트 루트 기준 경로 (어느 위치에서 실행해도 동일하게 동작하도록)
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BRIEF = BASE_DIR / "brand_brief.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

load_dotenv(BASE_DIR / ".env")


def load_brief(brief_path: Path) -> dict:
    """브리프 JSON 파일을 읽어 딕셔너리로 반환합니다."""
    if not brief_path.exists():
        raise FileNotFoundError(f"브리프 파일을 찾을 수 없습니다: {brief_path}")

    with brief_path.open(encoding="utf-8") as f:
        brief = json.load(f)

    if not isinstance(brief, dict):
        raise ValueError("브리프 파일의 최상위 구조는 JSON 객체(dict)여야 합니다.")

    return brief


def save_brand_result(brand_result: dict, output_dir: Path) -> Path:
    """생성된 브랜드 텍스트 결과를 brand_result.json으로 저장합니다."""
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "brand_result.json"

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(brand_result, f, ensure_ascii=False, indent=2)

    return file_path


def print_summary(brand_result: dict) -> None:
    """생성 결과를 콘솔에 보기 좋게 출력합니다."""
    print("\n[브랜드명 후보]")
    for index, item in enumerate(brand_result["names"], start=1):
        # 영문명이 없는 옛 결과 파일도 그대로 출력되도록 처리
        name_en = item.get("name_en")
        display = f"{item['name']} ({name_en})" if name_en else item["name"]
        print(f"  {index}. {display}: {item['meaning']}")

    print("\n[슬로건]")
    for slogan in brand_result["slogans"]:
        print(f"  - {slogan}")

    print("\n[브랜드 스토리]")
    print(f"  {brand_result['story']}")

    colors = brand_result["colors"]
    print("\n[컬러]")
    print(f"  main: {colors['main']}")
    print(f"  sub : {', '.join(colors['sub'])}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="브랜드 아이덴티티(텍스트 + 이미지) 생성기")
    parser.add_argument("--brief", type=Path, default=DEFAULT_BRIEF, help="브랜드 브리프 JSON 파일 경로")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="결과물을 저장할 폴더 경로")
    parser.add_argument("--no-images", action="store_true", help="이미지 생성을 건너뛰고 텍스트만 생성")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_files = []

    try:
        # 1단계: 브리프 로드
        print(f"[1/4] 브리프 로드: {args.brief}")
        brief = load_brief(args.brief)

        # 2단계: 브랜드 텍스트 생성
        print("[2/4] 브랜드 텍스트 생성 중... (OpenAI API 호출)")
        brand_result = generate_brand_text(brief)
        generated_files.append(save_brand_result(brand_result, args.output))
        print_summary(brand_result)

        if args.no_images:
            print("\n[3/4] --no-images 옵션이 지정되어 이미지 생성을 건너뜁니다.")
        else:
            # 3단계: 컬러 팔레트 이미지 (로컬 렌더링, API 호출 없음)
            print("\n[3/4] 컬러 팔레트 이미지 생성 중...")
            generated_files.append(Path(generate_color_palette(brand_result, str(args.output))))

            # 4단계: 로고 이미지 (브랜드명 3개 x 시안 3장 = 9장, OpenAI 이미지 API 호출)
            print("[4/4] 로고 이미지 9장 생성 중... (OpenAI API 호출, 수 분 소요될 수 있습니다)")
            generated_files.extend(Path(p) for p in generate_logos(brand_result, str(args.output)))

        print("\n====== 생성 완료 ======")
        for path in generated_files:
            print(f"  {path}")
        return 0

    except FileNotFoundError as e:
        print(f"[에러] {e}", file=sys.stderr)
    except ValueError as e:
        # API 키 미설정, 브리프 형식 오류 등
        print(f"[에러] {e}", file=sys.stderr)
        print("\n[알림] .env.example을 복사해 .env를 만들고 OPENAI_API_KEY를 채워주세요.", file=sys.stderr)
    except Exception as e:
        print(f"[에러] 예기치 못한 오류가 발생했습니다: {type(e).__name__}: {e}", file=sys.stderr)

    # 실패해도 그때까지 만들어진 파일은 알려줍니다.
    if generated_files:
        print("\n[참고] 아래 파일까지는 정상 생성되었습니다.", file=sys.stderr)
        for path in generated_files:
            print(f"  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
