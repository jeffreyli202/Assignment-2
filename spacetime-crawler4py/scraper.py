import re
from urllib.parse import urlparse, urljoin, urldefrag
from html.parser import HTMLParser

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

class LinkExtractor(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.links = []
    
    def tag_handler(self, tag, attributes):
        if tag.lower() != 'a':
            return
        for (attribute, val) in attributes:
            if attribute.lower() == 'href' and val:
                self.links.append(val.strip())

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
    
    if not resp:
        return []
    if resp.status < 200 or resp.status >= 300:
        return []
    
    res = resp.raw_response
    if not res:
        return []
    
    c_type = res.headers.get("Content-Type", "").lower()

    if "text/html" not in c_type:
        return []
    
    if hasattr(res, "text"):
        html = res.text
    else:
        try:
            html = res.content.decode("utf-8", errors="ignore")
        except Exception: return []

    base_url = resp.url if resp.url else url
    parser = LinkExtractor(base_url)

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
