"""Print MCP config using absolute paths. Does not collect or embed secrets."""
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
command = root / '.venv' / ('Scripts/engine-mcp.exe' if sys.platform == 'win32' else 'bin/engine-mcp')
print(json.dumps({'mcpServers': {'market-jury': {'command': str(command), 'env': {
    'ENGINE_URL': 'http://127.0.0.1:8008', 'ENGINE_API_KEY': 'REPLACE_LOCALLY_WITH_YOUR_ENGINE_KEY'
}}}}, indent=2))
