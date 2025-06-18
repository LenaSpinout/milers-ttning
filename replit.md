# Mileage Reimbursement Calculator

## Overview

This is a Streamlit web application designed for self-employed consultants to process PDF receipts and time reports, automatically match expenses to clients, and generate tax-compliant mileage reimbursement summaries. The application provides a user-friendly interface for uploading documents, managing client information, and exporting reports.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit (Python-based web framework)
- **Design Pattern**: Single-page application with step-by-step workflow
- **User Interface**: Clean, progressive disclosure interface with file upload capabilities
- **Configuration**: Custom Streamlit configuration for deployment on port 5000

### Backend Architecture
- **Runtime**: Python 3.11
- **Processing Engine**: Pandas for data manipulation and analysis
- **PDF Processing**: Dual-library approach using pdfplumber as primary and PyMuPDF (fitz) as fallback
- **File Handling**: Native Python I/O operations with BytesIO for memory-efficient processing

## Key Components

### PDF Processing Engine
- **Primary Library**: pdfplumber - optimized for text extraction from standard PDFs
- **Fallback Library**: PyMuPDF (fitz) - handles complex or image-based PDFs when pdfplumber fails
- **Error Handling**: Graceful degradation with automatic fallback mechanism
- **Text Extraction**: Multi-page processing with concatenated output

### Data Processing Pipeline
- **Input Processing**: Handles parking receipts and time reports via file upload
- **Matching Algorithm**: Intelligent date-based matching between receipts and work periods
- **Client Management**: Links clients to business addresses or parking locations
- **Export Generation**: CSV output for tax compliance reporting

### User Interface Components
- **File Upload Interface**: Multi-file PDF upload with progress indicators
- **Step-by-Step Workflow**: Five-stage process from upload to export
- **Data Review Tables**: Interactive tables for reviewing matches and client linkages
- **Export Controls**: One-click CSV download functionality

## Data Flow

1. **PDF Upload**: Users upload parking receipts and time reports
2. **Text Extraction**: Dual-library PDF processing extracts text content
3. **Data Parsing**: Extracted text is parsed for dates, amounts, and client information
4. **Client Mapping**: Users link clients to addresses/locations
5. **Automatic Matching**: System matches receipts to work dates by client
6. **Review & Validation**: Users review generated matches
7. **Export Generation**: System generates CSV reports for tax compliance

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework and UI components
- **pandas**: Data manipulation and analysis
- **pdfplumber**: Primary PDF text extraction
- **PyMuPDF (fitz)**: Fallback PDF processing for complex documents

### System Dependencies (Nix packages)
- **freetype**: Font rendering support
- **mupdf**: PDF processing backend
- **libjpeg_turbo**: Image processing optimization
- **openjpeg**: JPEG 2000 support
- **harfbuzz**: Text shaping engine
- **jbig2dec**: JBIG2 decoder for PDFs

## Deployment Strategy

### Platform
- **Target**: Replit autoscale deployment
- **Runtime Environment**: Nix-based with Python 3.11
- **Port Configuration**: Application runs on port 5000

### Deployment Configuration
- **Process Management**: Streamlit server with headless configuration
- **Scaling**: Autoscale deployment target for demand-based scaling
- **Dependency Management**: UV package manager for Python dependencies

### Build Process
- **Package Installation**: Automated UV-based dependency installation
- **Service Startup**: Streamlit server with custom port binding
- **Health Checks**: Port-based readiness checks (waitForPort: 5000)

## Changelog
- June 17, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.