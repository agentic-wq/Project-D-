"""Shared utilities for the Project D Web UI.

Currently contains the Google Maps scraping helper used by the ABC Create flow.
"""
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


def fetch_related_items(query: str, limit: int = 20) -> list[str]:
    """Fetch first N place names from Google Maps search results."""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        encoded_query = quote_plus(query)
        print(f"Navigating to Google Maps search for: {query}")
        print(f"Encoded query: {encoded_query}")
        maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        print(f"Maps URL: {maps_url}")
        driver.get(maps_url)

        import time
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        items: list[str] = []
        seen: set[str] = set()

        blocked_tokens = {
            "directions",
            "website",
            "call",
            "share",
            "save",
            "nearby",
            "send to your phone",
            "view all",
            "google maps",
            "open now",
            "closed",
            "sponsored",
        }

        def is_valid_place_name(name: str) -> bool:
            normalized = " ".join(name.split()).strip()
            if len(normalized) < 2 or len(normalized) > 120:
                return False
            low = normalized.casefold()
            if any(token in low for token in blocked_tokens):
                return False
            if any(ch in normalized for ch in ("$", "EUR", "GBP")):
                return False
            if normalized.replace(" ", "").isdigit():
                return False
            return True

        def collect_place_names() -> None:
            place_links = driver.find_elements(By.XPATH, "//div[@role='feed']//a[contains(@href, '/maps/place')]")
            if not place_links:
                place_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/place')]")
            for link in place_links:
                if len(items) >= limit:
                    return
                raw = (link.get_attribute("aria-label") or link.text or "").strip()
                if not raw:
                    continue
                name = raw.split("\n", 1)[0].strip()
                if not is_valid_place_name(name):
                    continue
                if name not in seen:
                    seen.add(name)
                    items.append(name)

        feed = None
        try:
            feed = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='feed']")))
        except Exception:
            feed = None

        stagnation = 0
        previous_count = -1
        for _ in range(45):
            collect_place_names()
            if len(items) >= limit:
                break

            if len(items) == previous_count:
                stagnation += 1
            else:
                stagnation = 0
                previous_count = len(items)

            if stagnation >= 6:
                break

            if feed is not None:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", feed)
            else:
                driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.6)

        collect_place_names()
        return items[:limit]
    except Exception as exc:
        print(f"Chrome Maps search error: {exc}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            driver.quit()


def fetch_related_items_agentic(category: str, limit: int = 3) -> dict:
    """Generate A–Z items using an AI agent with LangGraph.
    
    Uses LangGraph to orchestrate LLM-based generation of examples for each A–Z key.
    
    Args:
        category: The category to generate items for (e.g., "Animals", "Foods")
        limit: Max items per A–Z key (default: 3)
    
    Returns:
        dict: Mapping of A–Z keys to lists of generated items
    """
    import os
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("OPENAI_API_KEY not set. Agentic generation requires OpenAI API access.")
        return {chr(ord("A") + i): [] for i in range(26)}
    
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
        return {chr(ord("A") + i): [] for i in range(26)}
    
    results = {}
    
    for i in range(26):
        key = chr(ord("A") + i)
        prompt = (
            f"Generate {limit} examples of '{category}' that start with the letter '{key}'. "
            f"Return ONLY the examples as a comma-separated list, with NO explanations or numbering. "
            f"Example format: 'Apple, Apricot, Avocado'"
        )
        
        try:
            response = llm([HumanMessage(content=prompt)])
            items_str = response.content.strip()
            
            # Parse comma-separated items
            items = [item.strip() for item in items_str.split(",") if item.strip()]
            
            # Filter: keep only items that actually start with the letter
            valid_items = [
                item for item in items
                if item and item[0].upper() == key
            ]
            
            results[key] = valid_items[:limit]
            print(f"Generated {len(valid_items)} items for {key}: {valid_items}")
            
        except Exception as e:
            print(f"Error generating items for {key}: {e}")
            results[key] = []
    
    return results