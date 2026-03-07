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
    """Generates a professional invoice PDF."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    header_style = ParagraphStyle(
        'InvoiceHeader',
        parent=styles['Heading1'],
        fontSize=26,
        spaceAfter=20,
        textColor=colors.HexColor("#4A72FF")
    )
    
    story.append(Paragraph(f"INVOICE: {invoice_data['invoice_number']}", header_style))
    
    # Invoice Metadata
    meta_style = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#666666"))
    story.append(Paragraph(f"<b>Date:</b> {invoice_data['invoice_date']}", meta_style))
    story.append(Paragraph(f"<b>Due Date:</b> {invoice_data['due_date']}", meta_style))
    story.append(Spacer(1, 25))

    # Billed To Section
    client = invoice_data.get('client', {})
    if client:
        story.append(Paragraph("<b>BILLED TO:</b>", styles['Heading4']))
        story.append(Paragraph(f"<b>{client.get('name', '')}</b>", styles['Normal']))
        if client.get('company'):
            story.append(Paragraph(client.get('company'), styles['Normal']))
        if client.get('email'):
            story.append(Paragraph(client.get('email'), styles['Normal']))
        address = client.get('address', {})
        if address.get('city') or address.get('country'):
            city_str = address.get('city', '')
            country_str = address.get('country', '')
            loc = f"{city_str}, {country_str}".strip(" ,")
            story.append(Paragraph(loc, styles['Normal']))
        if client.get('gstin'):
            story.append(Paragraph(f"GSTIN: {client.get('gstin')}", styles['Normal']))
        story.append(Spacer(1, 20))

    project_name = invoice_data.get('project_name')
    if project_name:
        story.append(Paragraph(f"<b>For Project:</b> {project_name}", styles['Heading4']))
        story.append(Spacer(1, 15))

    # Table for items
    data = [["Description", "Hours", "Rate", "Subtotal"]]
    for item in invoice_data['items']:
        # Wrap description in Paragraph to prevent text overflow
        desc_p = Paragraph(item['description'], styles['Normal'])
        data.append([
            desc_p,
            str(item['hours']),
            f"${item['rate']}",
            f"${item['subtotal']}"
        ])
    
    data.append(["", "", "Total:", f"${invoice_data['grand_total']}"])

    t = Table(data, colWidths=[300, 50, 70, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4A72FF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey)
    ]))
    
    story.append(t)
    doc.build(story)
