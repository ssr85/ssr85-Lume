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
    """Generates a professional invoice PDF matching the strict grid layout."""
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # 1. Header (Centered)
    header_style = ParagraphStyle(
        'InvoiceHeader',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=1, # Center
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph("FREELANCER INVOICE", header_style))

    # 2. Freelancer Info (Top Left)
    freelancer_name = invoice_data.get('freelancer_name', 'Shubh Maheshwari')
    freelancer_email = invoice_data.get('freelancer_email', 'shubh@example.com')
    
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, leading=14)
    story.append(Paragraph(f"<b>Freelancer:</b> {freelancer_name}", info_style))
    story.append(Paragraph(f"<b>Email:</b> {freelancer_email}", info_style))
    story.append(Spacer(1, 15))

    # 3. Metadata Grid (4 Columns)
    client = invoice_data.get('client', {})
    client_name = client.get('name', '')
    project_name = invoice_data.get('project_name', '')
    
    meta_data = [
        ["Invoice Number", invoice_data.get('invoice_number', ''), "Invoice Status", invoice_data.get('status', 'UNPAID')],
        ["Invoice Date", invoice_data.get('invoice_date', ''), "Due Date", invoice_data.get('due_date', '')],
        ["Client Name", client_name, "Project Name", project_name]
    ]

    meta_table = Table(meta_data, colWidths=[110, 150, 110, 160])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), # Col 1 bold
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'), # Col 3 bold
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 4. Items Header
    story.append(Paragraph("<i><b>Work Items / Milestones</b></i>", ParagraphStyle('SubHeader', parent=styles['Heading3'], fontSize=12, spaceAfter=8)))

    # 5. Items Grid
    items_data = [["Work Item / Milestone", "Hours", "Rate ($)", "Subtotal ($)"]]
    for item in invoice_data.get('items', []):
        desc_p = Paragraph(item.get('description', ''), styles['Normal'])
        items_data.append([
            desc_p,
            str(item.get('hours', '')),
            str(item.get('rate', '')),
            str(item.get('subtotal', ''))
        ])

    grand_total = invoice_data.get('grand_total', 0)
    tax_percent = float(invoice_data.get('tax_percent', 0)) # updated key
    
    subtotal = invoice_data.get('subtotal', grand_total)
    tax_amount = invoice_data.get('tax_amount', 0)
    
    items_data.append(["", "", "Total Before Tax", str(subtotal)])
    items_data.append(["", "", f"Tax / GST ({tax_percent}%)", str(tax_amount)])
    items_data.append(["", "", "Grand Total Payable", str(grand_total)])

    total_paid = invoice_data.get('total_paid', 0)
    if total_paid > 0:
        items_data.append(["", "", "Amount Paid", f"-{total_paid}"])
        items_data.append(["", "", "Pending Balance", str(invoice_data.get('total_pending', 0))])

    num_items = len(invoice_data.get('items', []))
    
    t = Table(items_data, colWidths=[270, 60, 100, 100])
    
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), # Center hours, rate, subtotal cols globally
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Left align description
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, num_items), 0.5, colors.grey), # Grid over headers and items
        ('PADDING', (0, 0), (-1, -1), 6)
    ]
    
    # Bottom summary block styling
    summary_start_row = num_items + 1
    # Right align the labels
    style_commands.append(('ALIGN', (2, summary_start_row), (2, -1), 'RIGHT'))
    # Grid for the summary block
    style_commands.append(('GRID', (2, summary_start_row), (-1, -1), 0.5, colors.grey))
    # Grand total bold
    grand_total_row = summary_start_row + 2
    style_commands.append(('FONTNAME', (2, grand_total_row), (-1, grand_total_row), 'Helvetica-Bold'))
    
    # Highlight paid/pending if present
    if total_paid > 0:
        pending_row = grand_total_row + 2
        pending_val = invoice_data.get('total_pending', 0)
        color = colors.HexColor("#e74c3c") if pending_val > 0 else colors.HexColor("#2ecc71")
        style_commands.append(('TEXTCOLOR', (2, pending_row), (-1, pending_row), color))
        style_commands.append(('FONTNAME', (2, pending_row), (-1, pending_row), 'Helvetica-Bold'))

    t.setStyle(TableStyle(style_commands))
    story.append(t)
    story.append(Spacer(1, 30))

    # 6. Bank Details section
    story.append(Paragraph("<i><b>Freelancer Bank / Payment Details</b></i>", ParagraphStyle('SubHeader2', parent=styles['Heading4'], fontSize=11, spaceAfter=6)))
    
    bank_details = "Bank: HDFC Bank | A/C: 1234567890 | IFSC: HDFC0001234 | UPI: shubh@upi" # Hardcoded proxy or we can fetch from ENV
    import os
    env_bank = os.getenv("BANK_DETAILS")
    if env_bank: bank_details = env_bank
        
    story.append(Paragraph(bank_details, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # 7. Notes to Client
    story.append(Paragraph("<i><b>Notes to Client</b></i>", ParagraphStyle('SubHeader3', parent=styles['Heading4'], fontSize=11, spaceAfter=6)))
    story.append(Paragraph("Thank you for your business. Please complete the payment before the due date.", styles['Normal']))

    doc.build(story)
