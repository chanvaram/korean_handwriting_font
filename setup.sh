#!/bin/bash
set -e

echo "================================================"
echo " 한글 손글씨 폰트 생성기 환경 설정"
echo "================================================"

# Python 버전 확인
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 버전: $python_version"

# pip 의존성 설치
echo ""
echo "[1/4] Python 패키지 설치 중..."
pip install -r requirements.txt

# fontforge 설치 (Ubuntu/Debian)
echo ""
echo "[2/4] fontforge 설치 확인..."
if ! command -v fontforge &> /dev/null; then
    echo "fontforge 설치 중..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y fontforge python3-fontforge
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install fontforge
    else
        echo "WARNING: fontforge를 수동으로 설치해주세요 (https://fontforge.org)"
    fi
else
    echo "fontforge 이미 설치됨: $(fontforge --version 2>&1 | head -1)"
fi

# potrace 설치 (PNG → SVG 벡터화)
echo ""
echo "[3/4] potrace 설치 확인..."
if ! command -v potrace &> /dev/null; then
    echo "potrace 설치 중..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y potrace
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install potrace
    else
        echo "WARNING: potrace를 수동으로 설치해주세요 (http://potrace.sourceforge.net)"
    fi
else
    echo "potrace 이미 설치됨"
fi

# 디렉토리 생성
echo ""
echo "[4/4] 디렉토리 구조 생성..."
mkdir -p data/my_handwriting data/preprocessed
mkdir -p output/png output/svg
mkdir -p pretrained extern

echo ""
echo "================================================"
echo " 설정 완료!"
echo ""
echo " 다음 단계:"
echo "  1. extern/ 에 LF-Font 클론"
echo "     git clone https://github.com/clovaai/lffont extern/lffont"
echo ""
echo "  2. pretrained/ 에 lffont.pth 다운로드"
echo "     (LF-Font GitHub README 참고)"
echo ""
echo "  3. data/my_handwriting/ 에 손글씨 이미지 4장 저장"
echo "     파일명: 갈.png 넓.png 읽.png 좋.png"
echo "================================================"
