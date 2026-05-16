import re
from typing import Optional, List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pdfplumber

from summarizer import summarize_text


class Chapter:
    """Reprezentare a unui capitol din carte"""
    def __init__(self, number: int, title: str, content: str):
        self.number = number
        self.title = title
        self.content = content
        self.summary = None
        self.status = "pending"  # pending, analyzing, completed, failed

    def __repr__(self):
        return f"Chapter {self.number}: {self.title}"


def _detect_chapters(text: str) -> List[Chapter]:
    """
    Detectează automat capitolele din text folosind diverse pattern-uri.

    Suportă:
    - Chapter 1, Chapter 2, ...
    - Capitolul 1, Capitolul 2, ...
    - CHAPTER 1, ...
    - 1. (pentru capitol numarat)
    - Titlu Capitol (linii scurte, singure, între spații goale)

    Args:
        text: Textul complet din care se detecteaza capitolele

    Returns:
        Lista de obiecte Chapter detectate
    """
    chapters = []

    # Pattern-uri pentru detectare capitole cu NUMĂR (in ordine de prioritate)
    numbered_patterns = [
        # English: "Chapter 1: Title" sau "Chapter 1 Title"
        r'(?:^|\n)\s*(?:chapter|Chapter|CHAPTER)\s+(\d+)\s*[:—–-]?\s*(.+?)(?=\n|$)',
        # Romanian: "Capitolul 1: Title" sau "Capitolul 1 Title"
        r'(?:^|\n)\s*(?:capitolul|Capitolul|CAPITOLUL)\s+(\d+)\s*[:—–-]?\s*(.+?)(?=\n|$)',
        # Romanian: "Cap. 1: Title"
        r'(?:^|\n)\s*(?:cap\.|Cap\.)\s+(\d+)\s*[:—–-]?\s*(.+?)(?=\n|$)',
        # Numeric: "1. Title" (doar la inceput de linie)
        r'(?:^|\n)\s*(\d+)\.\s+([A-Z].+?)(?=\n|$)',
    ]

    # Pattern pentru detectare titluri de capitol (linii scurte, singure)
    # Linie care: incepe cu majuscula, max 50 caractere, intre linii goale
    title_pattern = r'(?:\n\n)([ \t]*[A-Z][^\n]{0,48})(?:\n\n|\n\s*$)'

    chapter_matches = []

    # Incearca fiecare pattern cu număr
    for pattern in numbered_patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
        if matches:
            for match in matches:
                chapter_num = int(match.group(1))
                chapter_title = match.group(2).strip()
                start_pos = match.start()

                # Filtreaza capitolele false: doar numerele 1-50 sunt reale
                # Numerele > 50 sunt probabil ani sau numere de pagina din bibliografie
                if 1 <= chapter_num <= 50:
                    chapter_matches.append((chapter_num, chapter_title, start_pos))
                else:
                    print(f"⊘ Exclus (capitolul {chapter_num} > 50, probabil an/pagina din bibliografie): {chapter_title[:40]}")


    # Incearca pattern-ul pentru titluri standalone
    title_matches = list(re.finditer(title_pattern, text, re.MULTILINE))
    if title_matches:
        print("📌 Detectare titluri de capitol standalone...")
        title_chapter_matches = []
        for match in title_matches:
            chapter_title = match.group(1).strip()
            start_pos = match.start()
            title_chapter_matches.append((chapter_title, start_pos))

        # Numara titlurile detectate
        for idx, (title, start_pos) in enumerate(title_chapter_matches, 1):
            # Verifica sa nu fie deja detectat prin alte pattern-uri
            is_duplicate = any(
                abs(m[2] - start_pos) < 20 for m in chapter_matches
            )
            if not is_duplicate:
                chapter_matches.append((idx, title, start_pos))
                print(f"   ✓ Capitol {idx}: {title}")

    if not chapter_matches:
        print("⚠️ Niciun capitol detectat. Tratez tot textul ca un singur capitol.")
        return [Chapter(1, "Continut Principal", text)]

    # Sorteaza dupa pozitie in text si elimina duplicate (dupa pozitie)
    chapter_matches = sorted(set(chapter_matches), key=lambda x: x[2])

    # Elimina capitolele duplicate (same number) - pastreaza cel cu titlu mai scurt/curat
    print("🔍 Verificare capitole duplicate...")
    filtered_chapters = {}
    for num, title, start_pos in chapter_matches:
        if num not in filtered_chapters:
            filtered_chapters[num] = (num, title, start_pos)
        else:
            # Compara titlurile - pastreaza cel mai scurt si mai curat
            existing_title = filtered_chapters[num][1]
            if len(title) < len(existing_title) or (len(title) == len(existing_title) and title < existing_title):
                print(f"   Înlocuiesc Cap. {num}: '{existing_title}' → '{title}'")
                filtered_chapters[num] = (num, title, start_pos)
            else:
                print(f"   Duplicat ignorat Cap. {num}: '{title}'")

    chapter_matches = list(filtered_chapters.values())

    # Exclude Chapter 43 explicit
    print("🚫 Exclud Chapter 43...")
    chapter_matches = [(num, title, pos) for num, title, pos in chapter_matches if num != 43]
    for num, title, pos in [(n, t, p) for n, t, p in chapter_matches if n == 43]:
        print(f"   ⊘ Exclus: Cap. {num}: {title}")

    # Extrage continutul fiecarui capitol
    for idx, (num, title, start_pos) in enumerate(chapter_matches):
        # Continutul incepe de la match si merge pana la urmatorul capitol
        if idx < len(chapter_matches) - 1:
            end_pos = chapter_matches[idx + 1][2]
            content = text[start_pos:end_pos].strip()
        else:
            content = text[start_pos:].strip()

        # Elimina linia cu titlul de capitol din continut
        content = re.sub(
            r'(?:^|\n)\s*(?:chapter|Chapter|CHAPTER|capitolul|Capitolul|CAPITOLUL|cap\.|Cap\.)\s+\d+\s*[:—–-]?.+?(?=\n)',
            '',
            content,
            count=1,
            flags=re.MULTILINE | re.IGNORECASE
        ).strip()

        # Elimina si titluri standalone daca au ramas
        content = re.sub(
            r'^\s*[A-Z][^\n]{0,48}\s*\n',
            '',
            content,
            count=1,
            flags=re.MULTILINE
        ).strip()

        if len(content) > 100:  # Doar daca are suficient continut
            chapters.append(Chapter(num, title, content))

    if not chapters:
        print("⚠️ Niciun capitol cu text suficient. Tratez tot textul ca un singur capitol.")
        return [Chapter(1, "Continut Principal", text)]

    return chapters


def _summarize_chapter_worker(args: tuple) -> Dict:
    """
    Worker function pentru ThreadPoolExecutor.
    Rezumă un capitol și returnează rezultatul.

    Args:
        args: Tuplu (chapter, idx, total)

    Returns:
        Dict cu rezultatul rezumării
    """
    chapter, idx, total = args

    print(f"\n   [{idx}/{total}] {chapter}")
    print(f"   Caracterere: {len(chapter.content)}")

    # Verifica daca textul e suficient de lung
    if len(chapter.content) < 100:
        print(f"   ⚠️ Text prea scurt, sar peste")
        return {
            'number': chapter.number,
            'title': chapter.title,
            'summary': None,
            'status': 'skipped',
            'reason': 'Text prea scurt'
        }

    # Rezumeaza
    print(f"   Rezumez...")
    summary = summarize_text(chapter.content)

    if summary:
        print(f"   ✓ Analizat cu succes")
        chapter.summary = summary
        chapter.status = 'completed'
        return {
            'number': chapter.number,
            'title': chapter.title,
            'summary': summary,
            'status': 'completed'
        }
    else:
        print(f"   ❌ Eroare la analiza")
        chapter.status = 'failed'
        return {
            'number': chapter.number,
            'title': chapter.title,
            'summary': None,
            'status': 'failed'
        }


def analyze_book(file_path: str) -> Optional[Dict]:
    """
    Analizeaza o carte completa (PDF) capitol cu capitol.

    Proces:
    1. Citeste PDF-ul
    2. Detecteaza automat capitolele
    3. Rezumeaza FIECARE capitol separat
    4. Combine rapoartele intr-un rezultat final

    Args:
        file_path: Calea catre fișierul PDF

    Returns:
        Dict cu structura:
        {
            'book_title': 'Titlul cartii',
            'total_chapters': int,
            'chapters': [
                {
                    'number': int,
                    'title': str,
                    'summary': {
                        'title': str,
                        'key_ideas': [str],
                        'summary': str
                    },
                    'status': 'completed' | 'failed'
                }
            ],
            'full_report': str (formatted)
        }
        sau None daca a esuat
    """
    try:
        # Pasul 1: Citeste PDF-ul
        print(f"📖 Citesc PDF-ul: {file_path}")
        path = Path(file_path)

        if not path.exists():
            print(f"❌ Fișierul nu există: {file_path}")
            return None

        if not path.suffix.lower() == '.pdf':
            print(f"❌ Fișierul trebuie sa fie PDF: {file_path}")
            return None

        # Extrage textul din PDF
        text_parts = []
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            print(f"   Pagini totale: {total_pages}")

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)

                if page_num % 10 == 0:
                    print(f"   ✓ Procesat pagina {page_num}/{total_pages}")

        full_text = '\n\n'.join(text_parts)

        if not full_text or len(full_text) < 100:
            print("❌ Nu s-a putut extrage text din PDF")
            return None

        print(f"✓ Text extras: {len(full_text)} caractere")

        # Pasul 2: Detecteaza capitolele
        print("\n🔍 Detectez capitolele...")
        chapters = _detect_chapters(full_text)
        print(f"✓ Detectate {len(chapters)} capitol(e)")
        for ch in chapters:
            print(f"   - {ch}")

        # Pasul 3: Rezumeaza FIECARE capitol (IN PARALEL cu 3 workers)
        print("\n⚙️ Analizez capitolele (paralel, 3 workers)...")
        chapter_results = []

        # Pregătește lista de argumente pentru workers
        worker_args = [(ch, idx, len(chapters)) for idx, ch in enumerate(chapters, 1)]

        # Procesează capitolele în paralel cu ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(_summarize_chapter_worker, worker_args)
            chapter_results = list(results)

        # Pasul 4: Combine rezultatele intr-un raport
        print("\n📋 Generad raportul final...")
        full_report = _generate_report(chapters, path.stem)

        result = {
            'book_title': path.stem,
            'total_chapters': len(chapters),
            'chapters': chapter_results,
            'full_report': full_report
        }

        print("✓ Analiza completa!")
        return result

    except Exception as e:
        print(f"❌ Eroare: {e}")
        import traceback
        traceback.print_exc()
        return None


def _generate_report(chapters: List[Chapter], book_title: str) -> str:
    """
    Genereaza raportul final formatat cu toate capitolele.

    Args:
        chapters: Lista de obiecte Chapter
        book_title: Titlul cartii

    Returns:
        String formatat cu raportul complet
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append(f"📖 RAPORT DE ANALIZA: {book_title.upper()}")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total capitol: {len(chapters)}")
    lines.append("")

    # Pentru fiecare capitol
    for idx, chapter in enumerate(chapters, 1):
        lines.append("-" * 80)
        lines.append(f"CAPITOL {chapter.number}: {chapter.title.upper()}")
        lines.append("-" * 80)

        if chapter.summary:
            summary = chapter.summary

            # Titlu rezumat
            lines.append(f"\n📌 Titlu: {summary['title']}")

            # Idei cheie
            lines.append(f"\n🔑 Idei Cheie:")
            for i, idea in enumerate(summary['key_ideas'], 1):
                lines.append(f"   {i}. {idea}")

            # Rezumat
            lines.append(f"\n📝 Rezumat:\n{summary['summary']}")
        else:
            lines.append("\n⚠️ Capitol nu a putut fi analizat")

        lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append("FIN RAPORT")
    lines.append("=" * 80)

    return '\n'.join(lines)


def export_report(analysis_result: Dict, output_format: str = 'txt') -> str:
    """
    Exporta raportul de analiza.

    Args:
        analysis_result: Rezultatul din analyze_book()
        output_format: 'txt' (default)

    Returns:
        Calea catre fisierul exportat
    """
    if not analysis_result:
        print("❌ Nu exista rezultat de exportat")
        return None

    book_title = analysis_result['book_title']
    filename = f"{book_title}_analysis.{output_format}"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(analysis_result['full_report'])

        print(f"✓ Raport exportat: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Eroare la export: {e}")
        return None


if __name__ == "__main__":
    # Exemplu de utilizare
    import sys

    if len(sys.argv) < 2:
        print("Utilizare: python book_analyzer.py <path_to_pdf>")
        print("Exemplu: python book_analyzer.py carte.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    result = analyze_book(pdf_path)

    if result:
        print("\n" + result['full_report'])
        export_report(result)
