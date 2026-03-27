from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv

# Import functions
from app import (
    get_products,
    generate_description,
    update_product_description,
    get_product_by_sku
)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"message": "API working"}


# =========================
# BULK GENERATE (ADMIN)
# =========================
@app.get("/generate")
def generate():
    try:
        products_data = get_products()
        products = products_data["data"]["products"]["edges"]

        for product in products:
            node = product["node"]

            title = node["title"]
            product_type = node.get("productType", "")
            vendor = node.get("vendor", "")
            product_id = node["id"]

            new_desc = generate_description(title, product_type, vendor)

            update_product_description(product_id, new_desc)

        return {"status": "All products updated"}

    except Exception as e:
        return {"error": str(e)}


# =========================
# CHAT API
# =========================
@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")

        url = "https://api.anthropic.com/v1/messages"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 300,
            "messages": [
                {"role": "user", "content": user_message}
            ],
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            return {"error": result["error"]}

        reply = result["content"][0]["text"]

        return {"reply": reply}

    except Exception as e:
        return {"error": str(e)}