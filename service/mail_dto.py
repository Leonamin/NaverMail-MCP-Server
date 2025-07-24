from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from imap_tools import MailMessage


@dataclass
class MailDTO:
    """메일 데이터 전송 객체"""
    uid: str
    subject: str
    from_email: str
    from_name: Optional[str]
    to_emails: List[str]
    cc_emails: List[str]
    bcc_emails: List[str]
    date: str  # ISO 형식 문자열
    text_content: Optional[str]
    html_content: Optional[str]
    has_attachments: bool
    attachment_count: int
    flags: List[str]
    size: int

    @classmethod
    def from_mail_message(cls, mail: MailMessage) -> 'MailDTO':
        """MailMessage 객체를 MailDTO로 변환"""
        # from_ 필드 파싱
        from_parts = mail.from_.split(
            '<') if '<' in mail.from_ else [mail.from_]
        from_name = from_parts[0].strip().strip(
            '"') if len(from_parts) > 1 else None
        from_email = from_parts[1].rstrip('>') if len(
            from_parts) > 1 else from_parts[0]

        return cls(
            uid=mail.uid,
            subject=mail.subject or "",
            from_email=from_email,
            from_name=from_name,
            to_emails=list(mail.to) if mail.to else [],
            cc_emails=list(mail.cc) if mail.cc else [],
            bcc_emails=list(mail.bcc) if mail.bcc else [],
            date=mail.date.isoformat() if mail.date else "",
            text_content=mail.text,
            html_content=mail.html,
            has_attachments=len(mail.attachments) > 0,
            attachment_count=len(mail.attachments),
            flags=list(mail.flags) if mail.flags else [],
            size=mail.size or 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return asdict(self)

    def to_json_string(self) -> str:
        """JSON 문자열로 변환"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_summary_text(self) -> str:
        """간단한 텍스트 요약 형태로 변환"""
        date_str = self.date[:19] if self.date else "Unknown"  # YYYY-MM-DDTHH:MM:SS
        from_display = self.from_name if self.from_name else self.from_email
        attachment_info = f" ({self.attachment_count}개 첨부)" if self.has_attachments else ""

        return f"{date_str} | {from_display} | {self.subject}{attachment_info}"

    def to_detailed_text(self) -> str:
        """상세한 텍스트 형태로 변환"""
        lines = [
            f"UID: {self.uid}",
            f"제목: {self.subject}",
            f"발신자: {self.from_name} <{self.from_email}>" if self.from_name else f"발신자: {self.from_email}",
            f"수신자: {', '.join(self.to_emails)}",
        ]

        if self.cc_emails:
            lines.append(f"참조: {', '.join(self.cc_emails)}")

        lines.extend([
            f"날짜: {self.date}",
            f"크기: {self.size:,} bytes",
            f"첨부파일: {self.attachment_count}개" if self.has_attachments else "첨부파일: 없음",
            f"플래그: {', '.join(self.flags) if self.flags else '없음'}",
        ])

        if self.text_content:
            preview = self.text_content[:200] + "..." if len(
                self.text_content) > 200 else self.text_content
            lines.append(f"내용 미리보기:\n{preview}")

        return "\n".join(lines)


class MailListDTO:
    """메일 목록 DTO"""

    def __init__(self, mails: List[MailMessage], page_info: Optional[Dict] = None):
        self.mails = [MailDTO.from_mail_message(mail) for mail in mails]
        self.page_info = page_info or {}
        self.total_count = len(self.mails)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "mails": [mail.to_dict() for mail in self.mails],
            "total_count": self.total_count,
            "page_info": self.page_info
        }

    def to_json_string(self) -> str:
        """JSON 문자열로 변환"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_summary_list(self) -> List[str]:
        """간단한 텍스트 목록으로 변환"""
        return [mail.to_summary_text() for mail in self.mails]

    def to_summary_text(self) -> str:
        """전체 목록을 하나의 텍스트로 변환"""
        if not self.mails:
            return "메일이 없습니다."

        lines = [f"메일 {self.total_count}개"]
        if self.page_info:
            if self.page_info.get('has_more'):
                lines[0] += f" (다음 페이지 있음)"
        lines.append("-" * 50)

        for i, mail in enumerate(self.mails, 1):
            lines.append(f"{i:2d}. {mail.to_summary_text()}")

        return "\n".join(lines)


# 편의 함수들
def mails_to_json(mails: List[MailMessage], page_info: Optional[Dict] = None) -> str:
    """메일 목록을 JSON 문자열로 변환하는 편의 함수"""
    mail_list = MailListDTO(mails, page_info)
    return mail_list.to_json_string()


def mails_to_text(mails: List[MailMessage], page_info: Optional[Dict] = None) -> str:
    """메일 목록을 텍스트로 변환하는 편의 함수"""
    mail_list = MailListDTO(mails, page_info)
    return mail_list.to_summary_text()


def mail_to_json(mail: MailMessage) -> str:
    """단일 메일을 JSON 문자열로 변환하는 편의 함수"""
    mail_dto = MailDTO.from_mail_message(mail)
    return mail_dto.to_json_string()


def mail_to_text(mail: MailMessage, detailed: bool = False) -> str:
    """단일 메일을 텍스트로 변환하는 편의 함수"""
    mail_dto = MailDTO.from_mail_message(mail)
    return mail_dto.to_detailed_text() if detailed else mail_dto.to_summary_text()
