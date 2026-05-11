"""
inference.py
LF-Font 모델을 사용해 손글씨 스타일의 한글 전체를 생성합니다.

사용법:
    python scripts/inference.py \
        --config configs/lffont.yaml \
        --weight pretrained/lffont.pth \
        --ref_dir data/preprocessed \
        --output_dir output/png
"""

import argparse
import os
import sys
from pathlib import Path

import torch
import yaml
from tqdm import tqdm
from PIL import Image
import numpy as np


# LF-Font 레포를 Python 경로에 추가
LFFONT_PATH = Path(__file__).parent.parent / "extern" / "lffont"
if LFFONT_PATH.exists():
    sys.path.insert(0, str(LFFONT_PATH))
else:
    print("오류: extern/lffont 디렉토리가 없습니다.")
    print("  git clone https://github.com/clovaai/lffont extern/lffont")
    sys.exit(1)


# 한글 완성형 전체 범위
ALL_KOREAN = [chr(c) for c in range(0xAC00, 0xD7A4)]

# 자모 분해 유틸
CHOSUNG = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNGSUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONGSUNG = list(" ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")


def decompose(char: str):
    """한글 음절 → (초성, 중성, 종성) 인덱스."""
    code = ord(char) - 0xAC00
    cho = code // (21 * 28)
    jung = (code % (21 * 28)) // 28
    jong = code % 28
    return cho, jung, jong


def load_model(config_path: str, weight_path: str, device: torch.device):
    """LF-Font 모델 로드."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    try:
        from models import Generator  # LF-Font 내부 모듈
    except ImportError:
        print("오류: LF-Font 모듈을 불러올 수 없습니다.")
        print("  extern/lffont 경로를 확인하세요.")
        sys.exit(1)

    model = Generator(**cfg.get("model", {})).to(device)
    state = torch.load(weight_path, map_location=device)
    model.load_state_dict(state.get("generator", state))
    model.eval()
    print(f"모델 로드 완료: {weight_path}")
    return model, cfg


def load_reference_images(ref_dir: Path, device: torch.device):
    """레퍼런스 손글씨 이미지 로드."""
    ref_images = {}
    for p in sorted(ref_dir.glob("*.png")):
        char = p.stem
        if len(char) == 1 and 0xAC00 <= ord(char) <= 0xD7A3:
            img = Image.open(p).convert("L")
            arr = np.array(img, dtype=np.float32) / 255.0
            tensor = torch.tensor(arr).unsqueeze(0).unsqueeze(0).to(device)
            ref_images[char] = tensor

    if not ref_images:
        print(f"오류: {ref_dir} 에서 한글 이미지를 찾을 수 없습니다.")
        sys.exit(1)

    print(f"레퍼런스 이미지 {len(ref_images)}장 로드: {list(ref_images.keys())}")
    return ref_images


def generate_all(model, ref_images: dict, output_dir: Path, device: torch.device, cfg: dict):
    """전체 한글 11,172자 생성."""
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_size = cfg.get("inference", {}).get("batch_size", 16)

    chars_to_generate = [
        c for c in ALL_KOREAN
        if not (output_dir / f"{c}.png").exists()
    ]
    print(f"\n생성할 글자: {len(chars_to_generate)}자")

    with torch.no_grad():
        for i in tqdm(range(0, len(chars_to_generate), batch_size), desc="생성 중"):
            batch_chars = chars_to_generate[i:i+batch_size]

            for char in batch_chars:
                try:
                    # LF-Font API 호출 (실제 API는 lffont 레포 참고)
                    out = model.generate(
                        content_char=char,
                        style_refs=ref_images,
                    )
                    img = (out.squeeze().cpu().numpy() * 255).astype(np.uint8)
                    Image.fromarray(img).save(output_dir / f"{char}.png")
                except Exception as e:
                    tqdm.write(f"  생성 실패 ({char}): {e}")

    print(f"\n생성 완료 → {output_dir}")


def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    print(f"장치: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    model, cfg = load_model(args.config, args.weight, device)
    ref_images = load_reference_images(Path(args.ref_dir), device)
    generate_all(model, ref_images, Path(args.output_dir), device, cfg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LF-Font 한글 손글씨 생성")
    parser.add_argument("--config", type=str, default="configs/lffont.yaml")
    parser.add_argument("--weight", type=str, default="pretrained/lffont.pth")
    parser.add_argument("--ref_dir", type=str, default="data/preprocessed",
                        help="전처리된 레퍼런스 이미지 폴더")
    parser.add_argument("--output_dir", type=str, default="output/png",
                        help="생성된 글자 이미지 저장 폴더")
    parser.add_argument("--cpu", action="store_true", help="CPU 강제 사용")
    args = parser.parse_args()
    main(args)
