import requests
from bs4 import BeautifulSoup
from typing import Optional


def scrape_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Descarcă o pagină web și extrage textul util.

    Args:
        url: URL-ul de descărcat
        timeout: Timeout în secunde pentru request

    Returns:
        Textul util din pagină sau None dacă descărcarea a eșuat
    """
    try:
        # Descarcă pagina
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parsează HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Elimină elementele care nu sunt utile
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'meta', 'noscript']):
            tag.decompose()

        # Elimină elementele cu clase/ID-uri de publicitate sau nav
        noise_keywords = ['ad', 'advert', 'nav', 'menu', 'sidebar', 'widget',
                        'cookie', 'popup', 'modal', 'banner', 'header']

        tags_to_remove = []
        for tag in soup.find_all(['div', 'section']):
            classes = ' '.join(tag.get('class', [])).lower()
            tag_id = tag.get('id', '').lower()
            if any(keyword in classes or keyword in tag_id for keyword in noise_keywords):
                tags_to_remove.append(tag)

        for tag in tags_to_remove:
            tag.decompose()

        # Extrage textul
        text = soup.get_text(separator='\n', strip=True)

        # Curăță spații multiple și linii goale
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)

        return clean_text if clean_text else None

    except requests.RequestException as e:
        print(f"Eroare la descărcarea URL-ului: {e}")
        return None
    except Exception as e:
        print(f"Eroare la procesarea paginii: {e}")
        return None
