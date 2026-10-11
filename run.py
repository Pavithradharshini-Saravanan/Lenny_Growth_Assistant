import uvicorn

if __name__ == "__main__":
    print("[Server] Starting The Lenny Growth Assistant server on http://localhost:8000...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
