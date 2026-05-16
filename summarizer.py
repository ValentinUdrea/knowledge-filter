import json
import re
import traceback
import ollama
from typing import Optional, List


def _split_into_chunks(text: str, chunk_size: int = 6000) -> List[str]:
    """
    Împarte textul în bucăți de dimensiune egală.

    Args:
        text: Textul de împărțit
        chunk_size: Dimensiunea fiecărei bucăți (default 6000)

    Returns:
        Lista de bucăți de text
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # Ia următoarea bucată
        chunk_end = min(current_pos + chunk_size, len(text))
        chunk = text[current_pos:chunk_end]

        # Dacă nu e ultimul chunk, încearcă să o termini la o limită naturală (spațiu, linie nouă)
        if chunk_end < len(text):
            # Cauta ultimul spațiu din chunk
            last_space = chunk.rfind('\n')
            if last_space > chunk_size // 2:  # Doar dacă e rezonabil de departe
                chunk = chunk[:last_space]
                chunk_end = current_pos + len(chunk)

        chunks.append(chunk.strip())
        current_pos = chunk_end

    return [c for c in chunks if len(c) > 50]  # Filtrează bucăți prea mici


def _summarize_chunk(text: str, chunk_num: int = 0, total_chunks: int = 1) -> Optional[dict]:
    """
    Rezumă o bucată de text. Versiunea internă a summarize_text.

    Args:
        text: Textul de rezumat
        chunk_num: Numărul bucății (pentru logging)
        total_chunks: Numărul total de bucăți

    Returns:
        Dict cu rezumatul sau None
    """
    if not text or len(text) < 100:
        return None

    max_retries = 2
    for attempt in range(1, max_retries + 1):
        try:
            chunk_label = f" [Parte {chunk_num}/{total_chunks}]" if total_chunks > 1 else ""
            prompt = f"""You must respond with only a JSON object, no other text, no markdown, no backticks.

Analizează textul următor și extrage ideile principale.{chunk_label}

TEXT:
{text}

Răspunde EXACT în acest format JSON:
{{
    "title": "Un titlu care rezumă conținutul (max 10 cuvinte)",
    "key_ideas": [
        "Idea cheie 1",
        "Idea cheie 2",
        "Idea cheie 3"
    ],
    "summary": "Rezumat de 2-3 propoziții care captează esența textului."
}}

Asigură-te că:
- Extrage maxim 5 idei cheie importante
- Ideile sunt concise și directe
- Rezumatul are 2-3 propoziții clare
- Răspunsul e VALID JSON, fără text suplimentar"""

            response = ollama.chat(
                model='llama3.1:8b',
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )

            response_text = response['message']['content']
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                continue

            json_str = json_match.group()
            result = json.loads(json_str)

            if not all(key in result for key in ['title', 'key_ideas', 'summary']):
                continue

            result['key_ideas'] = result['key_ideas'][:5]
            return result

        except (json.JSONDecodeError, Exception):
            continue

    return None


def _combine_chunk_summaries(chunk_summaries: List[dict]) -> Optional[dict]:
    """
    Combină rezumatele din mai multe bucăți într-un rezumat final.

    Logică:
    - Combină toate ideile cheie și extrage top 5
    - Combină toate rezumatele și le rezumează din nou

    Args:
        chunk_summaries: Lista de dicționare cu rezumate

    Returns:
        Dict cu rezumatul final
    """
    if not chunk_summaries:
        return None

    # Dacă e o singură bucată, returneaz-o așa cum e
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    print(f"   Combinând {len(chunk_summaries)} rezumate...")

    # Colectează toate ideile cheie
    all_ideas = []
    for summary in chunk_summaries:
        all_ideas.extend(summary.get('key_ideas', []))

    # Elimină duplicatele și ține top 5
    unique_ideas = list(dict.fromkeys(all_ideas))[:5]

    # Combină rezumatele
    combined_summaries = "\n".join([s.get('summary', '') for s in chunk_summaries])

    # Rezumă din nou rezumatele combinate
    print(f"   Rezumez rezumatele combinate...")
    final_summary = _summarize_chunk(combined_summaries, chunk_num=0, total_chunks=1)

    if final_summary:
        # Merge ideile din bucăți cu ideile din rezumatul final
        final_summary['key_ideas'] = unique_ideas + final_summary.get('key_ideas', [])
        final_summary['key_ideas'] = final_summary['key_ideas'][:5]
        return final_summary

    # Fallback: combină manual dacă rezumarea finală eșuează
    return {
        'title': chunk_summaries[0].get('title', 'Rezumat'),
        'key_ideas': unique_ideas,
        'summary': combined_summaries[:500] + "..." if len(combined_summaries) > 500 else combined_summaries
    }


def summarize_text(text: str) -> Optional[dict]:
    """
    Rezumă un text lung folosind Ollama cu modelul llama3.1:8b.

    Dacă textul e mai mare de 6000 caractere:
    - Îl împarte în bucăți
    - Rezumă fiecare bucată
    - Combină rezumatele

    Args:
        text: Textul de rezumat (trebuie să fie mai mare de 100 caractere)

    Returns:
        Dict cu 'title', 'key_ideas' (listă de max 5), și 'summary'
        sau None dacă Ollama a eșuat
    """
    if not text or len(text) < 100:
        print("Textul trebuie să aibă cel puțin 100 caractere")
        return None

    # Verifica dacă e nevoie de chunking
    if len(text) > 6000:
        print(f"   Text mare ({len(text)} caractere), se împarte în bucăți de 6000...")
        chunks = _split_into_chunks(text, chunk_size=6000)
        print(f"   Creat {len(chunks)} bucată(i)")

        chunk_summaries = []
        for chunk_idx, chunk in enumerate(chunks, 1):
            print(f"   [{chunk_idx}/{len(chunks)}] Rezumez bucată ({len(chunk)} caractere)...")
            chunk_summary = _summarize_chunk(chunk, chunk_num=chunk_idx, total_chunks=len(chunks))
            if chunk_summary:
                chunk_summaries.append(chunk_summary)
            else:
                print(f"   ⚠️ Nu s-a putut rezuma bucata {chunk_idx}")

        if not chunk_summaries:
            print("   ❌ Nu s-a putut rezuma niciuna din bucăți")
            return None

        # Combină rezumatele
        final_summary = _combine_chunk_summaries(chunk_summaries)
        if final_summary:
            print(f"   ✓ Rezumat final combinat")
        return final_summary

    # Text mic: rezumă normal
    else:
        print(f"   Text mic ({len(text)} caractere), rezumare directă...")
        return _summarize_chunk(text, chunk_num=0, total_chunks=1)


def format_summary(summary_dict: dict) -> str:
    """
    Formatează rezumatul pentru afișare pe consolă.

    Args:
        summary_dict: Dicționarul returnat de summarize_text()

    Returns:
        String formatat pentru afișare
    """
    if not summary_dict:
        return "Nu s-a putut genera rezumatul"

    output = []
    output.append(f"📌 {summary_dict['title']}\n")
    output.append("🔑 Idei cheie:")
    for i, idea in enumerate(summary_dict['key_ideas'], 1):
        output.append(f"  {i}. {idea}")

    output.append(f"\n📝 Rezumat:\n{summary_dict['summary']}")

    return '\n'.join(output)
