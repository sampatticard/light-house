import asyncio
import json
import requests
import os
from typing import List, Dict
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.tools import tool
from browser_use import Agent
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import asyncio
import json
import requests
import os
from typing import List, Dict
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.tools import tool
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from langchain_ollama import ChatOllama

load_dotenv()

# Use local Ollama model (phi3:mini)
llm = OllamaLLM(model="phi3:mini")
# TOOL 1: Form URL Finder using LLM + Serper.dev + Optional local map

def load_local_map():
    try:
        with open("form_map.json") as f:
            return json.load(f)
    except:
        return {}

def search_with_serper(query: str) -> str:
    api_key = "7d21f08a339b43f88c9cd0c39887ccd166bd970f"
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

@tool
def find_form_url(user_prompt: str) -> str:
    """Find official form URL from a .gov.in or .nic.in domain, using local cache and LLM-generated Serper.dev search."""
    # Step 0: Check local DB
    cache = load_local_map()
    for key, url in cache.items():
        if key in user_prompt.lower().replace(" ", "_"):
            return url

    # Step 1: Generate search query
    prompt = PromptTemplate.from_template(
        '''
        You are a government assistant.
        Convert this user request into a search query to find an Indian government form URL.

        Examples:
        - User: "I want to apply for a caste certificate in Bihar"
          → caste certificate apply site:gov.in Bihar

        User: {user_prompt}
        Query:
        '''
    )
    chain = prompt | llm
    raw_query = chain.invoke({"user_prompt": user_prompt}).strip()
    query = raw_query.split(",")[0].strip()
    print(f"🔍 Final Serper Query: {query}")

    # Step 2: Search using Serper
    return search_with_serper(query)

# TOOL 2: Form Field Extractor using Playwright

def extract_form_fields(url: str) -> List[Dict]:
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
# TOOL 3: Match user data with form fields and generate browser-use prompt

def match_and_generate_prompt(user_data: Dict, form_fields: List[Dict], form_url: str) -> str:
    # Serialize form fields and user data
    input_text = f"Form URL: {form_url}\n\nForm Fields:\n"
    for f in form_fields:
        input_text += f"- {f['label']} (name: {f['name']}, type: {f['type']})\n"

    input_text += "\nUser Data:\n"
    for k, v in user_data.items():
        input_text += f"- {k}: {v}\n"

    print(f"Input text : {input_text}")

    # Prompt LLM to reason and build natural language browser-use instructions
    template = PromptTemplate.from_template(
        '''
        Given a list of form fields and user data, generate natural language instructions to fill the form at the given URL.
        If any field is missing from user data, assume a default safe placeholder like "123456" keep only that field that you think it is necessary
        like firstName,lastName.

        Format:
        - Mention the form URL
        - For each field, write what value to set
        - End with "Then submit the form."

        {input_text}

        Instructions:
        '''
    )
    chain = template | llm
    res = chain.invoke({"input_text": input_text}).strip()
    print(f"response from third tool {res}")
    return res



async def execute_browser_task(prompt: str):
    print("\n🌐 Executing browser-use task...\n")
    llm=ChatOllama(model="qwen2.5")
    agent = Agent(
        task=prompt,
        llm=llm,
    )
    result = await agent.run()
    print("\n✅ Browser-Use Result:\n", result)


# MAIN WORKFLOW

async def main():
    user_prompt = "apply for pan card"
    user_data = {
        "name": "Yash Gupta",
        "dob": "2000-01-01",
        "father's name": "Raj Gupta",
        "address": "123 Main Street, Bihar",
    }

    # Tool 1: Get URL
    form_url = find_form_url.invoke(user_prompt)
    if not form_url:
        print("Could not find the form URL.")
        return
    print("✅ Form URL:", form_url)

    # Tool 2: Extract fields
    form_fields = await extract_form_fields(form_url)
    print("\n🧾 Extracted Form Fields:")
    for field in form_fields:
        print(f"• Label: {field.get('label')}, Name: {field.get('name')}, Type: {field.get('type')}")

    # Tool 3: Match fields and generate browser-use prompt
    print("\n🧠 Calling third tool:")
    browser_prompt = match_and_generate_prompt(user_data, form_fields, form_url)
    print("\n🧠 Browser-Use Prompt:")
    print(browser_prompt)
    await execute_browser_task(browser_prompt)

if __name__ == "__main__":
    asyncio.run(main())
