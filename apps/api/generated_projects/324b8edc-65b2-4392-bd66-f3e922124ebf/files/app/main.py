from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import news, user, auth

app = FastAPI(
    title="Mira News API",
    description="API for Mira News, an AI-powered platform delivering unbiased news summaries.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(user.router, prefix="/api", tags=["users"])
app.include_router(news.router, prefix="/api", tags=["news"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
