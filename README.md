# 📚 KnowledgeFilter - Analizor Inteligent de Documente

Un tool Python care transformă URL-uri și documente (PDF, TXT) în rezumate structurate și ușor de citit. Filtrează "zgomotul" și prezintă doar ideile principale.

## ✨ Ce face aplicația

- **Analizează URL-uri**: Descarcă pagini web, curăță HTML-ul și extrage conținut util
- **Citește documente**: Suportă PDF și TXT cu detectare automată de encoding
- **Rezumă inteligent**: Folosește Ollama (llama3.2) pentru generare de rezumate structurate
- **Export flexibil**: Salvează rezultatele în TXT sau PDF formatat frumos
- **Interfață grafică**: CustomTkinter pentru o experiență user-friendly

## 🎯 Rezumate structurate

Fiecare analiză produce:
- 🔹 **Titlu** — rezumat al conținutului (max 10 cuvinte)
- 🔑 **Idei cheie** — până la 5 puncte importante
- 📝 **Rezumat** — sinteza în 2-3 propoziții

## 📋 Cerințe de sistem

- **Python**: 3.12 sau mai nou
- **Ollama**: Instalat și rulând local cu modelul `llama3.2`
  - [Download Ollama](https://ollama.ai)
  - După instalare, descarcă modelul: `ollama pull llama3.2`

## 🚀 Instalare

### 1. Clonează repository-ul
```bash
cd c:\Proiecte\knowledge-filter
```

### 2. Creează și activează virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalează dependențe
```bash
pip install -r requirements.txt
```

## 🎮 Cum se rulează

### GUI (Interfață grafică - Recomandat)
```bash
python app.py
```

Apoi:
1. Introdu un URL sau selectează un fișier (PDF/TXT)
2. Apasă **"🔍 Analizează"**
3. Așteaptă rezumatul
4. Exportează ca **TXT** sau **PDF**

### CLI (Linie de comandă)
```bash
# Analizează un URL
python main.py --url "https://example.com"

# Analizează un fișier local
python main.py --file "document.pdf"
```

## 📦 Structura proiectului

```
knowledge-filter/
├── app.py              # Interfață grafică (CustomTkinter)
├── main.py             # CLI (click)
├── scraper.py          # Extrage conținut din URL-uri
├── reader.py           # Citește PDF și TXT
├── summarizer.py       # Rezumare cu Ollama
├── requirements.txt    # Dependențe Python
└── README.md          # Acest fișier
```

## 🔧 Dependențe

- **requests** - HTTP requests
- **beautifulsoup4** - Web scraping
- **pdfplumber** - Citire PDF
- **ollama** - Integare Ollama API
- **click** - CLI framework
- **customtkinter** - GUI moderna
- **reportlab** - Generare PDF

## ⚙️ Troubleshooting

### "Nu se găsește modelul llama3.2"
```bash
ollama pull llama3.2
```

### "Eroare de conexiune la Ollama"
Asigură-te că Ollama rulează: `ollama serve`

### "PDF-ul nu se salvează"
Asigură-te că ai permisiuni de scriere în directorul selectat.

## 📝 Exemplu de utilizare

```bash
# 1. Pornește app-ul
python app.py

# 2. Paste URL-ul
https://en.wikipedia.org/wiki/Python_(programming_language)

# 3. Apasă "Analizează"
# Așteptă 30-60 secunde

# 4. Rezultatul apare automat
# 📌 Python (limbaj de programmare)
# 🔑 Idei cheie:
#    1. Limbaj interpretativ, dinamic tipat
#    2. Creat în 1989 de Guido van Rossum
#    ...

# 5. Exportează
# Apasă "Exportă PDF" pentru o versiune formatată
```

## 🎨 Interfață GUI

- **Dark theme** cu culori apetisante
- Progres real-time cu status bar
- Butoane intuitive cu emoji
- Export dual (TXT + PDF)

## 📄 Licență

Liber pentru uz personal și educațional.

---

**Enjoying KnowledgeFilter?** Dă-i o stea ⭐

