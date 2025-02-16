import requests
import xml.etree.ElementTree as ET
import urllib.parse
from bs4 import BeautifulSoup
import time
import random
import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
]

def fetch_articles_from_scholar(query, max_results=50):
    articles = []
    start = 0
    
    while len(articles) < max_results:
        # Random delay between requests (2-5 seconds)
        time.sleep(random.uniform(2, 5))
        
        # Rotate User-Agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS)
        }
        
        url = 'https://scholar.google.com/scholar'
        params = {
            'q': query,
            'start': start
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                results = soup.find_all('div', {'class': 'gs_ri'})
                
                if not results:
                    break
                    
                for result in results:
                    if len(articles) >= max_results:
                        break
                        
                    # Parsing the title
                    title = result.find('h3').text if result.find('h3') else 'No Title Available'
                    
                    # Parsing the year of publication
                    year = 'No Year Available'
                    year_tag = result.find('div', {'class': 'gs_a'})
                    if year_tag:
                        year_text = year_tag.text
                        # Extract the year from the text (usually at the end)
                        year = year_text.split('-')[-1].strip() if '-' in year_text else year_text.strip()
                    
                    # Parsing the link to the article
                    link = result.find('h3').find('a')['href'] if result.find('h3').find('a') else None
                    
                    # Parsing the authors
                    authors_list = []
                    authors_tag = result.find('div', {'class': 'gs_a'})
                    if authors_tag:
                        authors = authors_tag.text.split('-')[0]
                        authors_list = [author.strip() for author in authors.split(',')]
                    
                    # Parsing the summary/abstract
                    summary_text = 'No Summary Available'
                    summary_tag = result.find('div', {'class': 'gs_rs'})
                    if summary_tag:
                        summary_text = summary_tag.text
                    
                    articles.append({
                        'title': title,
                        'year': year,
                        'link': link,
                        'authors': authors_list,
                        'summary': summary_text,
                        'abstract': summary_text,
                        'source': 'Google Scholar'
                    })
                
                start += 10
            else:
                print(f"Error: Status code {response.status_code}")
                break
                
        except Exception as e:
            print(f"Error: {e}")
            break
            
    return articles
def fetch_articles_from_core(query, max_results=25):
    url = 'https://api.core.ac.uk/v3/search/works'
    headers = {
        'Authorization': 'kvcBAQgn6lJCf5dha4jyWMIseOxUzwpK'  # Replace with your CORE API key
    }
    params = {
        'q': query,
        'limit': max_results,
        'offset': 0,
        'filters': 'language:English'  # Add filter for English articles
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for item in data.get('results', []):
                # Extract and clean the data
                title = item.get('title', 'No Title Available')
                year = item.get('yearPublished', 'Unknown Year')
                abstract = item.get('abstract', 'No Abstract Available')
                authors = [author.get('name', 'Unknown Author') 
                          for author in item.get('authors', [])]
                doi = item.get('doi', '')
                
                articles.append({
                    'title': title,
                    'year': str(year),
                    'link': item.get('downloadUrl', '') or f"https://doi.org/{doi}",
                    'authors': authors,
                    'summary': abstract,
                    'abstract': abstract,
                    'source': 'CORE',
                    'classifications': item.get('types', ['unknown'])
                })
            return articles
        else:
            print(f"Error fetching articles from CORE: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching from CORE: {e}")
        return []
def fetch_articles_from_crossref(query, max_results=25):
    url = 'https://api.crossref.org/works'
    params = {
        'query': query,
        'rows': max_results,
        'select': 'DOI,title,author,published-print,abstract,published-online,type',
        'sort': 'published-online',
        'order': 'desc',
        'filter': 'has-abstract:true'
    }
    
    headers = {
        'User-Agent': 'ResearchKoTo/1.0 (mailto:your-email@domain.com)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for item in data.get('message', {}).get('items', []):
                # Get publication year from either published-print or published-online
                pub_date = (item.get('published-print', {}) or item.get('published-online', {}))
                year = pub_date.get('date-parts', [['']])[0][0] if pub_date else 'Unknown Year'
                
                # Get title (handle list format)
                title = item.get('title', ['No Title Available'])
                if isinstance(title, list):
                    title = title[0]
                
                # Extract authors
                authors = []
                for author in item.get('author', []):
                    if 'given' in author and 'family' in author:
                        authors.append(f"{author['given']} {author['family']}")
                
                # Get DOI link
                doi = item.get('DOI', '')
                link = f"https://doi.org/{doi}" if doi else ''
                
                # Get abstract
                abstract = item.get('abstract', 'No Abstract Available')
                
                articles.append({
                    'title': title,
                    'year': str(year),
                    'link': link,
                    'authors': authors if authors else ['Unknown Author'],
                    'summary': abstract,
                    'abstract': abstract,
                    'source': 'Crossref',
                    'classifications': [item.get('type', 'unknown')],
                    'doi': doi
                })
            
            return articles
        else:
            print(f"Error fetching articles from Crossref: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching from Crossref: {e}")
        return []

    

def fetch_articles_from_ieee(query, max_results=10):
    url = 'https://ieeexploreapi.ieee.org/api/v1/search/articles'
    headers = {
        'Authorization': 'x7a37b94xfxn5m9z8dtp6ft6',
        'Accept': 'application/json'
    }
    params = {
        'querytext': query,
        'max_records': max_results,
        'start_record': 1,
        'sort_order': 'desc',
        'sort_field': 'publication_year'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for item in data.get('articles', []):
                title = item.get('title', 'No Title Available')
                year = item.get('publication_year', 'Unknown Year')
                abstract = item.get('abstract', 'No Abstract Available')
                authors = [author.get('full_name', 'Unknown Author') 
                          for author in item.get('authors', [])]
                
                articles.append({
                    'title': title,
                    'year': str(year),
                    'link': f"https://doi.org/{item.get('doi', '')}",
                    'authors': authors,
                    'summary': abstract,
                    'abstract': abstract,
                    'source': 'IEEE'
                })
            return articles
        else:
            print(f"Error fetching articles from IEEE: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching from IEEE: {e}")
        return []

def fetch_articles_from_arxiv(query, max_results=10):
    url = f'http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}'
    response = requests.get(url)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        articles = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            year = published.split('-')[0]
            link = entry.find('{http://www.w3.org/2005/Atom}id').text
            authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
            
            articles.append({
                'title': title or 'No Title Available',
                'year': year or 'Unknown Year',
                'link': link or 'No URL Available',
                'authors': authors or ['Unknown Author'],
                'summary': summary or 'No summary available',
                'abstract': summary or 'No Abstract Available',
                'source': 'arXiv'
            })
        return articles
    else:
        print("Error fetching articles from arXiv.")
        return []



def fetch_articles_from_pubmed(query, max_results=50):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'xml'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        id_list = root.find('.//IdList').findall('Id')
        articles = []
        
        for article_id in id_list:
            article_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={article_id.text}&retmode=xml'
            article_response = requests.get(article_url)
            article_root = ET.fromstring(article_response.text)
            docsum = article_root.find('.//DocSum')
            
            title = docsum.find("./Item[@Name='Title']").text
            pub_date_elem = docsum.find("./Item[@Name='PubDate']")
            year = pub_date_elem.text.split()[-1] if pub_date_elem is not None else "Unknown Year"
            
            authors_elem = docsum.findall("./Item[@Name='Author']")
            authors = [author.text for author in authors_elem] if authors_elem else ["Unknown Author"]
            
            summary_elem = docsum.find("./Item[@Name='Summary']")
            summary = summary_elem.text if summary_elem is not None else "No summary available"
            
            articles.append({
                'title': title or 'No Title Available',
                'year': year,
                'link': f'https://pubmed.ncbi.nlm.nih.gov/{article_id.text}/',
                'authors': authors,
                'summary': summary,
                'abstract': summary,
                'source': 'PubMed'
            })
        return articles
    else:
        print("Error fetching articles from PubMed.")

        return []
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

import requests
import random
import time
from bs4 import BeautifulSoup

# List of common User-Agent strings for rotation

def filter_recent_articles(articles):
    current_year = 2024  # You can also use datetime.now().year
    return [
        article for article in articles 
        if article.get('year', 'Unknown Year').isdigit() 
        and int(article.get('year')) >= 2020
        and int(article.get('year')) <= current_year
    ]
def fetch_articles(query):
    all_articles = []
    
    # IEEE Articles
    try:
        articles = fetch_articles_from_ieee(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from IEEE: {e}")
    
    # arXiv Articles    
    try:
        articles = fetch_articles_from_arxiv(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from arXiv: {e}")
    
    # PubMed Articles
    try:
        articles = fetch_articles_from_pubmed(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from PubMed: {e}")
        
    # CORE Articles
    try:
        articles = fetch_articles_from_core(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from CORE: {e}")
    
    # Crossref Articles
    try:
        articles = fetch_articles_from_crossref(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from Crossref: {e}")
        
    # Google Scholar Articles
    try:
        articles = fetch_articles_from_scholar(query)
        all_articles.extend(filter_recent_articles(articles))
    except Exception as e:
        print(f"Error fetching from Google Scholar: {e}")
    
    return all_articles