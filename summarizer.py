import json
import re
import traceback
import ollama
from typing import Optional


def summarize_text(text: str) -> Optional[dict]:
    """
    Rezumă un text lung folosind Ollama cu modelul llama3.2.

    Args:
        text: Textul de rezumat (trebuie să fie mai mare de 100 caractere)

    Returns:
        Dict cu 'title', 'key_ideas' (listă de max 5), și 'summary'
        sau None dacă Ollama a eșuat
    """
    if not text or len(text) < 100:
        print("Textul trebuie să aibă cel puțin 100 caractere")
        return None

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            prompt = f"""You must respond with only a JSON object, no other text, no markdown, no backticks.

Analizează textul următor și extrage ideile principale.

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
                model='llama3.2',
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )

            # Extrage textul din răspuns
            response_text = response['message']['content']

            # Extrage JSON-ul din răspuns folosind regex (caută { și })
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print(f"Încercare {attempt}/{max_retries}: Nu s-a găsit JSON în răspunsul Ollama")
                if attempt == max_retries:
                    return None
                continue

            json_str = json_match.group()
            result = json.loads(json_str)

            # Validare de bază
            if not all(key in result for key in ['title', 'key_ideas', 'summary']):
                print(f"Încercare {attempt}/{max_retries}: Răspunsul Ollama nu are structura așteptată")
                if attempt == max_retries:
                    return None
                continue

            # Asigură-te că key_ideas are max 5 elemente
            result['key_ideas'] = result['key_ideas'][:5]

            print(f"Analiza reușită la încercarea {attempt}/{max_retries}")
            return result

        except json.JSONDecodeError:
            print(f"Încercare {attempt}/{max_retries}: Nu s-a putut parseza răspunsul Ollama ca JSON")
            if attempt == max_retries:
                return None
            continue
        except Exception as e:
            print(f"Încercare {attempt}/{max_retries}: Eroare la apelul Ollama: {e}")
            traceback.print_exc()
            if attempt == max_retries:
                return None
            continue

    return None


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
