import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading, requests, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fpdf import FPDF
import datetime


visited_links = set()
emails_found = set()
phones_found = set()
stop_flag = False

class WebCrawlerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SpiderSense - Smart Web Crawler")
        self.root.geometry("800x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- GUI Components ---
        self.url_entry = ctk.CTkEntry(root, placeholder_text="Enter website URL", width=600)
        self.url_entry.pack(pady=10)

        self.depth_entry = ctk.CTkEntry(root, placeholder_text="Enter crawl depth (e.g., 2)", width=600)
        self.depth_entry.pack(pady=5)

        self.start_button = ctk.CTkButton(root, text="Start Crawling", command=self.start_crawl)
        self.start_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(root, text="Stop Crawling", command=self.stop_crawl)
        self.stop_button.pack(pady=5)

        self.result_box = ctk.CTkTextbox(root, width=750, height=350)
        self.result_box.pack(pady=10)

        self.export_button = ctk.CTkButton(root, text="Export Report (PDF)", command=self.export_pdf, state="disabled")
        self.export_button.pack(pady=5)

    def start_crawl(self):
        url = self.url_entry.get().strip()
        depth = self.depth_entry.get().strip()

        # Validation
        if not url.startswith("http"):
            messagebox.showerror("Invalid URL", "URL must start with http:// or https://")
            return

        try:
            depth = int(depth)
        except ValueError:
            messagebox.showerror("Invalid Depth", "Depth must be an integer.")
            return

        # Reset flags and data
        global stop_flag
        stop_flag = False
        visited_links.clear()
        emails_found.clear()
        phones_found.clear()

        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", f"Starting crawl on: {url} with depth: {depth}\n")

        self.export_button.configure(state="disabled")
        threading.Thread(target=self.run_crawler, args=(url, depth), daemon=True).start()

    def stop_crawl(self):
        global stop_flag
        stop_flag = True
        self.result_box.insert("end", "\nCrawling stopped by user.\n")
        self.result_box.see("end")

    def run_crawler(self, url, depth):
        try:
            base_domain = urlparse(url).netloc
            self.crawl(url, depth, base_domain)
        except Exception as e:
            self.result_box.insert("end", f"Unexpected error: {e}\n")
        finally:
            self.result_box.insert("end", f"\nCrawl completed.\nPages visited: {len(visited_links)}\n")
            self.result_box.insert("end", f"\nEmails Found:\n" + "\n".join(emails_found) + "\n")
            self.result_box.insert("end", f"\nPhone Numbers Found:\n" + "\n".join(phones_found) + "\n")
            self.export_button.configure(state="normal")

    def crawl(self, url, depth, base_domain):
        global stop_flag

        if stop_flag or depth == 0 or url in visited_links:
            return

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            visited_links.add(url)

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract emails
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text)
            emails_found.update(emails)

            # Extract phone numbers
            phones = re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d", response.text)
            phones_found.update(phones)

            self.result_box.insert("end", f"Visited: {url}\n")
            self.result_box.see("end")

            # Recursively crawl links
            for tag in soup.find_all("a", href=True):
                next_url = urljoin(url, tag['href'])
                parsed = urlparse(next_url)

                # Only follow links within the same domain
                if parsed.scheme in ["http", "https"] and parsed.netloc == base_domain:
                    self.crawl(next_url, depth - 1, base_domain)

        except Exception as e:
            self.result_box.insert("end", f"Error accessing {url}: {e}\n")
            self.result_box.see("end")

    def export_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Web Crawler Report", ln=True, align='C')
        pdf.ln(10)
        pdf.multi_cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        pdf.multi_cell(0, 10, f"Total Pages Visited: {len(visited_links)}\n")
        pdf.multi_cell(0, 10, f"Total Emails Found: {len(emails_found)}\n")
        pdf.multi_cell(0, 10, f"Total Phone Numbers Found: {len(phones_found)}\n\n")

        if emails_found:
            pdf.multi_cell(0, 10, "Emails:\n" + "\n".join(emails_found) + "\n")

        if phones_found:
            pdf.multi_cell(0, 10, "Phone Numbers:\n" + "\n".join(phones_found))

        pdf.output(file_path)
        messagebox.showinfo("Export Complete", f"PDF saved to:\n{file_path}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = WebCrawlerApp(root)
    root.mainloop()