import argparse
import asyncio
import os
from mcp import Tool, stdio_server
from imap_tools import MailBox, AND
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from service.mail_service import MailService
from service.mail_dto import mails_to_json, mails_to_text, mail_to_json, mail_to_text
from data.folder import folder_info_list_to_folder_list

# -------
# 1. Global credentials (set by main function)
NAVER_ID = None
NAVER_PASSWORD = None

# -------
# 2. Server Instance
server = Server("naver-mail-mcp")

# -------
# 3. Tools

# 3.1. List Tools


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_mails",
            description="최근 N개 메일 목록 조회 (JSON 또는 텍스트 형태)",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_count": {
                        "type": "number",
                        "default": 10,
                        "description": "가져올 메일 개수"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "text"],
                        "default": "text",
                        "description": "출력 형태 (json: JSON 형태, text: 읽기 쉬운 텍스트(내용은 없음))"
                    }
                },
                "required": [],
            }
        ),
        Tool(
            name="list_mails_paginated",
            description="페이징을 지원하는 메일 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_size": {
                        "type": "number",
                        "default": 10,
                        "description": "한 페이지당 메일 개수"
                    },
                    "last_uid": {
                        "type": "string",
                        "description": "이전 페이지의 마지막 UID (다음 페이지 요청시 사용)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "text"],
                        "default": "text",
                        "description": "출력 형태 (json: JSON 형태, text: 읽기 쉬운 텍스트(내용은 없음))"
                    }
                },
                "required": [],
            }
        ),
        Tool(
            name="get_mail_detail",
            description="특정 메일의 상세 정보 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "uid": {
                        "type": "string",
                        "description": "조회할 메일의 UID"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "text"],
                        "default": "json",
                        "description": "출력 형태 (json: JSON 형태, text: 읽기 쉬운 텍스트(내용은 없음))"
                    }
                },
                "required": ["uid"],
            }
        ),
        # 폴더 관리 tools
        Tool(
            name="list_folders",
            description="메일 폴더 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            }
        ),
        Tool(
            name="create_folder",
            description="새 메일 폴더 생성",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_name": {
                        "type": "string",
                        "description": "생성할 폴더 이름"
                    }
                },
                "required": ["folder_name"],
            }
        ),
        Tool(
            name="delete_folder",
            description="메일 폴더 삭제",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_name": {
                        "type": "string",
                        "description": "삭제할 폴더 이름"
                    }
                },
                "required": ["folder_name"],
            }
        ),
        Tool(
            name="rename_folder",
            description="메일 폴더 이름 변경",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_folder_name": {
                        "type": "string",
                        "description": "기존 폴더 이름"
                    },
                    "new_folder_name": {
                        "type": "string",
                        "description": "새 폴더 이름"
                    }
                },
                "required": ["old_folder_name", "new_folder_name"],
            }
        ),
        # 메일 조작 tools
        Tool(
            name="move_mails",
            description="메일을 다른 폴더로 이동",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "이동할 메일들의 UID 목록"
                    },
                    "folder_name": {
                        "type": "string",
                        "description": "이동할 대상 폴더 이름"
                    }
                },
                "required": ["mail_uids", "folder_name"],
            }
        ),
        Tool(
            name="copy_mails",
            description="메일을 다른 폴더로 복사",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "복사할 메일들의 UID 목록"
                    },
                    "folder_name": {
                        "type": "string",
                        "description": "복사할 대상 폴더 이름"
                    }
                },
                "required": ["mail_uids", "folder_name"],
            }
        ),
        Tool(
            name="delete_mails",
            description="메일 삭제",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "삭제할 메일들의 UID 목록"
                    }
                },
                "required": ["mail_uids"],
            }
        ),
        Tool(
            name="mark_mails_read",
            description="메일을 읽음 상태로 변경",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "읽음 처리할 메일들의 UID 목록"
                    }
                },
                "required": ["mail_uids"],
            }
        ),
        Tool(
            name="mark_mails_unread",
            description="메일을 읽지 않음 상태로 변경",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "읽지 않음 처리할 메일들의 UID 목록"
                    }
                },
                "required": ["mail_uids"],
            }
        ),
        Tool(
            name="mark_mails_important",
            description="메일을 중요 상태로 변경",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "중요 처리할 메일들의 UID 목록"
                    }
                },
                "required": ["mail_uids"],
            }
        ),
        Tool(
            name="mark_mails_unimportant",
            description="메일을 중요하지 않음 상태로 변경",
            inputSchema={
                "type": "object",
                "properties": {
                    "mail_uids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "중요하지 않음 처리할 메일들의 UID 목록"
                    }
                },
                "required": ["mail_uids"],
            }
        ),
        Tool(
            name="debug_env",
            description="환경 변수 및 서버 상태 디버깅",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }
        ),
        Tool(
            name="ping",
            description="서버 상태 확인",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }
        )
    ]

# -------
# 4. Tool Functions


@server.call_tool()
async def handle_call_tool(name: Tool, args: dict | None):
    if not args:
        args = {}

    try:
        # 글로벌 변수에서 자격 증명 가져오기
        if not NAVER_ID or not NAVER_PASSWORD:
            return [TextContent(type="text", text="자격 증명이 설정되지 않았습니다. 서버를 --naver-id와 --naver-password 인수로 시작해주세요.")]

        # 메일 서비스 인스턴스 생성
        mail_service = MailService(id=NAVER_ID, password=NAVER_PASSWORD)

        if name == "list_mails":
            max_count = args.get("max_count", 10)
            output_format = args.get("format", "text")

            mails = mail_service.get_mails(max_count=max_count)

            if output_format == "json":
                content = mails_to_json(mails)
            else:
                content = mails_to_text(mails)

            return [TextContent(type="text", text=content)]

        elif name == "list_mails_paginated":
            page_size = args.get("page_size", 10)
            last_uid = args.get("last_uid")
            output_format = args.get("format", "text")

            result = mail_service.get_mails_paginated(
                page_size=page_size,
                last_uid=last_uid
            )

            mails = result['mails']
            page_info = {
                'last_uid': result['last_uid'],
                'has_more': result['has_more']
            }

            if output_format == "json":
                content = mails_to_json(mails, page_info)
            else:
                content = mails_to_text(mails, page_info)

            return [TextContent(type="text", text=content)]

        elif name == "get_mail_detail":
            uid = args.get("uid")
            output_format = args.get("format", "json")

            if not uid:
                return [TextContent(type="text", text="UID가 필요합니다.")]

            # 특정 UID의 메일 가져오기
            with MailBox("imap.naver.com").login(NAVER_ID, NAVER_PASSWORD, "INBOX") as mailbox:
                mails = list(mailbox.fetch(criteria=AND(uid=uid)))

                if not mails:
                    return [TextContent(type="text", text=f"UID {uid}에 해당하는 메일을 찾을 수 없습니다.")]

                mail = mails[0]

                if output_format == "json":
                    content = mail_to_json(mail)
                else:
                    content = mail_to_text(mail, detailed=True)

            return [TextContent(type="text", text=content)]

        elif name == "debug_env":
            debug_info = {
                "naver_id": "***" if NAVER_ID else None,
                "naver_password": "***" if NAVER_PASSWORD else None,
                "working_dir": os.getcwd(),
            }
            return [TextContent(type="text", text=f"Debug Info:\n{debug_info}")]

        elif name == "ping":
            return [TextContent(type="text", text="MCP Server is running")]

        # 폴더 관리 tools
        elif name == "list_folders":
            folder_info_list = mail_service.get_folder_list()
            folder_list = folder_info_list_to_folder_list(folder_info_list)
            import json
            content = json.dumps(
                [folder.to_dict() for folder in folder_list], ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=content)]

        elif name == "create_folder":
            folder_name = args.get("folder_name")
            if not folder_name:
                return [TextContent(type="text", text="폴더 이름이 필요합니다.")]

            mail_service.create_folder(folder_name)
            return [TextContent(type="text", text=f"폴더 '{folder_name}'가 성공적으로 생성되었습니다.")]

        elif name == "delete_folder":
            folder_name = args.get("folder_name")
            if not folder_name:
                return [TextContent(type="text", text="폴더 이름이 필요합니다.")]

            # 폴더 존재 여부 확인
            if not mail_service.is_folder_exists(folder_name):
                return [TextContent(type="text", text=f"폴더 '{folder_name}'가 존재하지 않습니다.")]

            mail_service.delete_folder(folder_name)
            return [TextContent(type="text", text=f"폴더 '{folder_name}'가 성공적으로 삭제되었습니다.")]

        elif name == "rename_folder":
            old_folder_name = args.get("old_folder_name")
            new_folder_name = args.get("new_folder_name")

            if not old_folder_name or not new_folder_name:
                return [TextContent(type="text", text="기존 폴더 이름과 새 폴더 이름이 모두 필요합니다.")]

            # 기존 폴더 존재 여부 확인
            if not mail_service.is_folder_exists(old_folder_name):
                return [TextContent(type="text", text=f"폴더 '{old_folder_name}'가 존재하지 않습니다.")]

            mail_service.rename_folder(old_folder_name, new_folder_name)
            return [TextContent(type="text", text=f"폴더 '{old_folder_name}'가 '{new_folder_name}'로 성공적으로 변경되었습니다.")]

        # 메일 조작 tools
        elif name == "move_mails":
            mail_uids = args.get("mail_uids", [])
            folder_name = args.get("folder_name")

            if not mail_uids or not folder_name:
                return [TextContent(type="text", text="메일 UID 목록과 폴더 이름이 필요합니다.")]

            # 폴더 존재 여부 확인
            if not mail_service.is_folder_exists(folder_name):
                return [TextContent(type="text", text=f"폴더 '{folder_name}'가 존재하지 않습니다.")]

            mail_service.move_mails(mail_uids, folder_name)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 '{folder_name}' 폴더로 성공적으로 이동되었습니다.")]

        elif name == "copy_mails":
            mail_uids = args.get("mail_uids", [])
            folder_name = args.get("folder_name")

            if not mail_uids or not folder_name:
                return [TextContent(type="text", text="메일 UID 목록과 폴더 이름이 필요합니다.")]

            # 폴더 존재 여부 확인
            if not mail_service.is_folder_exists(folder_name):
                return [TextContent(type="text", text=f"폴더 '{folder_name}'가 존재하지 않습니다.")]

            mail_service.copy_mails(mail_uids, folder_name)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 '{folder_name}' 폴더로 성공적으로 복사되었습니다.")]

        elif name == "delete_mails":
            mail_uids = args.get("mail_uids", [])

            if not mail_uids:
                return [TextContent(type="text", text="삭제할 메일 UID 목록이 필요합니다.")]

            mail_service.delete_mails(mail_uids)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 성공적으로 삭제되었습니다.")]

        elif name == "mark_mails_read":
            mail_uids = args.get("mail_uids", [])

            if not mail_uids:
                return [TextContent(type="text", text="읽음 처리할 메일 UID 목록이 필요합니다.")]

            mail_service.mark_as_read(mail_uids)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 읽음 상태로 변경되었습니다.")]

        elif name == "mark_mails_unread":
            mail_uids = args.get("mail_uids", [])

            if not mail_uids:
                return [TextContent(type="text", text="읽지 않음 처리할 메일 UID 목록이 필요합니다.")]

            mail_service.mark_as_unread(mail_uids)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 읽지 않음 상태로 변경되었습니다.")]

        elif name == "mark_mails_important":
            mail_uids = args.get("mail_uids", [])

            if not mail_uids:
                return [TextContent(type="text", text="중요 처리할 메일 UID 목록이 필요합니다.")]

            mail_service.mark_as_important(mail_uids)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 중요 상태로 변경되었습니다.")]

        elif name == "mark_mails_unimportant":
            mail_uids = args.get("mail_uids", [])

            if not mail_uids:
                return [TextContent(type="text", text="중요하지 않음 처리할 메일 UID 목록이 필요합니다.")]

            mail_service.mark_as_unimportant(mail_uids)
            return [TextContent(type="text", text=f"{len(mail_uids)}개의 메일이 중요하지 않음 상태로 변경되었습니다.")]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        error_msg = f"Error occurred: {str(e)}\nType: {type(e).__name__}\nArgs: {args}"
        import traceback
        error_msg += f"\nTraceback:\n{traceback.format_exc()}"
        return [TextContent(type="text", text=error_msg)]


async def main(naver_id: str, naver_password: str):
    # 글로벌 변수에 자격 증명 설정
    global NAVER_ID, NAVER_PASSWORD
    NAVER_ID = naver_id
    NAVER_PASSWORD = naver_password

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="naver-mail-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Naver Mail MCP Server')
    parser.add_argument('--naver-id',
                        required=True,
                        help='Naver ID')
    parser.add_argument('--naver-password',
                        required=True,
                        help='Naver Password')

    args = parser.parse_args()
    asyncio.run(main(naver_id=args.naver_id,
                naver_password=args.naver_password))
