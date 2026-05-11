"""
collect_template.py
손글씨 샘플 수집용 인쇄 템플릿(PNG)을 생성합니다.

사용법:
    python scripts/collect_template.py --output assets/template.png

인쇄 후 네모 칸에 손글씨로 채워서 스캔하세요.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np


# LF-Font 최적 4글자 (자모 커버리지 최대화)
DEFAULT_CHARS = ["갈", "넓", "읽", "좋"]

# DM-Font용 28글자 (더 높은 품질 원할 때)
DMFONT_CHARS = [
    "갈", "넓", "읽", "좋", "밝", "흙", "닭", "삶",
    "젊", "옭", "긁", "뚫", "얽", "훑", "핥", "굶",
    "잃", "닳", "끓", "떫", "곬", "섧", "헑", "볶",
    "뒤", "쥐", "뢰", "쾌"
]


def make_template(chars: list, output_path: Path, title: str = "손글씨 샘플 수집"):
    """인쇄용 템플릿 이미지 생성."""
    # 페이지 설정 (A4 @ 150dpi)
    PAGE_W, PAGE_H = 1240, 1754
    MARGIN = 80
    CELL_SIZE = 220
    COLS = min(4, len(chars))
    ROWS = (len(chars) + COLS - 1) // COLS

    img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(img)

    # 제목
    draw.text((MARGIN, MARGIN), title, fill="black")
    draw.text((MARGIN, MARGIN + 40),
              "아래 칸에 각 글자를 손글씨로 쓰고 300dpi 이상으로 스캔하세요.",
              fill="#555555")

    y_start = MARGIN + 110
    for i, char in enumerate(chars):
        row = i // COLS
        col = i % COLS
        x = MARGIN + col * (CELL_SIZE + 20)
        y = y_start + row * (CELL_SIZE + 60)

        # 셀 박스
        draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE],
                       outline="black", width=2)

        # 안내 글자 (연하게)
        draw.text((x + CELL_SIZE // 2 - 40, y + CELL_SIZE // 2 - 40),
                  char, fill="#CCCCCC")

        # 파일명 안내
        draw.text((x, y + CELL_SIZE + 8),
                  f"파일명: {char}.png", fill="#333333")

        # 자모 분해 표시
        code = ord(char) - 0xAC00
        cho_idx = code // (21 * 28)
        jung_idx = (code % (21 * 28)) // 28
        jong_idx = code % 28
        CHOSUNG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
        JUNGSUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
        JONGSUNG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
        jamo = f"{CHOSUNG[cho_idx]}+{JUNGSUNG[jung_idx]}"
        if jong_idx > 0:
            jamo += f"+{JONGSUNG[jong_idx]}"
        draw.text((x, y + CELL_SIZE + 28), jamo, fill="#888888")

    # 하단 안내
    note_y = PAGE_H - MARGIN - 60
    draw.line([(MARGIN, note_y), (PAGE_W - MARGIN, note_y)], fill="#CCCCCC", width=1)
    draw.text((MARGIN, note_y + 12),
              "스캔 후 각 글자를 개별 크롭하여 data/my_handwriting/ 에 저장하세요.",
              fill="#555555")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, dpi=(150, 150))
    print(f"템플릿 저장: {output_path}")
    print(f"수집 글자 ({len(chars)}자): {' '.join(chars)}")


def main(args):
    chars = DMFONT_CHARS[:args.num_chars] if args.dm_font else DEFAULT_CHARS
    make_template(chars, Path(args.output),
                  title="손글씨 샘플 수집 (DM-Font)" if args.dm_font else "손글씨 샘플 수집 (LF-Font)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="손글씨 수집 템플릿 생성")
    parser.add_argument("--output", type=str, default="assets/template.png")
    parser.add_argument("--dm_font", action="store_true",
                        help="DM-Font용 28글자 템플릿 생성")
    parser.add_argument("--num_chars", type=int, default=28,
                        help="DM-Font 모드에서 글자 수 (최대 28)")
    args = parser.parse_args()
    main(args)
