import click
import sys
from scraper import scrape_url
from reader import read_file
from summarizer import summarize_text, format_summary


@click.command()
@click.option('--url', default=None, help='URL-ul paginii web de analizat')
@click.option('--file', default=None, help='Calea către fișierul local (PDF sau TXT)')
def main(url, file):
    """
    KnowledgeFilter - Extrage și rezumă ideile principale din URL-uri sau fișiere.

    Exemplu:
        python main.py --url "https://example.com"
        python main.py --file "document.pdf"
    """
    # Validare: trebuie să fie exact una din opțiuni
    if not url and not file:
        click.echo("❌ Eroare: Trebuie să furnizezi --url sau --file", err=True)
        click.echo("Folosi: python main.py --help", err=True)
        sys.exit(1)

    if url and file:
        click.echo("❌ Eroare: Nu poți folosi --url și --file în același timp", err=True)
        sys.exit(1)

    # Extrage textul
    text = None
    if url:
        click.echo(f"📥 Descărcând: {url}...", err=True)
        text = scrape_url(url)
        if not text:
            click.echo("❌ Nu s-a putut descărca pagina", err=True)
            sys.exit(1)

    elif file:
        click.echo(f"📂 Citind: {file}...", err=True)
        text = read_file(file)
        if not text:
            click.echo("❌ Nu s-a putut citi fișierul", err=True)
            sys.exit(1)

    # Rezumă textul
    click.echo("🧠 Analizez textul...", err=True)
    summary = summarize_text(text)

    if not summary:
        click.echo("❌ Nu s-a putut genera rezumatul", err=True)
        sys.exit(1)

    # Afișează rezultatul
    click.echo("")  # Linie goală pentru separare
    click.echo(format_summary(summary))
    click.echo("")  # Linie goală la sfârșit


if __name__ == '__main__':
    main()
