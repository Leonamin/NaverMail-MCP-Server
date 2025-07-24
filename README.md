# Mail MCP Server

## 실행환경 설정

## MCP Server 연동

### 테스트
1. inspector 다운로드 및 실행(node가 설치되어있어야 함)
```sh
npx @modelcontextprotocol/inspector uv run server.py --naver-id your-id --naver-password your-password
```

2. Session Token 복사
```
Starting MCP inspector...
⚙️ Proxy server listening on 127.0.0.1:6277
🔑 Session token: 3518ab7ad6026be0f0ad8d5c0ef9b2c853e48ed911fe1317eb9b0ed48bdd980e <--- 이거 복사
Use this token to authenticate requests or set DANGEROUSLY_OMIT_AUTH=true to disable auth

🔗 Open inspector with token pre-filled:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=3518ab7ad6026be0f0ad8d5c0ef9b2c853e48ed911fe1317eb9b0ed48bdd980e

🔍 MCP Inspector is up and running at http://127.0.0.1:6274 🚀
```
3. 127.0.0.1:6274 접속 및 Configuration 설정
**Configuration** -> **Proxy Session Token** 에 **2. Session Token 복사**에서 복사한 키 설정

4. Connect 실행


### Claude Desktop

```json
{
  "mcpServers": {
    "naver-mail": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/naver-mail-mcp",
        "run",
        "server.py"
        "--naver-id"
        "your-id"
        "--naver-password"
        "your-password"
      ]
    }
  }
}
```
