"""
Run the Code Weaver Pro API server

Usage:
    python run.py

Or with uvicorn directly:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )
