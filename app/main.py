from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.api_v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
# if settings.BACKEND_CORS_ORIGINS:
#     origins = settings.BACKEND_CORS_ORIGINS # This should be the list of origins
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=origins,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# (Removed debug print statement for registered routes)

if __name__ == "__main__":
    import uvicorn
    # This is for local development running `python app/main.py`
    # Use port 7777 to avoid conflicts with other services
    print("Starting Digital Twin Platform API on http://127.0.0.1:7777")
    uvicorn.run(app, host="127.0.0.1", port=7777)