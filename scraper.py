from bs4 import BeautifulSoup
import requests
import os
import time
from tqdm import tqdm
import json
from urllib.parse import urljoin
from urllib.parse import urlparse

def get_content(home_url, links, visited_links, headers):
    if not links:
        return None
    home_domain = urlparse(home_url).netloc 
    if len(links)>0:
        if urlparse(links[0]).scheme not in ('http', 'https'):
            return None, links, visited_links
        response = requests.get(links[0], headers=headers)
        content_type = response.headers.get('content-type')
        if "text/html" not in content_type:
            visited_links.append(links[0])
            links.remove(links[0])
            return None, links, visited_links
        if response.status_code == 200:
            current_link = str(links[0])
            visited_links.append(links[0])
            links.remove(links[0])
            soup = BeautifulSoup(response.text, 'html.parser')
            if soup is None:
                visited_links.append(links[0])
                links.remove(links[0])
                return None, links, visited_links
            # body = soup.find('body')
            content = soup.get_text(separator="\n", strip=True)
            content = content.replace("\"", "'").replace("\n", " ").replace("\t", " ")
            if soup.title is None:
                title = home_domain
            else:
                title = soup.title.string
            a_tags = soup.find_all("a")
            for link in a_tags:
                href = link.get("href")
                if href is not None:
                    if '#' in href:
                        continue
                    elif home_url not in href and urlparse(href).scheme not in ('mailto', 'javascript', 'ftp', 'tel', 'file', 'data'):
                        href = urljoin(home_url, href) 
                        if urlparse(href).netloc != home_domain:
                            continue
                        if href not in visited_links:
                            links.append(href)
                    
            links = list(set(links))
            data = {"title": title, "link": current_link, "content": content}
            return data, links, visited_links
        else:
            visited_links.append(links[0])
            links.remove(links[0])
            return None, links, visited_links

if __name__ == "__main__":
    home_urls = ["https://numpy.org/doc/stable/", "https://pandas.pydata.org/docs/", "https://www.python.org/doc/", "https://www.w3schools.com/", "https://whoosh.readthedocs.io/en/latest/", "https://pytorch.org/docs/stable", "https://docs.flutter.dev/", "https://go.dev/doc/"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept-Encoding": "*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    base_dir = "base/documentation"
    
    with tqdm(total=len(home_urls)) as pbar:
        for home_url in tqdm(home_urls, desc=""):
            pbar.set_description(f"Scraping {home_url}:")
            parts = home_url.split("//")[1].split(".")
            name = parts[1] if parts[0] == "www" or parts[0]=="docs" else parts[0]
            path = os.path.join(base_dir, name)
            
            
            os.makedirs(path, exist_ok=True)
            try:
                response = requests.get(home_url, headers=headers)
            except ConnectionResetError:
                print("ConnectionResetError, continuing not next home_url")
                continue
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            visited_links = []
            json_file = os.path.join(path, "visited_links.json")
            if os.path.exists(json_file):
                with open(os.path.join(path, "visited_links.json"), "r") as f:
                    link_data = json.load(f)
                    visited_links = link_data['visited_links']
            a_tags = soup.find_all("a")
            links = []
            home_domain = urlparse(home_url).netloc
            for tag in a_tags:
                href = tag.get("href")
                if href is not None:
                    if '#' in href:
                        continue
                    elif home_url not in href:
                        href = urljoin(home_url, href)
                        if urlparse(href).netloc != home_domain:
                            continue
                        links.append(href)
                    
            links = list(set(links))
            visited_links.append(home_url)
            if home_url in links:
                links.remove(home_url)
            # Remove any links that are already in the visited_links list
            links = [link for link in links if link not in visited_links]
            
            # data_list = []
            counter = 0
            while len(links)>0:
                time.sleep(3)
                data, links, visited_links = get_content(home_url, links, visited_links, headers=headers)
                if data is not None:
                    # data_list.append(data)
                    file_name = data['link'].split("//")[-1].replace(".", "_").replace("/", "_").replace("?", "_").replace("=", "_")
                    with open(os.path.join(path, f"{counter}_{file_name}.json"), "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    counter += 1
                v_link = {"visited_links": visited_links}
                with open(os.path.join(path, "visited_links.json"), "w", encoding='utf-8') as f:
                    json.dump(v_link, f, indent=4, ensure_ascii=False)
                # if counter is greater than 100, exit the while loop and continue with the next home_url
                if counter > 150:
                    break
                pbar.set_postfix(total_links=len(links), visited_links=len(visited_links), count=counter)
                pbar.update(1)

                


