from imap_tools import MailBox, MailMessage, AND


class MailService:
    def __init__(self, id: str, password: str):
        self.id = id
        self.password = password

    def _get_mailbox_client(self) -> MailBox:
        return MailBox("imap.naver.com").login(
            self.id, self.password, "INBOX"
        )

    def get_mails(self, max_count: int = 10) -> list[MailMessage]:
        with self._get_mailbox_client() as mailbox:
            return list(mailbox.fetch(limit=max_count, reverse=True))

    def get_mails_paginated(self, page_size: int = 10, last_uid: str = None) -> dict:
        """
        UID 기반 페이징으로 메일을 가져옵니다.

        Args:
            page_size: 한 페이지당 메일 개수
            last_uid: 이전 페이지의 마지막 UID (다음 페이지를 가져올 때 사용)

        Returns:
            {
                'mails': list[MailMessage],
                'last_uid': str,  # 다음 페이지 요청시 사용할 UID
                'has_more': bool  # 다음 페이지가 있는지
            }
        """
        with self._get_mailbox_client() as mailbox:
            # 검색 조건 설정
            if last_uid:
                # 특정 UID보다 작은 메일들만 가져오기 (reverse=True이므로)
                criteria = AND(uid=f"1:{last_uid}")
                # UID로 정렬하여 last_uid보다 작은 것들 중에서 최신순으로
                mails = list(mailbox.fetch(
                    criteria=criteria,
                    limit=page_size + 1,  # +1로 다음 페이지 존재 여부 확인
                    reverse=True
                ))
                # last_uid는 제외
                mails = [mail for mail in mails if mail.uid != last_uid]
            else:
                # 첫 페이지
                mails = list(mailbox.fetch(
                    limit=page_size + 1,
                    reverse=True
                ))

            # 다음 페이지 존재 여부 확인
            has_more = len(mails) > page_size
            if has_more:
                mails = mails[:page_size]

            # 마지막 UID 추출
            last_uid = mails[-1].uid if mails else None

            return {
                'mails': mails,
                'last_uid': last_uid,
                'has_more': has_more
            }

    def get_mails_by_range(self, start_index: int = 0, count: int = 10) -> list[MailMessage]:
        """
        인덱스 기반 페이징 (비추천: 메일이 추가/삭제되면 인덱스가 변경됨)
        """
        with self._get_mailbox_client() as mailbox:
            # 전체 메일 UID 목록 가져오기
            all_uids = mailbox.uids()
            all_uids.reverse()  # 최신순 정렬

            # 범위에 해당하는 UID만 선택
            target_uids = all_uids[start_index:start_index + count]

            if not target_uids:
                return []

            # 선택된 UID들의 메일 가져오기
            return list(mailbox.fetch(
                criteria=AND(uid=target_uids),
                reverse=True
            ))


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    mail_service = MailService(
        id=os.getenv("NAVER_ID"),
        password=os.getenv("NAVER_PASSWORD")
    )

    # 기존 방식
    print("=== 기존 방식 ===")
    mails = mail_service.get_mails(max_count=5)
    for mail in mails:
        print(f"{mail.date} | {mail.from_} | {mail.subject}")

    print("\n=== UID 기반 페이징 ===")
    # 첫 번째 페이지
    page1 = mail_service.get_mails_paginated(page_size=3)
    print(f"첫 번째 페이지 (has_more: {page1['has_more']}):")
    for mail in page1['mails']:
        print(f"{mail.date} | {mail.from_} | {mail.subject} | UID: {mail.uid}")

    # 두 번째 페이지
    if page1['has_more']:
        print(f"\n두 번째 페이지:")
        page2 = mail_service.get_mails_paginated(
            page_size=3,
            last_uid=page1['last_uid']
        )
        for mail in page2['mails']:
            print(f"{mail.date} | {mail.from_} | {mail.subject} | UID: {mail.uid}")
