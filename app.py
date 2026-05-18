import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from scraper import scrape_url
from reader import read_file
from summarizer import summarize_text, format_summary
from book_analyzer import analyze_book


class KnowledgeFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Knowledge Filter - Analizor Inteligent")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Setare tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.selected_file = None
        self.summary_dict = None
        self.book_analysis_result = None
        self.setup_ui()

    def setup_ui(self):
        """Configurează interfața grafică"""

        # Frame pentru input
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(padx=20, pady=20, fill="x")

        # Eticheta și câmp pentru URL
        url_label = ctk.CTkLabel(input_frame, text="URL (opțional):", font=("Arial", 12, "bold"))
        url_label.pack(anchor="w")

        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="https://example.com",
            font=("Arial", 11),
            height=40
        )
        self.url_entry.pack(fill="x", pady=(5, 15))

        # Frame pentru butoanele de fișier și analiză
        button_frame = ctk.CTkFrame(input_frame)
        button_frame.pack(fill="x", pady=(0, 15))

        # Buton "Alege PDF"
        self.file_button = ctk.CTkButton(
            button_frame,
            text="📁 Alege PDF",
            command=self.choose_file,
            font=("Arial", 11, "bold"),
            height=40,
            width=150
        )
        self.file_button.pack(side="left", padx=(0, 10))

        # Eticheta pentru fișierul selectat
        self.file_label = ctk.CTkLabel(
            button_frame,
            text="Niciun fișier selectat",
            text_color="gray",
            font=("Arial", 10)
        )
        self.file_label.pack(side="left", fill="x", expand=True)

        # Buton "Analizează"
        self.analyze_button = ctk.CTkButton(
            input_frame,
            text="🔍 Analizează",
            command=self.analyze,
            font=("Arial", 12, "bold"),
            height=45,
            fg_color="#1f6aa5"
        )
        self.analyze_button.pack(fill="x", pady=(0, 10))

        # Buton "Analizează Carte"
        self.analyze_book_button = ctk.CTkButton(
            input_frame,
            text="📚 Analizează Carte",
            command=self.analyze_book_handler,
            font=("Arial", 12, "bold"),
            height=45,
            fg_color="#7c3aed"
        )
        self.analyze_book_button.pack(fill="x", pady=(0, 15))

        # Separator
        separator = ctk.CTkFrame(self.root, height=2, fg_color="gray30")
        separator.pack(fill="x", padx=20)

        # Frame pentru output
        output_label = ctk.CTkLabel(
            self.root,
            text="📊 Rezultat:",
            font=("Arial", 12, "bold")
        )
        output_label.pack(anchor="w", padx=20, pady=(15, 5))

        # Text area pentru rezultat
        self.output_text = ctk.CTkTextbox(
            self.root,
            font=("Courier", 10),
            state="normal"
        )
        self.output_text.pack(padx=20, pady=(5, 10), fill="both", expand=True)

        # Frame pentru butoane de export
        export_frame = ctk.CTkFrame(self.root)
        export_frame.pack(padx=20, pady=(0, 10), fill="x")

        # Buton "Exportă ca TXT"
        self.export_txt_button = ctk.CTkButton(
            export_frame,
            text="💾 Exportă TXT",
            command=self.export_txt_result,
            font=("Arial", 11, "bold"),
            height=40,
            fg_color="#17a657",
            state="disabled"
        )
        self.export_txt_button.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Buton "Exportă ca PDF"
        self.export_pdf_button = ctk.CTkButton(
            export_frame,
            text="📄 Exportă PDF",
            command=self.export_pdf_result,
            font=("Arial", 11, "bold"),
            height=40,
            fg_color="#d97706",
            state="disabled"
        )
        self.export_pdf_button.pack(side="left", fill="x", expand=True)

        # Status bar
        self.status_label = ctk.CTkLabel(
            self.root,
            text="Gata. Introdu un URL sau selectează un fișier și apasă 'Analizează'",
            text_color="gray",
            font=("Arial", 9)
        )
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))

    def choose_file(self):
        """Deschide file explorer pentru selectarea unui PDF"""
        file_path = filedialog.askopenfilename(
            title="Selectează un fișier",
            filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            self.selected_file = file_path
            # Afișează doar numele fișierului, nu calea completă
            file_name = file_path.split("/")[-1]
            self.file_label.configure(text=f"✓ {file_name}", text_color="white")

    def analyze(self):
        """Declanșează analiza (URL sau fișier) într-un thread separat"""
        url = self.url_entry.get().strip()

        if not url and not self.selected_file:
            messagebox.showwarning(
                "Input lipsă",
                "Te rog introdu un URL sau selectează un fișier"
            )
            return

        # Dezactivează butoanele în timp ce se procesează
        self.analyze_button.configure(state="disabled")
        self.export_txt_button.configure(state="disabled")
        self.export_pdf_button.configure(state="disabled")
        self.status_label.configure(text="⏳ Se procesează...", text_color="orange")
        self.output_text.delete("1.0", "end")

        # Rulează în thread separat pentru a nu bloca UI
        thread = threading.Thread(target=self._analyze_thread, args=(url, self.selected_file))
        thread.daemon = True
        thread.start()

    def _analyze_thread(self, url, file_path):
        """Execută analiza pe un thread separat"""
        try:
            # Pasul 1: Extrage textul (din URL sau fișier)
            if url:
                self.update_status("Se descarcă pagina...")
                text = scrape_url(url)
            else:
                self.update_status("Se citește fișierul...")
                text = read_file(file_path)

            if not text:
                self.update_status("❌ Eroare: Nu s-a putut extrage textul", "red")
                self.root.after(0, lambda: self.output_text.insert("end", "❌ Eroare: Nu s-a putut extrage textul din sursă"))
                return

            # Pasul 2: Rezumă textul
            self.update_status("Se analizează conținutul...")
            summary_dict = summarize_text(text)

            if not summary_dict:
                self.update_status("❌ Eroare: Nu s-a putut genera rezumatul", "red")
                self.root.after(0, lambda: self.output_text.insert("end", "❌ Eroare: Nu s-a putut genera rezumatul. Asigură-te că Ollama rulează."))
                return

            # Pasul 3: Formatează și afișează
            formatted_summary = format_summary(summary_dict)
            self.root.after(0, lambda: self.output_text.insert("end", formatted_summary))
            self.root.after(0, lambda: self._store_summary(summary_dict))
            self.update_status("✓ Analiza completă", "green")
            self.root.after(0, lambda: self.export_txt_button.configure(state="normal"))
            self.root.after(0, lambda: self.export_pdf_button.configure(state="normal"))

        except Exception as e:
            error_msg = f"❌ Eroare neașteptată: {str(e)}"
            self.update_status(error_msg, "red")
            self.root.after(0, lambda: self.output_text.insert("end", error_msg))
        finally:
            # Reactivează butonul
            self.root.after(0, lambda: self.analyze_button.configure(state="normal"))

    def update_status(self, message, color="white"):
        """Actualizează status bar-ul din thread-ul de lucru"""
        self.root.after(0, lambda: self.status_label.configure(text=message, text_color=color))

    def _store_summary(self, summary_dict):
        """Stochează rezumatul pentru export"""
        self.summary_dict = summary_dict

    def analyze_book_handler(self):
        """Declanșează analiza unei cărți (PDF) într-un thread separat"""
        if not self.selected_file:
            messagebox.showwarning(
                "Input lipsă",
                "Te rog selectează un fișier PDF"
            )
            return

        # Dezactivează butoanele în timp ce se procesează
        self.analyze_button.configure(state="disabled")
        self.analyze_book_button.configure(state="disabled")
        self.export_txt_button.configure(state="disabled")
        self.export_pdf_button.configure(state="disabled")
        self.status_label.configure(text="⏳ Se citește cartea...", text_color="orange")
        self.output_text.delete("1.0", "end")

        # Rulează în thread separat pentru a nu bloca UI
        thread = threading.Thread(target=self._analyze_book_thread, args=(self.selected_file,))
        thread.daemon = True
        thread.start()

    def _analyze_book_thread(self, file_path):
        """Execută analiza cărții pe un thread separat"""
        try:
            self.update_status("📖 Se citește PDF-ul...", "white")

            # Apelează analyze_book
            result = analyze_book(file_path)

            if not result:
                self.update_status("❌ Eroare: Nu s-a putut analiza cartea", "red")
                self.root.after(0, lambda: self.output_text.insert("end", "❌ Eroare: Nu s-a putut analiza cartea. Asigură-te că Ollama rulează."))
                return

            # Afișează raportul complet
            self.update_status("📋 Se genereaza raportul final...", "white")
            self.root.after(0, lambda: self.output_text.insert("end", result['full_report']))

            # Stochează rezultatul pentru export
            self.root.after(0, lambda: self._store_book_analysis(result))

            # Actualizează status
            chapters_completed = sum(1 for ch in result['chapters'] if ch['status'] == 'completed')
            self.update_status(f"✓ Analiza cărții completă ({chapters_completed}/{result['total_chapters']} capitole)", "green")

            # Activează butoanele de export
            self.root.after(0, lambda: self.export_txt_button.configure(state="normal"))
            self.root.after(0, lambda: self.export_pdf_button.configure(state="normal"))

        except Exception as e:
            error_msg = f"❌ Eroare neașteptată: {str(e)}"
            self.update_status(error_msg, "red")
            self.root.after(0, lambda: self.output_text.insert("end", error_msg))
        finally:
            # Reactivează butoanele
            self.root.after(0, lambda: self.analyze_button.configure(state="normal"))
            self.root.after(0, lambda: self.analyze_book_button.configure(state="normal"))

    def _store_book_analysis(self, result):
        """Stochează rezultatul analizei cărții pentru export"""
        self.book_analysis_result = result

    def export_txt_result(self):
        """Deschide dialog pentru salvarea rezumatului ca TXT"""
        file_path = filedialog.asksaveasfilename(
            title="Salvează rezumatul",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                result_text = self.output_text.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result_text)
                messagebox.showinfo("Succes", f"Rezumatul a fost salvat în:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Eroare", f"Nu s-a putut salva fișierul:\n{str(e)}")

    def export_pdf_result(self):
        """Deschide dialog pentru salvarea rezumatului ca PDF"""
        if not self.summary_dict and not self.book_analysis_result:
            messagebox.showerror("Eroare", "Nu există rezumat de exportat")
            return

        file_path = filedialog.asksaveasfilename(
            title="Salvează rezumatul ca PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if file_path:
            try:
                if self.book_analysis_result:
                    self._generate_book_pdf(file_path, self.book_analysis_result)
                else:
                    self._generate_pdf(file_path, self.summary_dict)
                messagebox.showinfo("Succes", f"Rezumatul a fost salvat în:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Eroare", f"Nu s-a putut salva fișierul PDF:\n{str(e)}")

    def _generate_pdf(self, file_path, summary_dict):
        """Generează un PDF frumos cu rezumatul"""
        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        # Stil personalizat pentru titlu
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1f6aa5',
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        # Stil pentru idei cheie
        ideas_style = ParagraphStyle(
            'IdeasTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#17a657',
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        # Stil pentru text normal
        text_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=6
        )

        # Stil pentru bullet points
        bullet_style = ParagraphStyle(
            'BulletText',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=20,
            spaceAfter=6
        )

        # Titlu
        title = Paragraph(summary_dict['title'], title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*inch))

        # Idei cheie
        ideas_title = Paragraph("Idei Cheie", ideas_style)
        story.append(ideas_title)

        for idea in summary_dict['key_ideas']:
            bullet = Paragraph(f"• {idea}", bullet_style)
            story.append(bullet)

        story.append(Spacer(1, 0.2*inch))

        # Rezumat
        summary_title = Paragraph("Rezumat", ideas_style)
        story.append(summary_title)

        summary_text = Paragraph(summary_dict['summary'], text_style)
        story.append(summary_text)

        # Build PDF
        doc.build(story)

    def _generate_book_pdf(self, file_path, book_result):
        """Generează un PDF cu raportul analizei cărții"""
        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        # Stil pentru titlu carte
        title_style = ParagraphStyle(
            'BookTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1f6aa5',
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        # Stil pentru titlu capitol
        chapter_style = ParagraphStyle(
            'ChapterTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#7c3aed',
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        # Stil pentru idei cheie
        ideas_style = ParagraphStyle(
            'IdeasTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor='#17a657',
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        )

        # Stil pentru text normal
        text_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=4
        )

        # Stil pentru bullet points
        bullet_style = ParagraphStyle(
            'BulletText',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=20,
            spaceAfter=3
        )

        # Titlu carte
        title = Paragraph(f"📖 {book_result['book_title']}", title_style)
        story.append(title)

        chapters_info = Paragraph(f"Total capitole: {book_result['total_chapters']}", text_style)
        story.append(chapters_info)
        story.append(Spacer(1, 0.2*inch))

        # Pentru fiecare capitol
        for chapter in book_result['chapters']:
            if chapter['summary']:
                # Titlu capitol
                chapter_title = Paragraph(f"Capitol {chapter['number']}: {chapter['title']}", chapter_style)
                story.append(chapter_title)

                summary_data = chapter['summary']

                # Titlu rezumat
                summary_title = Paragraph(summary_data.get('title', 'Rezumat'), ideas_style)
                story.append(summary_title)

                # Idei cheie
                ideas_label = Paragraph("Idei cheie:", ideas_style)
                story.append(ideas_label)

                for idea in summary_data.get('key_ideas', []):
                    bullet = Paragraph(f"• {idea}", bullet_style)
                    story.append(bullet)

                story.append(Spacer(1, 0.1*inch))

                # Rezumat text
                summary_text = Paragraph(summary_data.get('summary', ''), text_style)
                story.append(summary_text)

                story.append(Spacer(1, 0.15*inch))
                story.append(PageBreak())

        # Build PDF
        doc.build(story)


def main():
    root = ctk.CTk()
    app = KnowledgeFilterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
