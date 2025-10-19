#!/usr/bin/env python3
"""
QR 코드 생성 스크립트
ngrok URL을 QR 코드로 변환하여 터미널에 표시하고 이미지로 저장
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# PUBLIC_BASE_URL 읽기
public_url = os.getenv('PUBLIC_BASE_URL', 'http://localhost:8000')

print("\n" + "="*60)
print("🌐 AI 인프라비서 장애알림체험 - QR 코드 생성")
print("="*60)
print(f"\n📍 URL: {public_url}")
print("\n" + "-"*60)

try:
    import qrcode
    
    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(public_url)
    qr.make(fit=True)
    
    # 터미널에 ASCII QR 코드 출력
    print("\n📱 모바일로 스캔하세요:\n")
    qr.print_ascii(invert=True)
    
    # 이미지로 저장
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("simulator_qr.png")
    
    print("\n" + "-"*60)
    print("✅ QR 코드 이미지 저장: simulator_qr.png")
    print("="*60 + "\n")
    
except ImportError:
    print("\n⚠️  qrcode 라이브러리가 설치되지 않았습니다.")
    print("\n설치 방법:")
    print("  pip install qrcode[pil]")
    print("\n또는 온라인에서 QR 코드 생성:")
    print(f"  https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={public_url}")
    print("\n" + "="*60 + "\n")

