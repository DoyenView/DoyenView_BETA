from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.chiefs.chief_router import route_to_chief

fastapi_app = FastAPI(title="DoyenView Chief API")

@fastapi_app.post("/api/execute")
async def execute_command(request: Request):
    data = await request.json()
    command = data.get("command")
    if not command:
        return JSONResponse(content={"reply": "No command provided."}, status_code=400)

    reply = route_to_chief(command)
    return JSONResponse(content={"reply": reply})
