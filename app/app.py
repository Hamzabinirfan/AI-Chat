import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOP = "breechesdotcom.myshopify.com"
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SHOPIFY_URL = f"https://{SHOP}/admin/api/2026-01/graphql.json"


# =========================
# GET PRODUCTS
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

    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    return data


# =========================
# GET PRODUCT BY SKU
# =========================
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
# CLAUDE DESCRIPTION
# =========================
def generate_description(title, product_type, vendor):
    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    prompt = f"""
Write a professional Shopify product description in HTML.

Product title: {title}
Product type: {product_type}
Brand: {vendor}

Rules:
- concise
- benefit-focused
- no false claims
- include short paragraph + 3 bullet points
"""

    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 400,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise Exception(data["error"])

    return data["content"][0]["text"]


# =========================
# UPDATE PRODUCT
# =========================
def update_product_description(product_id, new_description):
    mutation = """
    mutation productUpdate($input: ProductUpdateInput!) {
      productUpdate(product: $input) {
        product {
          id
          title
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "id": product_id,
            "descriptionHtml": new_description,
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    }

    response = requests.post(
        SHOPIFY_URL,
        headers=headers,
        json={"query": mutation, "variables": variables},
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(data["errors"])

    user_errors = data.get("data", {}).get("productUpdate", {}).get("userErrors", [])

    if user_errors:
        raise Exception(user_errors)

    return data