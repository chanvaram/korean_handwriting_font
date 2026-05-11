# 한글 손글씨 폰트 생성기 

**4글자 손글씨 샘플만으로 11,172자 전체 한글 폰트를 자동 생성합니다.**

NAVER CLOVA의 [LF-Font](https://github.com/clovaai/lffont) (AAAI 2021) 기반 구현체입니다.  
자모(초/중/종성)를 Matrix Factorization으로 분해해 적은 샘플로 전체 한글을 합성합니다.

---

## 결과 예시

| 입력 (4글자) | 생성 결과 |
|---|---|
| 갈, 넓, 읽, 좋 | 전체 한글 11,172자 (내 손글씨 스타일) |

---

## 원리

```
손글씨 4글자 이미지
       ↓
  Style Encoder  ←─ 자모 단위 스타일 분해 (Matrix Factorization)
       +
 Content Encoder ←─ 글자 구조(획 배치) 인코딩
       ↓
    Decoder      ←─ 새 글자 합성
       ↓
  PNG 11,172장   →  TTF 폰트 파일
```

---

## 빠른 시작

### 1. 환경 설정

```bash
git clone https://github.com/<your-username>/korean-handwriting-font
cd korean-handwriting-font
bash setup.sh
```

### 2. LF-Font 사전학습 모델 준비

```bash
# LF-Font 레포 클론 (서브모듈)
git clone https://github.com/clovaai/lffont extern/lffont

# 사전학습 가중치 다운로드 (LF-Font README 참고)
# pretrained/ 폴더에 lffont.pth 배치
```

### 3. 샘플 글자 수집

아래 4글자를 A4 종이에 손으로 쓰고 300dpi 이상으로 스캔합니다.

```
갈  넓  읽  좋
```

스캔 이미지를 `data/my_handwriting/` 에 저장:

```
data/my_handwriting/
├── 갈.png
├── 넓.png
├── 읽.png
└── 좋.png
```

> 파일명이 반드시 한글 음절이어야 합니다 (UTF-8).

### 4. 이미지 전처리

```bash
python scripts/preprocess.py \
  --input_dir data/my_handwriting \
  --output_dir data/preprocessed
```

### 5. 폰트 생성

```bash
python scripts/inference.py \
  --config configs/lffont.yaml \
  --weight pretrained/lffont.pth \
  --ref_dir data/preprocessed \
  --output_dir output/png
```

### 6. TTF 변환

```bash
python scripts/build_ttf.py \
  --png_dir output/png \
  --output output/my_handwriting.ttf
```

---

## 디렉토리 구조

```
korean-handwriting-font/
├── data/
│   ├── my_handwriting/      # 원본 손글씨 스캔 이미지 (4장)
│   └── preprocessed/        # 전처리 완료 이미지
├── output/
│   ├── png/                 # 생성된 글자 이미지
│   └── my_handwriting.ttf   # 최종 폰트 파일
├── scripts/
│   ├── preprocess.py        # 이미지 전처리
│   ├── inference.py         # LF-Font 추론
│   ├── build_ttf.py         # PNG → TTF 변환
│   └── collect_template.py  # 샘플 수집 템플릿 생성
├── configs/
│   └── lffont.yaml          # 모델 설정
├── extern/                  # LF-Font 서브모듈
├── pretrained/              # 사전학습 가중치 (git 미포함)
├── setup.sh
├── requirements.txt
└── README.md
```

---

## 요구사항

- Python 3.8+
- PyTorch 1.7+ (CUDA 11.0 권장)
- fontforge (TTF 변환용)
- GPU: GTX 1060 6GB 이상 권장 (CPU도 가능, 느림)

GPU 없을 경우 → [Google Colab 버전](#colab) 사용

---

## 참고 논문

- **LF-Font**: *Few-Shot Compositional Font Generation with Dual Memory* (ECCV 2020)  
  [arxiv](https://arxiv.org/abs/2009.11042) | [code](https://github.com/clovaai/lffont)
- **DM-Font**: *Decomposition-based Font Generation* (AAAI 2021)  
  [arxiv](https://arxiv.org/abs/2005.10510) | [code](https://github.com/clovaai/dmfont)
- 발표: 차준범 (NAVER CLOVA), *Few-shot handwriting copycat AI*, 2020
