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
    story.append(Paragraph("INVOICE", header_style))

    # 2. Freelancer Info & Metadata Grid (Combined Top section)
    freelancer_name = invoice_data.get('freelancer_name', 'Shubh Maheshwari')
    freelancer_email = invoice_data.get('freelancer_email', 'shubh@example.com')
    freelancer_phone = invoice_data.get('freelancer_phone', '+91 9876543210')
    freelancer_city = invoice_data.get('freelancer_city', 'New Delhi')
    freelancer_country = invoice_data.get('freelancer_country', 'India')

    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, leading=14)
    
    # Left side: Freelancer details
    freelancer_p = []
    freelancer_p.append(Paragraph(f"<b>{freelancer_name.upper()}</b>", info_style))
    freelancer_p.append(Paragraph(f"{freelancer_email} - {freelancer_phone}", info_style))
    freelancer_p.append(Paragraph(f"{freelancer_city}, {freelancer_country}", info_style))

    # Right side: Invoice meta
    meta_p = []
    meta_p.append(Paragraph(f"Invoice #: <b>{invoice_data.get('invoice_number', '')}</b>", ParagraphStyle('Meta', parent=info_style, alignment=2)))
    meta_p.append(Paragraph(f"Date: <b>{invoice_data.get('invoice_date', '')}</b>", ParagraphStyle('Meta', parent=info_style, alignment=2)))
    meta_p.append(Paragraph(f"Due Date: <b>{invoice_data.get('due_date', '')}</b>", ParagraphStyle('Meta', parent=info_style, alignment=2)))

    top_data = [[freelancer_p, meta_p]]
    top_table = Table(top_data, colWidths=[270, 260])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    # Outer box for top section to match INVOICE_GENERATION.md
    outer_top_data = [[top_table]]
    outer_top_table = Table(outer_top_data, colWidths=[530])
    outer_top_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(outer_top_table)

    # 3. Bill To Section
    client = invoice_data.get('client', {})
    client_name = client.get('name', 'N/A')
    client_company = client.get('company_name', 'N/A')
    client_email = client.get('email', 'N/A')
    client_gstin = client.get('gstin', '')
    client_phone = client.get('phone', '')

    bill_to_p = []
    bill_to_p.append(Paragraph("<b>BILL TO:</b>", info_style))
    bill_to_p.append(Paragraph(client_name, info_style))
    if client_company:
        bill_to_p.append(Paragraph(client_company, info_style))
    bill_to_p.append(Paragraph(client_email, info_style))
    
    if client_gstin or client_phone:
        gstin_str = f"GSTIN: {client_gstin}" if client_gstin else "GSTIN: N/A"
        phone_str = f"Phone: {client_phone}" if client_phone else "Phone: N/A"
        bill_to_p.append(Paragraph(f"{gstin_str} | {phone_str}", info_style))

    bill_to_data = [[bill_to_p]]
    bill_to_table = Table(bill_to_data, colWidths=[530])
    bill_to_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('PADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(bill_to_table)

    # 4. Items Grid
    items_data = [["#", "Description", "Hrs", "Rate", "Amount"]]
    for i, item in enumerate(invoice_data.get('items', [])):
        desc_p = Paragraph(item.get('description', ''), styles['Normal'])
        rate_val = item.get('rate', '')
        rate_str = f"${rate_val}" if rate_val else ""
        subtotal_val = item.get('subtotal', '')
        subtotal_str = f"${subtotal_val}" if subtotal_val else ""
        items_data.append([
            str(i + 1),
            desc_p,
            str(item.get('hours', '')),
            rate_str,
            subtotal_str
        ])

    num_items = len(invoice_data.get('items', []))
    
    t = Table(items_data, colWidths=[30, 240, 60, 100, 100])
    
    style_commands = [
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('GRID', (0, 0), (-1, num_items), 0.5, colors.black), # Grid over headers and items
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'), # Center hours, rate, amount
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center index
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Left align description
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]
    t.setStyle(TableStyle(style_commands))
    story.append(t)

    # 5. Totals block
    grand_total = invoice_data.get('grand_total', 0)
    tax_percent = float(invoice_data.get('tax_percent', 0))
    subtotal = invoice_data.get('subtotal', grand_total)
    tax_amount = invoice_data.get('tax_amount', 0)
    
    totals_data = []
    totals_data.append(["", "", "Subtotal:", f"${subtotal}"])
    totals_data.append(["", "", f"Tax ({tax_percent}%):", f"${tax_amount}"])
    totals_data.append(["", "", "Total Amount:", f"${grand_total}"])

    total_paid = invoice_data.get('total_paid', 0)
    if total_paid > 0:
        totals_data.append(["", "", "Amount Paid:", f"${total_paid}"])
        totals_data.append(["", "", "PENDING DUE:", f"${invoice_data.get('total_pending', 0)}"])

    totals_table = Table(totals_data, colWidths=[30, 240, 160, 100])
    
    totals_styles = [
        ('BOX', (0,0), (-1,-1), 0.5, colors.black), # Outline around totals section to match invoice box
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]
    
    # Grand Total Bold
    totals_styles.append(('FONTNAME', (2, 2), (-1, 2), 'Helvetica-Bold'))
    
    if total_paid > 0:
        totals_styles.append(('FONTNAME', (2, 4), (-1, 4), 'Helvetica-Bold'))
        
    totals_table.setStyle(TableStyle(totals_styles))
    story.append(totals_table)

    # 6. Payment block & Notes
    bank_details = "Bank: HDFC Bank | A/C: 1234567890 | IFSC: HDFC0001234 | UPI: shubh@upi"
    import os
    env_bank = os.getenv("BANK_DETAILS")
    if env_bank: bank_details = env_bank
    
    payment_notes_p = []
    payment_notes_p.append(Paragraph("<b>PAYMENT DETAILS</b>", info_style))
    payment_notes_p.append(Paragraph(bank_details, info_style))
    payment_notes_p.append(Spacer(1, 10))
    payment_notes_p.append(Paragraph("<b>NOTES:</b> Thank you for your business. Please complete the payment before the due date.", info_style))

    payment_notes_data = [[payment_notes_p]]
    payment_notes_table = Table(payment_notes_data, colWidths=[530])
    payment_notes_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(payment_notes_table)

    doc.build(story)
