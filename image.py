"""브랜드 이미지(로고 3종 + 컬러 팔레트) 생성 모듈.

- generate_logos()        : OpenAI 이미지 API로 logo_01~03.png 생성
- generate_color_palette(): 생성된 HEX 코드로 color_palette.png를 로컬에서 렌더링

import 만으로 API가 호출되지 않도록, 모든 동작은 함수 안에 들어 있습니다.
API 키는 코드에 하드코딩하지 않고 .env의 OPENAI_API_KEY에서만 읽습니다.
"""

import base64
import os
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# .env 파일 불러오기
load_dotenv()

# 이미지 모델 (.env에서 OPENAI_IMAGE_MODEL로 변경 가능)
# 계정에 gpt-image-2 권한이 없을 경우 gpt-image-1로 자동 폴백합니다.
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
FALLBACK_IMAGE_MODEL = "gpt-image-1"
IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "medium"

# 브랜드명 후보 3개 x 이름당 시안 3장 = 총 9장
LOGO_NAME_COUNT = 3
LOGO_VARIANT_COUNT = 3

# 한글 라벨 렌더링용 폰트 후보 (없으면 기본 폰트로 대체)
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]


# =====================================================================
# 내부 유틸리티
# =====================================================================


def _get_client() -> OpenAI:
    """API 키를 환경변수에서 읽어 OpenAI 클라이언트를 만듭니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    return OpenAI(api_key=api_key)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한글이 깨지지 않는 폰트를 찾아 로드합니다."""
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """'#2E7D32' 형태의 HEX 문자열을 (46, 125, 50) RGB 튜플로 변환합니다."""
    value = str(hex_code).strip().lstrip("#")
    if len(value) == 3:  # #ABC 축약형 지원
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return (204, 204, 204)  # 형식이 깨졌을 때의 안전한 회색
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (204, 204, 204)


def _text_color_for(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """배경색 밝기에 따라 읽기 쉬운 글자색(검정/흰색)을 고릅니다."""
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return (0, 0, 0) if luminance > 0.6 else (255, 255, 255)


def _extract_names(brand_result: dict) -> List[Tuple[str, str]]:
    """brand_result에서 (브랜드명, 의미) 쌍을 최대 3개까지 뽑아냅니다.

    명세 스키마({"name":..., "meaning":...})와 옛 스키마(문자열 배열)를 모두 지원합니다.
    """
    names = brand_result.get("names") or ["Brand"]

    extracted: List[Tuple[str, str]] = []
    for entry in names[:LOGO_NAME_COUNT]:
        if isinstance(entry, dict):
            extracted.append((entry.get("name", "Brand"), entry.get("meaning", "")))
        else:
            extracted.append((str(entry), ""))

    return extracted


def _extract_colors(brand_result: dict) -> Tuple[str, List[str]]:
    """brand_result에서 (메인 컬러, 서브 컬러 목록)을 뽑아냅니다."""
    colors = brand_result.get("colors", {}) or {}
    if "main" in colors:
        main_color = colors.get("main", "#2E7D32")
        sub_colors = [c for c in colors.get("sub", []) if c][:2]
    else:
        # 옛 스키마(primary/secondary/background/accent) 호환
        def _hex_of(key: str, default: str) -> str:
            entry = colors.get(key)
            if isinstance(entry, dict):
                return entry.get("hex", default)
            return entry or default

        main_color = _hex_of("primary", "#2E7D32")
        sub_colors = [_hex_of("secondary", "#81C784"), _hex_of("accent", "#E8F5E9")]

    return main_color, sub_colors


def _build_prompts_for_name(brand_name: str, meaning: str, slogan: str,
                            main_color: str, sub_colors: List[str]) -> List[str]:
    """브랜드명 하나에 대해 서로 다른 스타일의 로고 프롬프트 3개를 만듭니다."""
    palette = f"main color {main_color}, supporting colors {', '.join(sub_colors)}"

    common = f"""
Create a professional brand logo for '{brand_name}'.

Brand context:
Brand meaning: {meaning}
Brand slogan: {slogan}
Color palette: {palette}

Visual requirements:
Flat vector style,
clean and modern,
centered composition,
plain white background,
soft and elegant feeling.

No people.
No famous brands.
No copyrighted or existing brand logos.
No photo mockups.
No watermark.
"""

    return [
        common + "\nStyle: minimal abstract symbol mark only, simple geometric shapes, generous negative space.",
        common + f"\nStyle: elegant wordmark spelling '{brand_name}' in a refined sans-serif typeface.",
        common + f"\nStyle: circular emblem/badge combining a simple icon with the brand name '{brand_name}'.",
    ]


def _build_logo_plan(brand_result: dict) -> List[Tuple[int, int, str, str]]:
    """브랜드명 3개 x 시안 3개 = 총 9장의 생성 계획을 만듭니다.

    Returns:
        list[tuple]: (이름 순번, 시안 순번, 브랜드명, 프롬프트) 목록
    """
    slogan = (brand_result.get("slogans") or [""])[0]
    main_color, sub_colors = _extract_colors(brand_result)

    plan: List[Tuple[int, int, str, str]] = []
    for name_index, (brand_name, meaning) in enumerate(_extract_names(brand_result), start=1):
        prompts = _build_prompts_for_name(brand_name, meaning, slogan, main_color, sub_colors)
        for variant_index, prompt in enumerate(prompts[:LOGO_VARIANT_COUNT], start=1):
            plan.append((name_index, variant_index, brand_name, prompt))

    return plan


def _generate_one_image(client: OpenAI, prompt: str) -> bytes:
    """이미지 1장을 생성해 PNG 바이트로 돌려줍니다. (모델별 파라미터 차이 처리)"""

    def _call(model: str):
        kwargs = {"model": model, "prompt": prompt, "size": IMAGE_SIZE, "n": 1}
        if model.startswith("gpt-image"):
            kwargs["quality"] = IMAGE_QUALITY
            kwargs["output_format"] = "png"
        else:
            # dall-e-3 계열은 기본이 URL 응답이라 base64로 명시해 받습니다.
            kwargs["response_format"] = "b64_json"
        return client.images.generate(**kwargs)

    try:
        response = _call(IMAGE_MODEL)
    except Exception as e:
        if IMAGE_MODEL == FALLBACK_IMAGE_MODEL:
            raise
        print(f"  [알림] '{IMAGE_MODEL}' 호출 실패({type(e).__name__}) → '{FALLBACK_IMAGE_MODEL}'로 재시도합니다.")
        response = _call(FALLBACK_IMAGE_MODEL)

    return base64.b64decode(response.data[0].b64_json)


# =====================================================================
# 1. 로고 이미지 생성 함수
# =====================================================================


def generate_logos(brand_result: dict, output_dir: str) -> List[str]:
    """브랜드명 후보 3개에 대해 각각 로고 시안 3장씩, 총 9장을 생성해 저장합니다.

    파일명은 logo_{이름순번}_{시안순번}.png 형식입니다.

    Args:
        brand_result (dict): generate_brand_text()가 반환한 딕셔너리
        output_dir (str): PNG를 저장할 폴더 경로 (없으면 자동 생성)

    Returns:
        list[str]: 저장된 PNG 파일 경로 목록 (총 9개)
            예: ["output/logo_01_01.png", "output/logo_01_02.png", ..., "output/logo_03_03.png"]
    """
    client = _get_client()

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    plan = _build_logo_plan(brand_result)
    total = len(plan)

    saved_paths: List[str] = []
    for step, (name_index, variant_index, brand_name, prompt) in enumerate(plan, start=1):
        print(f"  [{step}/{total}] '{brand_name}' 시안 {variant_index}/{LOGO_VARIANT_COUNT} 생성 중...")
        image_bytes = _generate_one_image(client, prompt)

        file_path = out_path / f"logo_{name_index:02d}_{variant_index:02d}.png"
        file_path.write_bytes(image_bytes)
        saved_paths.append(str(file_path))

    return saved_paths


# =====================================================================
# 2. 컬러 팔레트 이미지 생성 함수
# =====================================================================


def generate_color_palette(brand_result: dict, output_dir: str) -> str:
    """브랜드 컬러(main 1 + sub 2)를 시각화한 color_palette.png를 만듭니다.

    API 호출 없이 Pillow로 직접 그리기 때문에 추가 비용이 들지 않습니다.

    Returns:
        str: 저장된 PNG 파일 경로 (예: "output/color_palette.png")
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    brand_name = _extract_names(brand_result)[0][0]
    main_color, sub_colors = _extract_colors(brand_result)

    swatches = [("MAIN", main_color)]
    for i, sub_hex in enumerate(sub_colors, start=1):
        swatches.append((f"SUB {i}", sub_hex))

    # 캔버스 설정
    width, height = 1200, 520
    header_height = 120
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(44)
    label_font = _load_font(28)
    hex_font = _load_font(34)

    # 헤더: 브랜드명
    draw.text((48, 40), f"{brand_name}  Color Palette", font=title_font, fill=(30, 30, 30))

    # 컬러 스와치를 가로로 균등 배치
    swatch_width = width // len(swatches)
    for i, (label, hex_code) in enumerate(swatches):
        rgb = _hex_to_rgb(hex_code)
        x0 = i * swatch_width
        x1 = width if i == len(swatches) - 1 else (i + 1) * swatch_width
        draw.rectangle([x0, header_height, x1, height], fill=rgb)

        text_color = _text_color_for(rgb)
        draw.text((x0 + 40, header_height + 60), label, font=label_font, fill=text_color)
        draw.text((x0 + 40, header_height + 110), str(hex_code).upper(), font=hex_font, fill=text_color)

    file_path = out_path / "color_palette.png"
    canvas.save(file_path, "PNG")
    return str(file_path)


# =====================================================================
# 3. 이 파일만 단독 실행했을 때: 저장된 brand_result.json으로 이미지 생성
# =====================================================================
if __name__ == "__main__":
    import json

    result_path = os.path.join("output", "brand_result.json")
    if not os.path.exists(result_path):
        result_path = "brand_result.json"

    if not os.path.exists(result_path):
        raise SystemExit("brand_result.json이 없습니다. 먼저 'python main.py'를 실행해주세요.")

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    print(f"'{result_path}' 기준으로 이미지 생성을 시작합니다.")
    print(generate_color_palette(result, "output"))
    for path in generate_logos(result, "output"):
        print(path)
