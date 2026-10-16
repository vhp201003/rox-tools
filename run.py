import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ROX Wiki & DPS Simulator Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to listen on")
    parser.add_argument("--reload", action=argparse.BooleanOptionalAction, default=True, help="Enable/disable auto-reload")
    args = parser.parse_args()

    uvicorn.run("rox_wiki.server:app", host=args.host, port=args.port, reload=args.reload, app_dir="src")
