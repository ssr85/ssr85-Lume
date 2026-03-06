from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_proposal_pdf(content: str, output_path: str):
    """Generates a professional proposal PDF from markdown-like content."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'ProposalTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#0F1F3D")
    )

    # Simplified parsing (assuming the content follows the 8 sections)
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['Heading2']))
        elif line.strip():
            story.append(Paragraph(line, styles['BodyText']))
            story.append(Spacer(1, 12))

    doc.build(story)

def generate_invoice_pdf(invoice_data: dict, output_path: str):
    """Generates a professional glassmorphism-inspired invoice PDF (simulated style)."""
    # Logic for invoice PDF would go here...
    pass
