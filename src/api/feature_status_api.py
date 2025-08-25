"""
Feature Status API voor real-time dashboard updates
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Feature Status API")

# CORS voor browser toegang
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Cache voor performance
_feature_cache = None
_cache_timestamp = None
CACHE_DURATION = 300  # 5 minuten


@app.get("/api/feature-status")
async def get_feature_status():
    """Get current feature status from GitHub or cache"""
    global _feature_cache, _cache_timestamp

    # Check cache
    if _feature_cache and _cache_timestamp:
        cache_age = (datetime.now(timezone.utc) - _cache_timestamp).seconds
        if cache_age < CACHE_DURATION:
            return _feature_cache

    # Load from JSON file (or fetch from GitHub)
    try:
        json_path = (
            Path(__file__).parent.parent.parent
            / "docs"
            / "architectuur"
            / "feature-status.json"
        )
        with open(json_path) as f:
            data = json.load(f)

        # Update cache
        _feature_cache = data
        _cache_timestamp = datetime.now(timezone.utc)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feature-status/summary")
async def get_feature_summary():
    """Get summary statistics only"""
    data = await get_feature_status()
    return {
        "lastUpdated": data.get("lastUpdated"),
        "statistics": data.get("statistics"),
        "epicCount": len(data.get("epics", [])),
    }


@app.get("/api/feature-status/epic/{epic_id}")
async def get_epic_status(epic_id: str):
    """Get status for specific epic"""
    data = await get_feature_status()

    for epic in data.get("epics", []):
        if epic["id"] == epic_id:
            return epic

    raise HTTPException(status_code=404, detail=f"Epic {epic_id} not found")


@app.get("/api/feature-status/by-status/{status}")
async def get_features_by_status(status: str):
    """Get all features with specific status"""
    valid_statuses = ["complete", "in-progress", "not-started"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    data = await get_feature_status()
    features = []

    for epic in data.get("epics", []):
        for feature in epic.get("features", []):
            if feature["status"] == status:
                features.append(
                    {**feature, "epicId": epic["id"], "epicName": epic["name"]}
                )

    return {"status": status, "count": len(features), "features": features}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
