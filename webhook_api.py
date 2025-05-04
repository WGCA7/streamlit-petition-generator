from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

app = FastAPI()

# Allow CORS so Zapier can post
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook")
async def receive_data(request: Request):
    body = await request.json()

    with open("latest_webhook_data.json", "w") as f:
        json.dump(body, f, indent=2)

    return {"status": "received", "data": body}

if __name__ == "__main__":
    uvicorn.run("webhook_api:app", host="0.0.0.0", port=8000, reload=True)
