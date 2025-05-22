import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque, Counter
import time
import re
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# CONFIGURATION
START_URLS = [
    "https://www.allrecipes.com/"
]
ALLOWED_DOMAIN = "allrecipes.com"
OUTPUT_FILE = r"C:\\Users\\Dell\\Documents\\recipes.txt"

visited = set()
recipes = {}

def is_valid_recipe_url(url):
    return (
        url and
        ALLOWED_DOMAIN in url and
        '/recipe/' in url and
        '?' not in url and
        '#' not in url
    )

def fetch_links(url):
    try:
        time.sleep(1)  # Be polite
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.content, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        return links
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

def extract_recipe_title_and_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Unknown Title", [], None

        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

        paragraphs = soup.find_all('p')
        content_sections = []
        current_heading = "No Heading"

        for p in paragraphs:
            heading_tag = p.find_previous('h2')
            if heading_tag:
                heading_text = heading_tag.get_text(strip=True)
                if heading_text != current_heading:
                    current_heading = heading_text
                    content_sections.append(f"=== {current_heading} ===")

            text = p.get_text(strip=True)
            if text:
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                for sentence in sentences:
                    content_sections.append(sentence + '.')
                content_sections.append("")

        # Try to find the main image
        image_tag = soup.find("img", {"class": "image-container__image"}) or \
                    soup.find("img", {"class": "rec-photo"}) or \
                    soup.find("img", src=True)
        image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else None

        return title, content_sections, image_url

    except Exception as e:
        return f"Failed to load ({e})", [], None

def crawl_recipes(start_urls, max_recipes):
    queue = deque(start_urls)

    while queue and len(recipes) < max_recipes:
        current_url = queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"\n🔍 Crawling: {current_url}")
        links = fetch_links(current_url)

        for link in links:
            full_url = urljoin(current_url, link)
            if is_valid_recipe_url(full_url) and full_url not in recipes:
                title, content_sections, image_url = extract_recipe_title_and_content(full_url)
                recipes[full_url] = (title, content_sections, image_url)
                print(f"\n✅ {title} - {full_url}\n")

                for line in content_sections:
                    print(line)

                print("\n" + "=" * 80 + "\n")

                if len(recipes) >= max_recipes:
                    break
                queue.append(full_url)

    return recipes

def save_to_txt(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for url, (title, content, image_url) in data.items():
            f.write(f"{title}\n{url}\n\n")
            for line in content:
                f.write(line + "\n")
            f.write("\n" + "="*50 + "\n\n")
    print(f"\n📝 Saved {len(data)} recipes to {filename}\n")

if __name__ == "__main__":
    while True:
        try:
            max_recipes = int(input("Enter the number of recipes to crawl: "))
            if max_recipes <= 0:
                print("Please enter a positive integer.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    results = crawl_recipes(START_URLS, max_recipes)
    save_to_txt(results, OUTPUT_FILE)

    # ------- Most Famous Recipes by Title --------
    title_counts = Counter(title for title, _, _ in results.values())
    most_common_titles = title_counts.most_common(15)
    labels, counts = zip(*most_common_titles)

    plt.figure(figsize=(10, 6))
    plt.barh(labels[::-1], counts[::-1], color='orange')
    plt.title("Top 15 Most Common Recipe Titles")
    plt.xlabel("Number of Occurrences")
    plt.ylabel("Recipe Title")
    plt.tight_layout()
    plt.show()

    # ------- Display All Recipe Images --------
    print("\n📸 Displaying All Recipe Images...\n")
    for url, (title, _, image_url) in results.items():
        if image_url:
            try:
                response = requests.get(image_url, timeout=5)
                img = Image.open(BytesIO(response.content))

                plt.figure()
                plt.imshow(img)
                plt.axis('off')
                plt.title(title)
                plt.show()

            except Exception as e:
                print(f"Could not load image for {title}: {e}")
