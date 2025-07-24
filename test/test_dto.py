#!/usr/bin/env python3
"""
DTO 테스트 스크립트
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from service.mail_service import MailService
from service.mail_dto import MailDTO, MailListDTO, mails_to_json, mails_to_text

def test_dto():
    load_dotenv()
    
    mail_service = MailService(
        id=os.getenv("NAVER_ID"),
        password=os.getenv("NAVER_PASSWORD")
    )
    
    print("=== DTO 테스트 ===")
    
    # 메일 가져오기
    mails = mail_service.get_mails(max_count=3)
    
    if not mails:
        print("메일이 없습니다.")
        return
    
    print(f"\n--- 첫 번째 메일 단일 변환 테스트 ---")
    first_mail = mails[0]
    
    # 단일 메일 DTO 변환
    mail_dto = MailDTO.from_mail_message(first_mail)
    
    print("📧 요약 텍스트:")
    print(mail_dto.to_summary_text())
    
    print("\n📧 상세 텍스트:")
    print(mail_dto.to_detailed_text())
    
    print("\n📧 JSON 형태:")
    print(mail_dto.to_json_string())
    
    print(f"\n--- 메일 목록 변환 테스트 ---")
    
    # 메일 목록 DTO 변환
    mail_list_dto = MailListDTO(mails)
    
    print("📋 목록 요약 텍스트:")
    print(mail_list_dto.to_summary_text())
    
    print("\n📋 목록 JSON 형태:")
    print(mail_list_dto.to_json_string())
    
    print(f"\n--- 편의 함수 테스트 ---")
    
    print("🔧 mails_to_text():")
    print(mails_to_text(mails))
    
    print("\n🔧 mails_to_json():")
    print(mails_to_json(mails))

def test_pagination_dto():
    load_dotenv()
    
    mail_service = MailService(
        id=os.getenv("NAVER_ID"),
        password=os.getenv("NAVER_PASSWORD")
    )
    
    print("\n=== 페이징 DTO 테스트 ===")
    
    # 첫 번째 페이지
    page1 = mail_service.get_mails_paginated(page_size=2)
    
    print("📄 첫 번째 페이지 (텍스트):")
    print(mails_to_text(page1['mails'], {'has_more': page1['has_more']}))
    
    print("\n📄 첫 번째 페이지 (JSON):")
    print(mails_to_json(page1['mails'], {'has_more': page1['has_more'], 'last_uid': page1['last_uid']}))

if __name__ == "__main__":
    test_dto()
    test_pagination_dto() 