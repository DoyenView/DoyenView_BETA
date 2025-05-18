import uvicorn
from api.fastapi_routes import fastapi_app

if __name__ == "__main__":
    uvicorn.run("api.fastapi_routes:fastapi_app", host="127.0.0.1", port=8800, reload=True)
