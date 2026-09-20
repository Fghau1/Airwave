#!/usr/bin/env python3
"""Search Wikipedia and read article summaries from the terminal."""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://en.wikipedia.org/w/api.php"
SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
HEADERS = {"User-Agent": "AirwaveTerminalTools/1.0 (Wikipedia terminal reader)"}


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def search(query):
    params = urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": 8, "format": "json", "utf8": 1,
    })
    hits = get_json(API + "?" + params)["query"]["search"]
    if not hits:
        print("No Wikipedia results found.")
        return
    print("\nWikipedia results:\n")
    for i, hit in enumerate(hits, 1):
        title = hit["title"]
        print(f" {i}. {title}")
    print()
    choice = input("Read an article (number, or Enter to quit): ").strip()
    if not choice:
        return
    try:
        title = hits[int(choice) - 1]["title"]
    except (ValueError, IndexError):
        print("Choose one of the listed numbers.", file=sys.stderr)
        return
    page = get_json(SUMMARY.format(urllib.parse.quote(title.replace(" ", "_"), safe="")))
    print(f"\n{page.get('title', title)}\n{'=' * len(page.get('title', title))}\n")
    print(page.get("extract") or "No summary is available.")
    page_url = page.get("content_urls", {}).get("desktop", {}).get("page")
    if page_url:
        print(f"\nFull article: {page_url}")


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Search Wikipedia: ").strip()
    if not query:
        return
    try:
        search(query)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Wikipedia request failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
