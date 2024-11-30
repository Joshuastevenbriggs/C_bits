import re
from tkinter import Tk, filedialog
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
import time
from datetime import datetime
from queue import Queue
import xml.etree.ElementTree as ET
start_url="https://cbits.netlify.app/"
domain=urlparse(start_url).netloc
visited=set()
queue=Queue()
queue.put((start_url,0))
url_pattern=re.compile(r'href=["\'](.*?)["\']')
js_url_pattern = re.compile(r'(https?://[^\s]+)')
extensions=['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.apng',
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a',
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    '.csv', '.xml', '.rss', '.atom',
    '.zip', '.rar', '.tar', '.gz', '.7z', '.iso',
    '.css', '.ts', '.jsx', '.vue', '.scss', '.less',
    '.exe', '.dll', '.bin', '.deb', '.apk', '.dmg', '.msi', '.pkg',
    '.ico', '.ttf', '.woff', '.woff2', '.eot', '.map','.json']
def init_robot_parser(domain):
    robots_url = f"https://{domain}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        print(f"Loaded robots.txt from {robots_url}")
    except:
        print(f"Failed to load robots.txt from {robots_url}. Assuming all URLs are allowed.")
        rp = None  
    return rp
def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    try:
        response=requests.get(url,headers=headers,timeout=5)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Request failed for {url}:{e}")
        return ""
    
def extract_urls(html, base_url):
    urls=re.findall(url_pattern,html)
    absolute_urls=[urljoin(base_url, url.strip()) for url in urls if url.strip()]
    return absolute_urls

def extract_links_from_js(js_content, base_url):
    """Extract potential URLs from JavaScript content."""
    urls = re.findall(js_url_pattern, js_content)
    absolute_urls = [urljoin(base_url, url.strip()) for url in urls if url.strip()]
    return absolute_urls

def extract_links_from_xml(xml_content, base_url):
    """Extract URLs from XML content (assuming XML has URL tags)."""
    urls = []
    try:
        root = ET.fromstring(xml_content)
        # Check for <url> or <link> tags and extract URLs
        for elem in root.findall('.//url') + root.findall('.//link'):
            url = elem.text
            if url:
                urls.append(url)
    except ET.ParseError:
        print("Error parsing XML.")
    return [urljoin(base_url, url.strip()) for url in urls]

def filter_urls(absolute_urls, domain, crawl_subdomains):
    filtered_urls=set()
    for url in absolute_urls:
        url_netloc = urlparse(url).netloc
        if crawl_subdomains:
            if not any(url.endswith(ext) for ext in extensions):
                 filtered_urls.add(url)
        elif url_netloc==domain:
            if not any(url.endswith(ext) for ext in extensions):
                 filtered_urls.add(url)
    return filtered_urls

crawl_subdomains_input = input("Do you want to crawl subdomains? (yes/no): ").strip().lower()
crawl_subdomains = True if crawl_subdomains_input == "yes" else False 


robot_parser = init_robot_parser(domain)

while not queue.empty():
    current_url,depth=queue.get()

    if current_url in visited or depth>1:
        continue
    if robot_parser and not robot_parser.can_fetch("*", current_url):
        print(f"Skipping {current_url} due to robots.txt restrictions.")
        continue

    print(f"Crawling {current_url} at depth {depth}")
    visited.add(current_url)
    
    html=get_html(current_url)
    if not html:
        continue
    

    absolute_urls=extract_urls(html,current_url)
    if current_url.endswith('.js'):
        js_links = extract_links_from_js(html, current_url)
        absolute_urls.extend(js_links)
    if current_url.endswith('.xml') or current_url.endswith('.rss') or current_url.endswith('.atom'):
        xml_links = extract_links_from_xml(html, current_url)
        absolute_urls.extend(xml_links)
    if current_url.endswith('.asp') or current_url.endswith('.php'):
        print(f"Checking ASP/PHP content at {current_url}")
        asp_php_links = extract_urls(html, current_url)
        absolute_urls.extend(asp_php_links)
    filtered_urls=filter_urls(absolute_urls, domain,crawl_subdomains)

    for url in filtered_urls:
        if url not in visited:
            queue.put((url, depth+1))
            print(f"Queued: {url}")
    time.sleep(1)

print("Crawling complete")
print(f"Visited {len(visited)} URLs")

def save_to_file(urls, default_filename="crawled_URLs"):
    
    root = Tk()
    root.withdraw()  

    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    domain_safe = domain.replace('.', '_')  
    default_filename = f"{default_filename}_({domain_safe}_{timestamp}).txt"
    
    
    filepath = filedialog.asksaveasfilename(
        title="Save Crawled URLs As",
        initialfile=default_filename,
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )

    
    if not filepath:
        print("Save operation canceled.")
        return

    
    with open(filepath, "w") as file:
        file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for url in urls:
            file.write(url + "\n")
        file.write("\n")
    print(f"Saved {len(urls)} URLs to {filepath}.")

save_to_file(visited) 
 
