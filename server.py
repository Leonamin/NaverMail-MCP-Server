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
    asyncio.run(main(naver_id=args.naver_id, naver_password=args.naver_password))
