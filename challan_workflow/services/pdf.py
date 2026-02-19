import pdfkit
class PDFGenerator:
    def __init__(self):
        self.options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
        }

    def url_to_pdf(self, url: str) -> bool:
        """Convert URL to PDF"""
        try:
            pdfkit.from_url(url, output_path="test.pdf", options=self.options)
        except Exception as e:
            print(f"Error converting URL to PDF: {e}")
            return None

    
if __name__ == "__main__":
    url = "https://echallan.parivahan.gov.in/api/print-challan-receipt?data=nU59z5U%2BZKVeOv5dAgLQRCgiWKqIEKZHtb%2FdZVlVTsIoRR%2B91TUCfMIgeIbcs2fqjoESs7zdJN94AA%2B5Tm0toMF1pwYmvDD7oFJQZcRens%2BsZ7w3OVGMkoPi3S0ClEgSBN1%2Bko9F5fb9AStA1JE5dg6Ckyk5VDMmPDUso1rJhCABD4hjziyWEQYiqrUTwrH4twX2VvrJkt1Ccck6szkWTYJY4I%2FklcPHUx1WsyONXYlwcwaDC2v9WeUMS5JOGz1ma%2FlgzBJy3Aisc3akcTRWmOaWqQMwwdGLrsa5cYwip2QTsjGvWI80oZ3zXZIPCIF7AGOmRmggYZ0IQxpaEHEm406GkG24ptQLDNeKnA9c9F6RVn8qdMxEgM1XKeMVCWkt"
    pdf_generator = PDFGenerator()
    pdf_generator.url_to_pdf(url)