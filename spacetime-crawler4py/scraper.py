import json
import re
from urllib.parse import urlparse, urljoin, urldefrag
from html.parser import HTMLParser

STOPWORDS = {
    "the", "and", "of", "to", "a", "in", "for", "is", "on", "that", "with", "as",
    "by", "at", "an", "be", "from", "this", "or", "it", "are", "was"
}

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    
    def handle_starttag(self, tag, attributes):
        if tag.lower() != 'a':
            return
        for (attribute, val) in attributes:
            if attribute.lower() == 'href' and val:
                self.links.append(val.strip())

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []
    
    def handle_data(self, data):
        if data:
            self.chunks.append(data)
    
    def combine_chunks(self):
        return ''.join(self.chunks)

def extract_text(html):
    parser = TextExtractor()
    parser.feed(html)
    return parser.combine_chunks()

def tokenize(text):
    text = text.lower()
    return re.findall(r"[a-z0-9]+", text)

def extract_subdomain(url):
    p = urlparse(url)
    return p.netloc.lower()

def scraper(url, resp):
    with open("scraper.log", "a") as f:
        f.write(f"[SCRAPER] got: {url}\n")

    links = extract_next_links(url, resp)

    if resp and 200 <= resp.status < 400 and resp.raw_response:
        raw = resp.raw_response
        if hasattr(raw, "text"):
            html = raw.text
        else:
            html = raw.content.decode("utf-8", "ignore")

        text = extract_text(html)
        words = tokenize(text)
        words = [w for w in words if w not in STOPWORDS]

        canon_url, _ = urldefrag(resp.url if resp.url else url)
        subdomain = extract_subdomain(canon_url)

        rec = {
            "url": canon_url,
            "subdomain": subdomain,
            "word_count": len(words),
            "tokens": words,
        }

        with open("data.txt", "a") as data_f:
            data_f.write(json.dumps(rec) + "\n")

    return list({link for link in links if is_valid(link)})


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    if resp is None:
        return []
    if resp.status < 200 or resp.status >= 400:
        return []
    
    res = resp.raw_response
    if res is None:
        return []
    
    c_type = res.headers.get("Content-Type", "").lower()
    c_type = c_type.lower() if c_type else ""

    if c_type and "text/html" not in c_type:
        return []
    
    if hasattr(res, "text"):
        html = res.text
    else:
        try:
            html = res.content.decode("utf-8", errors="ignore")
        except Exception: return []

    base_url = resp.url if resp.url else url
    parser = LinkExtractor()

    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass

    links = []

    for href in parser.links:
        if not href: continue
        if href.startswith(("javascript:", "mailto:", "tel:")): continue

        cleaned_url = urljoin(base_url, href)
        cleaned_url, j = urldefrag(cleaned_url)

        data_parsed = urlparse(cleaned_url)
        if not data_parsed.scheme or not data_parsed.netloc:
            continue
        links.append(cleaned_url)
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        allowed = (
            "ics.uci.edu",
            "cs.uci.edu",
            "informatics.uci.edu",
            "stat.uci.edu",
            "today.uci.edu",
        )
        host = parsed.netloc.lower()
        if not any(host == d or host.endswith("." + d) for d in allowed):
            return False
        
        if host == "today.uci.edu":
            if not parsed.path.startswith("/department/information_computer_sciences"):
                return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", url)
        raise
