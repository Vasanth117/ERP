"""Minimal PDF generation for examination hall tickets."""


def build_hall_ticket_pdf(
    *,
    institution_name: str,
    ticket_number: str,
    student_name: str,
    roll_number: str,
    session_title: str,
    subjects: list[str],
    verification_code: str,
) -> bytes:
    lines = [
        f"Institution: {institution_name}",
        f"Hall Ticket: {ticket_number}",
        f"Student: {student_name}",
        f"Roll No: {roll_number}",
        f"Session: {session_title}",
        "Subjects:",
        *subjects,
        f"Verification: {verification_code}",
    ]
    content_lines = ["BT /F1 11 Tf 50 750 Td"]
    for idx, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        dy = 16 if idx == 0 else -16
        prefix = f"{dy} 0 Td " if idx > 0 else ""
        content_lines.append(f"{prefix}({escaped}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines)
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n",
        f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode()
        + stream_bytes
        + b"\nendstream\nendobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj
    xref_start = len(pdf)
    pdf += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode()
    return pdf