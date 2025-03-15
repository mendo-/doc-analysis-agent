"""Test PDF file generation for integration tests."""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def create_test_pdfs() -> dict[str, Path]:
    """Create test PDF files with known content and relationships.

    Returns:
        dict[str, Path]: Dictionary mapping PDF names to their file paths
    """
    data_dir = Path(__file__).parent / "pdfs"
    data_dir.mkdir(exist_ok=True)

    # Contract PDF with specific terms
    contract_path = data_dir / "contract.pdf"
    c = canvas.Canvas(str(contract_path), pagesize=letter)
    c.drawString(100, 750, "SERVICE AGREEMENT")
    c.drawString(100, 700, "Between: TechCorp Inc. and DataCo Ltd.")
    c.drawString(100, 650, "Value: $50,000")
    c.drawString(100, 600, "Duration: 12 months")
    c.drawString(100, 550, "Start Date: 2024-01-01")
    c.drawString(100, 500, "Services: AI Model Development")
    c.save()

    # Amendment PDF referencing the contract
    amendment_path = data_dir / "amendment.pdf"
    c = canvas.Canvas(str(amendment_path), pagesize=letter)
    c.drawString(100, 750, "CONTRACT AMENDMENT")
    c.drawString(100, 700, "Reference: Service Agreement dated 2024-01-01")
    c.drawString(100, 650, "Changes:")
    c.drawString(120, 600, "1. Contract value increased to $75,000")
    c.drawString(120, 550, "2. Duration extended to 18 months")
    c.drawString(120, 500, "3. Additional service: Model Deployment")
    c.save()

    # Progress report referencing both documents
    report_path = data_dir / "report.pdf"
    c = canvas.Canvas(str(report_path), pagesize=letter)
    c.drawString(100, 750, "PROJECT STATUS REPORT")
    c.drawString(100, 700, "Re: AI Model Development Project")
    c.drawString(100, 650, "Contract: Service Agreement (2024-01-01)")
    c.drawString(100, 600, "Amendment: Contract Amendment (2024-03-15)")
    c.drawString(100, 550, "Progress:")
    c.drawString(120, 500, "- Model development 60% complete")
    c.drawString(120, 450, "- Team size increased to handle deployment")
    c.drawString(120, 400, "- Current spend: $45,000")
    c.save()

    # Unrelated document for testing
    other_path = data_dir / "other.pdf"
    c = canvas.Canvas(str(other_path), pagesize=letter)
    c.drawString(100, 750, "MEETING MINUTES")
    c.drawString(100, 700, "Topic: Office Renovation")
    c.drawString(100, 650, "Date: 2024-03-20")
    c.drawString(100, 600, "Budget: $25,000")
    c.save()

    return {
        "contract": contract_path,
        "amendment": amendment_path,
        "report": report_path,
        "other": other_path,
    }
