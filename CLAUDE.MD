]# KnowledgeFilter — Context

## Ce face aplicația
Un tool Python care primește un URL sau un fișier (PDF, TXT) 
și returnează un rezumat structurat cu ideile principale.
Scopul e să filtreze "zgomotul" și să prezinte doar ce e util.

## Moduri de input
- URL (pagină web) → curăță HTML-ul, extrage conținut, rezumă
- Fișier local (PDF, TXT) → extrage textul, rezumă

## Stack
- Python 3.11+
- requests + BeautifulSoup (web scraping)
- pdfplumber (citit PDF)
- Claude API (rezumat inteligent)
- click (interfață CLI)

## Cum se rulează
python main.py --url "https://..."
python main.py --file "document.pdf"

## Stil de cod
- Cod simplu și lizibil, nu over-engineered
- Comentarii în română e ok
- Fișiere separate pe funcționalitate (scraper.py, reader.py, summarizer.py)