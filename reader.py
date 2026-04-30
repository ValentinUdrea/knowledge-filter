import os
import pdfplumber
from pathlib import Path
from typing import Optional


def read_file(file_path: str) -> Optional[str]:
    """
    Extrage textul dintr-un fișier PDF sau TXT.

    Args:
        file_path: Calea către fișier (PDF sau TXT)

    Returns:
        Textul din fișier ca string, sau None dacă citirea a eșuat
    """
    try:
        # Convertește la Path pentru o manipulare mai ușoară
        path = Path(file_path)

        # Verifică dacă fișierul există
        if not path.exists():
            print(f"Eroare: Fișierul nu există: {file_path}")
            return None

        # Obține extensia fișierului
        file_ext = path.suffix.lower()

        if file_ext == '.pdf':
            return _read_pdf(path)
        elif file_ext == '.txt':
            return _read_txt(path)
        else:
            print(f"Eroare: Format de fișier nesuportat: {file_ext}")
            print("Suportate: .pdf, .txt")
            return None

    except Exception as e:
        print(f"Eroare la deschiderea fișierului: {e}")
        return None


def _read_pdf(path: Path) -> Optional[str]:
    """
    Extrage textul dintr-un fișier PDF.

    Args:
        path: Path object către fișierul PDF

    Returns:
        Textul din PDF sau None dacă extragerea a eșuat
    """
    try:
        text_parts = []

        with pdfplumber.open(path) as pdf:
            # Iterează prin fiecare pagină
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        if not text_parts:
            print(f"Avertisment: Nu s-a putut extrage text din PDF-ul {path.name}")
            return None

        # Combină textul din toate paginile cu separator
        combined_text = '\n\n'.join(text_parts)
        return combined_text

    except Exception as e:
        print(f"Eroare la citirea PDF-ului: {e}")
        return None


def _read_txt(path: Path) -> Optional[str]:
    """
    Extrage textul dintr-un fișier TXT.

    Args:
        path: Path object către fișierul TXT

    Returns:
        Textul din fișier sau None dacă citirea a eșuat
    """
    try:
        # Încearcă mai întâi cu UTF-8, apoi cu alte encoding-uri
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    text = f.read().strip()
                    if text:
                        return text
                    else:
                        print(f"Avertisment: Fișierul {path.name} e gol")
                        return None
            except UnicodeDecodeError:
                continue

        print(f"Eroare: Nu s-a putut citi fișierul {path.name} cu niciunul din encoding-urile suportate")
        return None

    except Exception as e:
        print(f"Eroare la citirea TXT-ului: {e}")
        return None
