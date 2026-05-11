"""
build_ttf.py
생성된 PNG 글자 이미지들을 TTF 폰트 파일로 변환합니다.

파이프라인:
  PNG → (이진화) → SVG (potrace) → TTF (fontforge)

사용법:
    python scripts/build_ttf.py \
        --png_dir output/png \
        --output output/my_handwriting.ttf \
        --font_name "MyHandwriting"

요구사항:
    - potrace: sudo apt install potrace
    - fontforge: sudo apt install fontforge python3-fontforge
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm


# ─── 상수 ───────────────────────────────────────────────
GLYPH_SIZE = 1000      # UPM (units per em)
BASELINE = 120         # 베이스라인 오프셋
IMG_SIZE = 128         # 입력 PNG 크기


def check_dependencies():
    """potrace, fontforge 설치 확인."""
    missing = []
    for cmd in ["potrace", "fontforge"]:
        result = subprocess.run(["which", cmd], capture_output=True)
        if result.returncode != 0:
            missing.append(cmd)
    if missing:
        print(f"오류: 다음 프로그램이 설치되지 않았습니다: {', '.join(missing)}")
        print("  Ubuntu: sudo apt install potrace fontforge python3-fontforge")
        print("  macOS:  brew install potrace fontforge")
        sys.exit(1)


def png_to_bmp(png_path: Path, bmp_path: Path, threshold: int = 128):
    """PNG를 potrace 입력용 BMP로 변환 (1-bit)."""
    img = Image.open(png_path).convert("L")
    arr = np.array(img)
    binary = (arr < threshold).astype(np.uint8) * 255
    Image.fromarray(binary).convert("1").save(bmp_path)


def bmp_to_svg(bmp_path: Path, svg_path: Path):
    """potrace로 BMP → SVG 벡터 변환."""
    result = subprocess.run(
        ["potrace", str(bmp_path), "-s", "-o", str(svg_path),
         "--tight", "-W", "1", "-H", "1"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"potrace 오류: {result.stderr}")


def build_ttf(svg_dir: Path, output_path: Path, font_name: str):
    """fontforge Python API로 SVG들을 TTF로 조합."""
    try:
        import fontforge
    except ImportError:
        print("오류: fontforge Python 모듈을 찾을 수 없습니다.")
        print("  Ubuntu: sudo apt install python3-fontforge")
        print("  또는 fontforge 내장 Python으로 실행: fontforge -script scripts/build_ttf.py ...")
        sys.exit(1)

    font = fontforge.font()
    font.fontname = font_name.replace(" ", "")
    font.fullname = font_name
    font.familyname = font_name
    font.encoding = "UnicodeFull"
    font.em = GLYPH_SIZE

    svg_files = sorted(svg_dir.glob("*.svg"))
    print(f"\nTTF 빌드 중: {len(svg_files)}개 글리프...")

    added = 0
    for svg_path in tqdm(svg_files, desc="글리프 추가"):
        char = svg_path.stem
        if len(char) != 1:
            continue

        unicode_val = ord(char)
        glyph = font.createChar(unicode_val, char)
        glyph.width = GLYPH_SIZE

        try:
            glyph.importOutlines(str(svg_path))
            # 스케일 & 위치 조정
            glyph.transform(
                fontforge.unitlessTransform(
                    GLYPH_SIZE, 0, 0, GLYPH_SIZE, 0, BASELINE
                )
            )
            glyph.correctDirection()
            added += 1
        except Exception as e:
            tqdm.write(f"  글리프 오류 ({char}): {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    font.generate(str(output_path))
    print(f"\n완료: {added}개 글리프 → {output_path}")


def main(args):
    check_dependencies()

    png_dir = Path(args.png_dir)
    output_path = Path(args.output)
    svg_dir = Path(args.svg_dir) if args.svg_dir else png_dir.parent / "svg"
    svg_dir.mkdir(parents=True, exist_ok=True)

    png_files = sorted(png_dir.glob("*.png"))
    print(f"PNG 파일 {len(png_files)}개 발견")

    # PNG → SVG
    print("\n[1/2] PNG → SVG 변환 중 (potrace)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for png_path in tqdm(png_files, desc="벡터화"):
            char = png_path.stem
            if len(char) != 1:
                continue
            bmp_path = tmp / f"{char}.bmp"
            svg_path = svg_dir / f"{char}.svg"
            if svg_path.exists() and not args.force:
                continue
            try:
                png_to_bmp(png_path, bmp_path)
                bmp_to_svg(bmp_path, svg_path)
            except Exception as e:
                tqdm.write(f"  오류 ({char}): {e}")

    # SVG → TTF
    print("\n[2/2] SVG → TTF 빌드 중 (fontforge)...")
    build_ttf(svg_dir, output_path, args.font_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PNG 글자 이미지 → TTF 폰트 변환")
    parser.add_argument("--png_dir", type=str, default="output/png",
                        help="생성된 PNG 글자 이미지 폴더")
    parser.add_argument("--svg_dir", type=str, default=None,
                        help="중간 SVG 저장 폴더 (기본: output/svg)")
    parser.add_argument("--output", type=str, default="output/my_handwriting.ttf",
                        help="출력 TTF 파일 경로")
    parser.add_argument("--font_name", type=str, default="MyHandwriting",
                        help="폰트 이름")
    parser.add_argument("--force", action="store_true",
                        help="이미 존재하는 SVG도 재생성")
    args = parser.parse_args()
    main(args)
