import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.routes import health, counties, facilities, boundaries, sublocations, roads

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(health.router)
app.include_router(counties.router)
app.include_router(facilities.router)
app.include_router(boundaries.router)
app.include_router(sublocations.router)
app.include_router(roads.router)


@app.on_event("startup")
async def warmup():
    for attempt in range(5):
        try:
            from app.routes.boundaries import _load_and_simplify
            _load_and_simplify(0.01)
            print("✅ Boundary cache warmed up")
            return
        except Exception as e:
            print(f"⚠️ Warmup attempt {attempt+1}/5 failed: {str(e)[:100]}")
            time.sleep(3)
    print("⚠️ Warmup gave up after 5 attempts")


@app.get("/")
def root():
    return {"status": "ok", "project": settings.APP_NAME, "version": settings.APP_VERSION}
