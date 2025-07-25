from dataclasses import asdict, dataclass
import os
from typing import Any, Dict, List
from imap_tools import FolderInfo


@dataclass
class Folder:
    """메일 폴더 객체"""

    name: str
    delim: str
    flags: List[str]

    @classmethod
    def from_imap_tools_folder(cls, folder: FolderInfo) -> 'Folder':
        return cls(
            name=folder.name,
            delim=folder.delim,
            flags=folder.flags
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json_string(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def folder_info_list_to_folder_list(folder_info_list: List[FolderInfo]) -> List[Folder]:
    return [Folder.from_imap_tools_folder(folder) for folder in folder_info_list]

if __name__ == "__main__":
    from service.mail_service import MailService
    from dotenv import load_dotenv
    load_dotenv()

    mail_service = MailService(
        id=os.getenv("NAVER_ID"),
        password=os.getenv("NAVER_PASSWORD")
    )

    folder_info_list = mail_service.get_folder_list()

    folder_list = folder_info_list_to_folder_list(folder_info_list)

    print("\n".join(forder.to_json_string() for forder in folder_list))

    
