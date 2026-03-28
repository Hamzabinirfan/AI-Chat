import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

SHOP = "breechesdotcom.myshopify.com"
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SHOPIFY_URL = f"https://{SHOP}/admin/api/2024-10/graphql.json"

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/")
def home():
    return "Server is running 🚀"

# =========================
# SHOPIFY FUNCTIONS
# =========================
def get_products():
    query = """
    {
      products(first: 10) {
        edges {
          node {
            id
            title
            productType
            vendor
            descriptionHtml
            variants(first: 5) {
              edges {
                node {
                  sku
                  price
                  availableForSale
                }
              }
            }
          }
        }
      }
    }
    """
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    }
    response = requests.post(SHOPIFY_URL, headers=headers, json={"query": query})
    response.raise_for_status()
    return response.json()


def format_products_for_ai(products_data):
    edges = products_data.get("data", {}).get("products", {}).get("edges", [])
    product_list = []
    for edge in edges:
        node = edge["node"]
        variants = node.get("variants", {}).get("edges", [])
        prices = [v["node"]["price"] for v in variants if v["node"]["price"]]
        price_str = f"${prices[0]}" if prices else "N/A"
        product_list.append(f"- {node['title']} | Type: {node['productType']} | Price: {price_str}")
    return "\n".join(product_list)


# =========================
# CHAT ENDPOINT
# =========================
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    try:
        data = request.get_json()
        message = data.get("message", "")

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Shopify se products fetch karo
        try:
            products_data = get_products()
            products_text = format_products_for_ai(products_data)
        except Exception:
            products_text = "Product information currently unavailable."

        # Claude AI call with products context
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 500,
                "system": f"""You are a helpful shopping assistant for Breeches.com, an equestrian clothing store.
Answer customer questions helpfully and concisely.
Always respond in the same language the customer uses.

Here are our current products:
{products_text}

Use this product information to answer customer queries about availability, pricing, and product types.
If a product is not in the list, say it's not currently available.""",
                "messages": [
                    {"role": "user", "content": message}
                ]
            }
        )

        result = response.json()
        reply = result["content"][0]["text"]

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

## Steps:

**1. Anthropic API Key lao:**
- `https://console.anthropic.com` pe jaao → API Keys → New Key banao

**2. Render → Environment tab mein add karo:**
```
ANTHROPIC_API_KEY = sk-ant-xxxxxxxx
SHOPIFY_TOKEN = (pehle se set hai)