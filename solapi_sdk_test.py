#!/usr/bin/env python3
"""
SOLAPI SDK를 사용한 음성 메시지 테스트
"""

from solapi import SolapiMessageService
from solapi.model.request.message import Message, MessageType

def send_voice_message():
    """SOLAPI SDK로 음성 메시지 발송"""
    
    # SOLAPI 메시지 서비스 초기화
    message_service = SolapiMessageService(
        api_key='NCS6P2VW8NH44ZNI',
        api_secret='EMAMDFGPTPMH3SQI37ZIBTZVGQQLRBN3'
    )
    
    # 음성 메시지 설정
    message = Message(
        to='01098942273',  # 수신번호
        from_='01098942273',  # 발신번호 (SOLAPI에 등록된 번호)
        text='안녕하세요. SOLAPI 음성 메시지 테스트입니다. 1번을 누르시면 확인됩니다.',
        type=MessageType.VOICE,
        voiceOptions={
            'voiceType': 'FEMALE',
            'headerMessage': '안녕하세요. SOLAPI 테스트입니다.',
            'tailMessage': '감사합니다. 좋은 하루 되세요.',
            'replyRange': 1
        }
    )
    
    try:
        print("=== SOLAPI SDK 음성 메시지 발송 ===")
        print(f"발신번호: {message.from_}")
        print(f"수신번호: {message.to}")
        print(f"메시지: {message.text}")
        print("음성 메시지 발송 중...")
        
        # 음성 메시지 발송
        result = message_service.send(message)
        
        print(f"[SUCCESS] 발송 성공!")
        print(f"Message ID: {result.get('messageId')}")
        print(f"Response: {result}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] 발송 실패: {e}")
        return None

if __name__ == "__main__":
    send_voice_message()
