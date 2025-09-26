import os
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from basics.browser_toolkit import BrowserUseToolkit
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
browser_toolkit = BrowserUseToolkit()
# TOOL 1: Form URL Finder using OpenAI + Serper.dev + Optional local map
def load_local_map():
    try:
        with open("form_map.json") as f:
            return json.load(f)
    except:
        return {}

def search_with_serper(query: str) -> str:
    api_key = os.getenv("SERPER_API_KEY", "7d21f08a339b43f88c9cd0c39887ccd166bd970f")
    if not api_key:
        print("❌ SERPER_API_KEY not found in .env file.")
        return ""

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    data = {"q": query}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("❌ Serper.dev search failed:", response.text)
        return ""

    results = response.json().get("organic", [])
    for r in results:
        link = r.get("link", "")
        return link
    return ""

def openai_complete(prompt: str, temperature: float = 0.2, max_tokens: int = 64) -> str:
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"].strip()

def find_form_url(user_prompt: str) -> str:
    # Step 0: Check local DB
    cache = load_local_map()
    for key, url in cache.items():
        if key in user_prompt.lower().replace(" ", "_"):
            return url

    # Step 1: Generate search query using OpenAI
    prompt = f'''
You are a government assistant.
Convert this user request into a search query to find an Indian government form URL.

Examples:
- User: "I want to apply for a caste certificate in Bihar"
  → caste certificate apply site:gov.in Bihar

User: {user_prompt}
Query:
'''
    raw_query = openai_complete(prompt, max_tokens=32)
    query = raw_query.split(",")[0].strip()
    print(f"🔍 Final Serper Query: {query}")

    # Step 2: Search using Serper
    return search_with_serper(query)

def extract_form_fields_sync(url: str) -> List[Dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        inputs = page.query_selector_all("input, select, textarea")
        fields = []

        for input_element in inputs:
            field_type = input_element.get_attribute("type") or input_element.evaluate("el => el.tagName.toLowerCase()")
            name = input_element.get_attribute("name") or input_element.get_attribute("id")
            label = input_element.get_attribute("aria-label") or input_element.get_attribute("placeholder") or name

            if name and label:
                fields.append({
                    "label": label.strip(),
                    "name": name.strip(),
                    "type": field_type.strip() if field_type else "text",
                })

        browser.close()
        return fields

async def extract_form_fields(url: str) -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        inputs = await page.query_selector_all("input, select, textarea")
        fields = []

        for input_element in inputs:
            field_type = await input_element.get_attribute("type")
            if not field_type:
                field_type = await input_element.evaluate("el => el.tagName.toLowerCase()")
            name = await input_element.get_attribute("name")
            if not name:
                name = await input_element.get_attribute("id")
            label = await input_element.get_attribute("aria-label")
            if not label:
                label = await input_element.get_attribute("placeholder")
            if not label:
                label = name

            if name and label:
                fields.append({
                    "label": label.strip(),
                    "name": name.strip(),
                    "type": field_type.strip() if field_type else "text",
                })

        await browser.close()
        return fields

def match_and_generate_prompt(user_data: Dict, form_fields: List[Dict], form_url: str) -> str:
    input_text = f"Form URL: {form_url}\n\nForm Fields:\n"
    for f in form_fields:
        input_text += f"- {f['label']} (name: {f['name']}, type: {f['type']})\n"

    input_text += "\nUser Data:\n"
    for k, v in user_data.items():
        input_text += f"- {k}: {v}\n"

    print(f"Input text : {input_text}")

    prompt = f'''
Given a list of form fields and user data, generate natural language instructions to fill the form at the given URL.
If any field is missing from user data, assume a default safe placeholder like "123456" keep only that field that you think it is necessary like firstName,lastName.

Format:
- Mention the form URL
- For each field, write what value to set
- End with "Then submit the form."

{input_text}

Instructions:
'''
    res = openai_complete(prompt, max_tokens=256)
    print(f"response from third tool {res}")
    return res

async def run_fallback_form_filler(user_prompt: str, user_data: Dict):
    form_url = find_form_url(user_prompt)
    if not form_url:
        print("Could not find the form URL.")
        return
    print("✅ Form URL:", form_url)

    form_fields = await extract_form_fields(form_url)
    print("\n🧾 Extracted Form Fields:")
    for field in form_fields:
        print(f"• Label: {field.get('label')}, Name: {field.get('name')}, Type: {field.get('type')}")

    print("\n🧠 Calling third tool:")
    browser_prompt = match_and_generate_prompt(user_data, form_fields, form_url)
    print("\n🧠 Browser-Use Prompt:")
    print(browser_prompt)
    await browser_toolkit.execute_browser_task(browser_prompt) 