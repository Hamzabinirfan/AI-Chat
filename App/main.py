import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

# =========================
# ENV VARIABLES
# =========================
SHOP = "breechesdotcom.myshopify.com"
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not SHOPIFY_TOKEN or not ANTHROPIC_API_KEY:
    print("⚠️ Missing environment variables")

SHOPIFY_URL = f"https://{SHOP}/admin/api/2024-10/graphql.json"

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return "Server is running 🚀"

@app.route("/products")
def products():
    return jsonify(get_products())

@app.route("/product/<sku>")
def product_by_sku(sku):
    product = get_product_by_sku(sku)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)

# ✅ NEW: CHAT ENDPOINT (FOR SHOPIFY)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Simple response (you can connect AI later)
    reply = f"🤖 You said: {user_message}"

    return jsonify({"reply": reply})

# =========================
# SHOPIFY FUNCTIONS
# =========================
def get_products():
    query = """
    {
      products(first: 5) {
        edges {
          node {
            id
            title
            productType
            vendor
            descriptionHtml
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


def get_product_by_sku(sku):
    query = f"""
    {{
      productVariants(first: 1, query: "sku:{sku}") {{
        edges {{
          node {{
            sku
            product {{
              id
              title
              descriptionHtml
              productType
              vendor
            }}
          }}
        }}
      }}
    }}
    """

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    }

    response = requests.post(SHOPIFY_URL, headers=headers, json={"query": query})
    response.raise_for_status()

    data = response.json()

    edges = data.get("data", {}).get("productVariants", {}).get("edges", [])

    if not edges:
        return None

    return edges[0]["node"]["product"]

# =========================
# RUN SERVER (LOCAL TEST)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)