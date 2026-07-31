import io

import qrcode
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

# Layout constants
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 25 * mm
MARGIN_RIGHT = 25 * mm
MARGIN_TOP = 25 * mm
MARGIN_BOTTOM = 20 * mm
SECTION_GAP = 15 * mm
CARD_PADDING_X = 6 * mm
CARD_PADDING_Y = 4 * mm

CONTENT_X = MARGIN_LEFT
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
TOP_Y = PAGE_HEIGHT - MARGIN_TOP

# Typography
FONT_BRAND = ("Helvetica-Bold", 22)
FONT_TITLE = ("Helvetica-Bold", 14)
FONT_SUBTITLE = ("Helvetica", 10)
FONT_SECTION = ("Helvetica-Bold", 10)
FONT_LABEL = ("Helvetica-Bold", 8.3)
FONT_VALUE = ("Helvetica", 9.8)
FONT_MONO = ("Courier", 9)
FONT_STATUS = ("Helvetica-Bold", 12)
FONT_FOOTER = ("Helvetica", 9)

# Colors
PRIMARY = colors.HexColor("#1E3A8A")
SECONDARY = colors.HexColor("#3B82F6")
BORDER = colors.HexColor("#CBD5E1")
CARD_BG = colors.HexColor("#F8FAFC")
STATUS_GREEN = colors.HexColor("#16A34A")
STATUS_GREEN_BG = colors.HexColor("#DCFCE7")
TEXT = colors.HexColor("#0F172A")
LABEL = colors.HexColor("#64748B")
WHITE = colors.white


def _format_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")
    return str(value)


def _issuer_name(certificate):
    issuer = getattr(certificate, "issuer", None)
    if not issuer:
        return "Not specified"

    get_full_name = getattr(issuer, "get_full_name", None)
    if callable(get_full_name):
        full_name = get_full_name().strip()
        if full_name:
            return full_name

    first_name = getattr(issuer, "first_name", "").strip()
    last_name = getattr(issuer, "last_name", "").strip()
    if first_name or last_name:
        return f"{first_name} {last_name}".strip()

    username = getattr(issuer, "username", "").strip()
    if username:
        return username

    return str(issuer)


def _group4(text):
    chunks = [text[i : i + 4] for i in range(0, len(text), 4)]
    return " ".join(chunks)


def _format_hash(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return "Not available"

    if len(text) > 40:
        return f"{text[:16]}...{text[-16:]}"

    return _group4(text)


def _wrap_text(text, font_name, font_size, max_width):
    if text is None:
        return [""]

    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_wrapped_text_object(c, text, x, y, max_width, font_name, font_size, leading):
    text_obj = c.beginText()
    text_obj.setTextOrigin(x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setLeading(leading)

    for line in _wrap_text(text, font_name, font_size, max_width):
        text_obj.textLine(line)

    c.drawText(text_obj)


def _draw_card(c, x, y_top, width, height):
    y = y_top - height
    c.setFillColor(CARD_BG)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.roundRect(x, y, width, height, 7, stroke=1, fill=1)
    return y


def _draw_card_title(c, x, y_top, width, title):
    c.setFillColor(PRIMARY)
    c.setFont(*FONT_SECTION)
    c.drawString(x + CARD_PADDING_X, y_top - CARD_PADDING_Y - 2 * mm, title)
    c.setStrokeColor(SECONDARY)
    c.setLineWidth(0.8)
    line_y = y_top - CARD_PADDING_Y - 3.6 * mm
    c.line(x + CARD_PADDING_X, line_y, x + width - CARD_PADDING_X, line_y)


def _draw_seal(c, center_x, center_y, radius):
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.2)
    c.setFillColor(WHITE)
    c.circle(center_x, center_y, radius, stroke=1, fill=1)

    c.setStrokeColor(SECONDARY)
    c.setLineWidth(0.9)
    c.circle(center_x, center_y, radius - 2.2 * mm, stroke=1, fill=0)

    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(center_x, center_y + 1.6 * mm, "VERIFIED")
    c.setFont("Helvetica", 6)
    c.drawCentredString(center_x, center_y - 1.6 * mm, "CERTCHAIN SEAL")


def draw_header(c, width, y_start):
    header_h = 24 * mm
    y_bottom = y_start - header_h

    c.setFillColor(PRIMARY)
    c.setFont(*FONT_BRAND)
    c.drawString(CONTENT_X, y_start - 7 * mm, "CERTCHAIN")

    c.setFillColor(PRIMARY)
    c.setFont(*FONT_TITLE)
    c.drawString(CONTENT_X, y_start - 14 * mm, "BLOCKCHAIN VERIFICATION RECEIPT")

    c.setFillColor(LABEL)
    c.setFont(*FONT_SUBTITLE)
    c.drawString(CONTENT_X, y_start - 19 * mm, "Tamper-Proof Academic Credential Verification")

    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.0)
    c.line(CONTENT_X, y_bottom, CONTENT_X + width, y_bottom)

    return y_bottom


def draw_status(c, width, y_start):
    status_h = 21 * mm
    y_bottom = _draw_card(c, CONTENT_X, y_start, width, status_h)
    _draw_card_title(c, CONTENT_X, y_start, width, "VERIFICATION STATUS")

    badge_w = 52 * mm
    badge_h = 11.5 * mm
    badge_x = CONTENT_X + width - CARD_PADDING_X - badge_w
    badge_y = y_bottom + (status_h - badge_h) / 2 - 1.2 * mm

    c.setFillColor(STATUS_GREEN_BG)
    c.setStrokeColor(STATUS_GREEN)
    c.setLineWidth(1)
    c.roundRect(badge_x, badge_y, badge_w, badge_h, 5, stroke=1, fill=1)

    c.setFillColor(STATUS_GREEN)
    c.setFont(*FONT_STATUS)
    c.drawCentredString(badge_x + badge_w / 2, badge_y + 3.6 * mm, "AUTHENTIC")

    c.setFillColor(TEXT)
    c.setFont(*FONT_VALUE)
    c.drawString(CONTENT_X + CARD_PADDING_X, y_bottom + status_h / 2 - 1 * mm, "Credential integrity and issuer match validated.")

    seal_center_x = badge_x - 11 * mm
    seal_center_y = y_bottom + status_h / 2 - 1 * mm
    _draw_seal(c, seal_center_x, seal_center_y, 7.2 * mm)

    return y_bottom


def draw_verification_statement(c, width, y_start):
    statement_h = 31 * mm
    y_bottom = _draw_card(c, CONTENT_X, y_start, width, statement_h)
    _draw_card_title(c, CONTENT_X, y_start, width, "VERIFICATION STATEMENT")

    statement = (
        "This document certifies that the academic credential described below has been reviewed, "
        "authenticated, and permanently recorded on the Ethereum blockchain by the issuing institution.\n\n"
        "Any modification to the referenced credential invalidates this verification."
    )

    c.setFillColor(TEXT)
    text_x = CONTENT_X + CARD_PADDING_X
    text_y = y_start - 11.5 * mm
    max_width = min(150 * mm, width - 2 * CARD_PADDING_X)
    _draw_wrapped_text_object(
        c,
        statement,
        text_x,
        text_y,
        max_width,
        font_name="Helvetica",
        font_size=9.7,
        leading=15,
    )

    return y_bottom


def _draw_table_rows(c, x, y_top, table_width, label_width, rows, row_h, value_font=FONT_VALUE, mono_rows=None):
    if mono_rows is None:
        mono_rows = set()

    y = y_top
    for index, (label_text, value_text) in enumerate(rows):
        if index > 0:
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.5)
            c.line(x, y + 1.4 * mm, x + table_width, y + 1.4 * mm)

        c.setFillColor(LABEL)
        c.setFont(*FONT_LABEL)
        c.drawString(x, y - 1.1 * mm, label_text)

        c.setFillColor(TEXT)
        if index in mono_rows:
            c.setFont(*FONT_MONO)
        else:
            c.setFont(*value_font)

        value_x = x + label_width
        max_value_width = table_width - label_width
        font_name, font_size = c._fontname, c._fontsize
        wrapped = _wrap_text(value_text, font_name, font_size, max_value_width)
        c.drawString(value_x, y - 1.1 * mm, wrapped[0] if wrapped else "")
        y -= row_h


def draw_document_details(c, width, y_start, certificate):
    details_h = 44 * mm
    y_bottom = _draw_card(c, CONTENT_X, y_start, width, details_h)
    _draw_card_title(c, CONTENT_X, y_start, width, "VERIFIED DOCUMENT DETAILS")

    rows = [
        ("Holder", getattr(certificate, "student_name", "Not available")),
        ("Certificate Type", getattr(certificate, "course_name", "Not available")),
        ("Institution", _issuer_name(certificate)),
        ("Original Issue Date", _format_date(getattr(certificate, "issue_date", "Not available"))),
        ("Certificate ID", str(getattr(certificate, "certificate_id", "Not available"))),
    ]

    table_x = CONTENT_X + CARD_PADDING_X
    table_y = y_start - 11.2 * mm
    table_w = width - 2 * CARD_PADDING_X
    label_w = 42 * mm
    row_h = 6.8 * mm
    _draw_table_rows(c, table_x, table_y, table_w, label_w, rows, row_h)

    return y_bottom


def draw_blockchain_record(c, width, y_start, certificate, tx_hash):
    block_h = 46 * mm
    y_bottom = _draw_card(c, CONTENT_X, y_start, width, block_h)
    _draw_card_title(c, CONTENT_X, y_start, width, "BLOCKCHAIN RECORD")

    left_w = width * 0.65
    right_w = width - left_w

    left_x = CONTENT_X + CARD_PADDING_X
    left_top = y_start - 11.2 * mm

    tx_value = "Not available"
    if tx_hash and tx_hash != "Blockchain unavailable":
        tx_value = tx_hash

    rows = [
        ("Network", "Ethereum"),
        ("Verification Date", _format_date(timezone.localdate())),
        ("Certificate Fingerprint (SHA-256)", _format_hash(getattr(certificate, "certificate_hash", None))),
        ("Transaction Hash", _format_hash(tx_value)),
    ]

    table_w = left_w - 2 * CARD_PADDING_X
    label_w = 48 * mm
    row_h = 7.2 * mm
    _draw_table_rows(c, left_x, left_top, table_w, label_w, rows, row_h, mono_rows={2, 3})

    # Dedicated QR card on the right column
    qr_card_x = CONTENT_X + left_w + 2 * mm
    qr_card_w = right_w - 4 * mm
    qr_card_h = block_h - 12 * mm
    qr_card_top = y_start - 8 * mm
    qr_card_bottom = _draw_card(c, qr_card_x, qr_card_top, qr_card_w, qr_card_h)

    verify_url = f"/verify/{certificate.certificate_id}/"
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1E3A8A", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_size = min(26 * mm, qr_card_w - 8 * mm)
    qr_x = qr_card_x + (qr_card_w - qr_size) / 2
    qr_y = qr_card_bottom + (qr_card_h - qr_size) / 2 + 3 * mm

    c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)

    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(qr_card_x + qr_card_w / 2, qr_y - 4.2 * mm, "Scan to verify independently")

    return y_bottom


def draw_footer(c, width, y_start):
    footer_h = 26 * mm
    y_bottom = _draw_card(c, CONTENT_X, y_start, width, footer_h)

    # Blue label for IMPORTANT
    label_w = 28 * mm
    label_h = 7 * mm
    label_x = CONTENT_X + CARD_PADDING_X
    label_y = y_start - 9 * mm
    c.setFillColor(PRIMARY)
    c.roundRect(label_x, label_y, label_w, label_h, 2.5, stroke=0, fill=1)

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8.3)
    c.drawCentredString(label_x + label_w / 2, label_y + 2.2 * mm, "IMPORTANT")

    footer_text = (
        "This Blockchain Verification Receipt confirms the authenticity of the referenced academic credential. "
        "It does not replace the original certificate issued by the institution. Powered by CertChain."
    )

    c.setFillColor(TEXT)
    _draw_wrapped_text_object(
        c,
        footer_text,
        CONTENT_X + CARD_PADDING_X,
        y_start - 13 * mm,
        width - 2 * CARD_PADDING_X,
        font_name=FONT_FOOTER[0],
        font_size=FONT_FOOTER[1],
        leading=12,
    )

    return y_bottom


def draw_page_shell(c):
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)


def generate_certificate_pdf(certificate, tx_hash):
    """
    Generate a professional Blockchain Verification Receipt.
    Returns a BytesIO object containing the PDF.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    draw_page_shell(c)

    y = TOP_Y
    y = draw_header(c, CONTENT_WIDTH, y)
    y -= SECTION_GAP

    y = draw_status(c, CONTENT_WIDTH, y)
    y -= SECTION_GAP

    y = draw_verification_statement(c, CONTENT_WIDTH, y)
    y -= SECTION_GAP

    y = draw_document_details(c, CONTENT_WIDTH, y, certificate)
    y -= SECTION_GAP

    y = draw_blockchain_record(c, CONTENT_WIDTH, y, certificate, tx_hash)
    y -= SECTION_GAP

    # Keep footer inside bottom margin.
    min_footer_top = MARGIN_BOTTOM + 26 * mm
    if y < min_footer_top:
        y = min_footer_top

    draw_footer(c, CONTENT_WIDTH, y)

    c.save()
    buffer.seek(0)
    return buffer
