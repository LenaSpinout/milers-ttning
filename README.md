# Mileage Reimbursement Calculator

A Streamlit web application for self-employed consultants to process PDF receipts and time reports, automatically match expenses to clients, and generate tax-compliant mileage reimbursement summaries.

## Features

- **PDF Processing**: Upload and parse parking receipts and time reports using advanced PDF extraction
- **Automatic Matching**: Intelligently match receipt dates with work dates by client
- **Client Management**: Link clients to business addresses or parking locations
- **Export Functionality**: Generate CSV reports for tax compliance
- **User-Friendly Interface**: Clean, step-by-step workflow with progress indicators

## Tech Stack

- **Backend/Frontend**: Streamlit
- **PDF Processing**: pdfplumber and PyMuPDF (fitz)
- **Data Handling**: pandas
- **File Processing**: Native Python libraries

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install streamlit pandas pdfplumber PyMuPDF
   ```

## Usage

1. Start the application:
   ```bash
   streamlit run main.py --server.port 5000
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Follow the step-by-step process:
   - **Step 1**: Upload PDF parking receipts
   - **Step 2**: Upload PDF time report
   - **Step 3**: Link clients to addresses
   - **Step 4**: Review generated matches
   - **Step 5**: Download CSV report

## How It Works

### PDF Processing
The application uses two PDF extraction libraries:
- **pdfplumber**: Primary extraction method for most PDFs
- **PyMuPDF**: Fallback method for complex or image-based PDFs

### Date Matching Algorithm
- Extracts dates from both receipts and time reports
- Performs exact date matching first
- Falls back to ±1 day matching for near dates
- Flags unmatched entries for manual review

### Data Export
Generated CSV files include:
- Date of parking/receipt
- Matched client name
- Business address/location
- Match confidence level
- Generation timestamp

## File Structure

