"""
preprocess.py
손글씨 스캔 이미지를 LF-Font 입력 포맷으로 전처리합니다.
- 이진화 (Otsu thresholding)
- 글자 영역 자동 크롭
- 128x128 리사이즈 + 패딩
"""

import argparse
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from tqdm import tqdm


TARGET_SIZE = 128
PADDING_RATIO = 0.1  # 글자 주변 여백 비율


def binarize(img_gray: np.ndarray) -> np.ndarray:
    """Otsu thresholding으로 이진화. 흰 배경, 검정 글자 출력."""
    _, binary = cv2.threshold(
        img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return binary


def crop_to_content(binary: np.ndarray, padding: int = 10) -> np.ndarray:
    """글자가 있는 영역을 자동으로 크롭."""
    coords = cv2.findNonZero(binary)
    if coords is None:
        return binary  # 빈 이미지면 그대로 반환

    x, y, w, h = cv2.boundingRect(coords)

    # 여백 추가
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(binary.shape[1] - x, w + 2 * padding)
    h = min(binary.shape[0] - y, h + 2 * padding)

    return binary[y:y+h, x:x+w]


def pad_to_square(img: np.ndarray) -> np.ndarray:
    """정사각형으로 패딩 (중앙 정렬)."""
    h, w = img.shape
    size = max(h, w)
    pad_h = (size - h) // 2
    pad_w = (size - w) // 2
    padded = np.zeros((size, size), dtype=np.uint8)
    padded[pad_h:pad_h+h, pad_w:pad_w+w] = img
    return padded


def preprocess_image(src_path: Path, dst_path: Path, size: int = TARGET_SIZE):
    """단일 이미지 전처리 파이프라인."""
    img = cv2.imread(str(src_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {src_path}")

    binary = binarize(img)
    cropped = crop_to_content(binary)
    squared = pad_to_square(cropped)

    # 리사이즈 (고품질 보간)
    resized = cv2.resize(squared, (size, size), interpolation=cv2.INTER_AREA)

    # 흰 배경 / 검정 글자로 반전 후 저장
    final = cv2.bitwise_not(resized)  # LF-Font: 흰 배경에 검정 글자
    cv2.imwrite(str(dst_path), final)


def validate_filename(path: Path) -> bool:
    """파일명이 한글 음절인지 확인."""
    stem = path.stem
    if len(stem) != 1:
        return False
    code = ord(stem)
    return 0xAC00 <= code <= 0xD7A3  # 한글 완성형 범위


def main(args):
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_files = list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg"))

    if not image_files:
        print(f"오류: {input_dir} 에서 이미지를 찾을 수 없습니다.")
        return

    print(f"총 {len(image_files)}장 처리 중...\n")
    errors = []

    for src in tqdm(image_files):
        if not validate_filename(src):
            print(f"  경고: '{src.name}' — 파일명이 한글 음절 1자여야 합니다. 건너뜀.")
            errors.append(src.name)
            continue

        dst = output_dir / src.name.replace(src.suffix, ".png")
        try:
            preprocess_image(src, dst, size=args.size)
        except Exception as e:
            print(f"  오류 ({src.name}): {e}")
            errors.append(src.name)

    print(f"\n완료: {len(image_files) - len(errors)}/{len(image_files)}장 처리됨")
    print(f"저장 위치: {output_dir}")

    if errors:
        print(f"\n처리 실패: {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="손글씨 이미지 전처리")
    parser.add_argument("--input_dir", type=str, default="data/my_handwriting",
                        help="원본 손글씨 이미지 폴더")
    parser.add_argument("--output_dir", type=str, default="data/preprocessed",
                        help="전처리 결과 저장 폴더")
    parser.add_argument("--size", type=int, default=128,
                        help="출력 이미지 크기 (기본: 128)")
    args = parser.parse_args()
    main(args)
