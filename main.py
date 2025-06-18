import streamlit as st
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
from datetime import datetime, timedelta
import re
from io import BytesIO
import traceback

# Configure page
st.set_page_config(
    page_title="Mileage Reimbursement Calculator",
    page_icon="🚗",
    layout="wide"
)

def extract_text_from_pdf(uploaded_file):
    """Extract text from PDF using pdfplumber with PyMuPDF fallback"""
    try:
        # First try with pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text.strip():
            return text
        else:
            raise Exception("No text extracted with pdfplumber")
            
    except Exception as e:
        st.warning(f"pdfplumber failed: {str(e)}. Trying PyMuPDF...")
        
        try:
            # Fallback to PyMuPDF
            uploaded_file.seek(0)  # Reset file pointer
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text() + "\n"
            doc.close()
            
            if text.strip():
                return text
            else:
                raise Exception("No text extracted with PyMuPDF")
                
        except Exception as fallback_error:
            st.error(f"Both PDF extraction methods failed. pdfplumber: {str(e)}, PyMuPDF: {str(fallback_error)}")
            return None

def parse_dates_from_text(text):
    """Extract dates from text using various date patterns"""
    dates = []
    
    # Common date patterns
    date_patterns = [
        r'\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        r'\b(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})\b',  # YYYY/MM/DD
        r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})\b',  # DD Month YYYY
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',  # Month DD, YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                        # Numeric date
                        if len(groups[0]) == 4:  # YYYY/MM/DD format
                            date_obj = datetime.strptime(f"{groups[0]}-{groups[1]}-{groups[2]}", "%Y-%m-%d")
                        else:  # MM/DD/YYYY or DD/MM/YYYY format - assume MM/DD/YYYY for US format
                            date_obj = datetime.strptime(f"{groups[0]}/{groups[1]}/{groups[2]}", "%m/%d/%Y")
                        dates.append(date_obj.date())
                    else:
                        # Month name format
                        month_names = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        if groups[1].lower()[:3] in month_names:
                            month = month_names[groups[1].lower()[:3]]
                            day = int(groups[0])
                            year = int(groups[2])
                            date_obj = datetime(year, month, day)
                            dates.append(date_obj.date())
                        elif groups[0].lower()[:3] in month_names:
                            month = month_names[groups[0].lower()[:3]]
                            day = int(groups[1])
                            year = int(groups[2])
                            date_obj = datetime(year, month, day)
                            dates.append(date_obj.date())
            except ValueError:
                continue
    
    return list(set(dates))  # Remove duplicates

def parse_parking_receipts(text):
    """Parse parking receipt data from text"""
    dates = parse_dates_from_text(text)
    
    # Extract location information
    locations = []
    lines = text.split('\n')
    
    # Look for common parking location indicators
    location_keywords = ['lot', 'garage', 'parking', 'meter', 'street', 'ave', 'avenue', 'blvd', 'boulevard', 'rd', 'road']
    
    for line in lines:
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in location_keywords):
            # Clean up the line and add as potential location
            cleaned_line = re.sub(r'[^\w\s\-\.]', ' ', line).strip()
            if len(cleaned_line) > 3:  # Avoid very short matches
                locations.append(cleaned_line)
    
    # Extract amounts (optional, for future use)
    amounts = []
    amount_pattern = r'\$?(\d+\.?\d*)'
    amount_matches = re.findall(amount_pattern, text)
    for amount in amount_matches:
        try:
            amounts.append(float(amount))
        except ValueError:
            continue
    
    return {
        'dates': dates,
        'locations': locations[:10],  # Limit to first 10 locations found
        'amounts': amounts[:10]  # Limit to first 10 amounts found
    }

def parse_time_report(text):
    """Parse time report data from text"""
    dates = parse_dates_from_text(text)
    
    # Extract client names with better filtering
    clients = []
    lines = text.split('\n')
    
    # Common words to exclude from client names
    exclude_words = {
        'total', 'hours', 'time', 'date', 'project', 'task', 'work', 'report',
        'summary', 'billing', 'invoice', 'amount', 'cost', 'rate', 'page',
        'description', 'notes', 'client', 'company', 'contact', 'phone',
        'email', 'address', 'city', 'state', 'zip', 'country'
    }
    
    for line in lines:
        line = line.strip()
        # Skip lines that are too short, all digits, or contain dates
        if (len(line) < 3 or line.isdigit() or 
            re.match(r'^\d+[/.-]\d+[/.-]\d+', line) or
            re.search(r'\$\d+', line)):  # Skip lines with dollar amounts
            continue
            
        # Look for lines with proper capitalization (likely company names)
        words = line.split()
        potential_client = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if (len(word) > 1 and
                (word.istitle() or word.isupper()) and
                clean_word not in exclude_words and
                not word.isdigit()):
                potential_client.append(word)
        
        if len(potential_client) >= 1:  # At least one proper noun
            client_name = ' '.join(potential_client)
            # Filter out very long strings (likely not client names)
            if 3 <= len(client_name) <= 50 and client_name not in clients:
                clients.append(client_name)
    
    # Sort clients alphabetically and limit to reasonable number
    clients = sorted(list(set(clients)))[:10]
    
    return {
        'dates': dates,
        'clients': clients
    }

def match_dates_to_clients(receipt_dates, time_report_data, client_address_mapping):
    """Match receipt dates with work dates and assign clients"""
    matches = []
    
    for receipt_date in receipt_dates:
        best_matches = []
        
        # Look for exact date matches first
        if receipt_date in time_report_data['dates']:
            for client in time_report_data['clients']:
                if client in client_address_mapping:
                    best_matches.append({
                        'date': receipt_date,
                        'client': client,
                        'address': client_address_mapping[client],
                        'match_type': 'exact'
                    })
        
        # If no exact match, look for dates within ±1 day
        if not best_matches:
            for time_date in time_report_data['dates']:
                date_diff = abs((receipt_date - time_date).days)
                if date_diff <= 1:
                    for client in time_report_data['clients']:
                        if client in client_address_mapping:
                            best_matches.append({
                                'date': receipt_date,
                                'client': client,
                                'address': client_address_mapping[client],
                                'match_type': f'±{date_diff} day(s)'
                            })
        
        # Only add matches if we found valid ones (skip unmatched entries)
        if best_matches:
            matches.extend(best_matches)
    
    return matches

def main():
    st.title("🚗 Mileage Reimbursement Calculator")
    st.markdown("**For Self-Employed Consultants**")
    
    st.markdown("""
    This application helps you process PDF receipts and time reports to calculate tax-free mileage reimbursement.
    
    **How it works:**
    1. Upload your parking receipts (PDF)
    2. Upload your time report (PDF) 
    3. Add your clients and their addresses
    4. Review matched results
    5. Download your summary report
    """)
    
    # Initialize session state
    if 'receipt_data' not in st.session_state:
        st.session_state.receipt_data = None
    if 'time_report_data' not in st.session_state:
        st.session_state.time_report_data = None
    if 'client_address_mapping' not in st.session_state:
        st.session_state.client_address_mapping = {}
    
    # Section 1: Upload Parking Receipts
    st.header("📄 Step 1: Upload Parking Receipts")
    
    uploaded_receipts = st.file_uploader(
        "Choose PDF file(s) containing parking receipts",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload PDF files containing your parking receipts. The system will extract dates and location information."
    )
    
    if uploaded_receipts:
        with st.spinner("Processing parking receipts..."):
            all_receipt_data = {'dates': [], 'locations': [], 'amounts': []}
            
            for receipt_file in uploaded_receipts:
                try:
                    text = extract_text_from_pdf(receipt_file)
                    if text:
                        receipt_data = parse_parking_receipts(text)
                        all_receipt_data['dates'].extend(receipt_data['dates'])
                        all_receipt_data['locations'].extend(receipt_data['locations'])
                        all_receipt_data['amounts'].extend(receipt_data['amounts'])
                        st.success(f"✓ Processed {receipt_file.name}")
                    else:
                        st.error(f"✗ Could not extract text from {receipt_file.name}")
                except Exception as e:
                    st.error(f"✗ Error processing {receipt_file.name}: {str(e)}")
            
            # Remove duplicates and sort
            all_receipt_data['dates'] = sorted(list(set(all_receipt_data['dates'])))
            all_receipt_data['locations'] = list(set(all_receipt_data['locations']))
            
            st.session_state.receipt_data = all_receipt_data
            
        if st.session_state.receipt_data['dates']:
            st.success(f"Found {len(st.session_state.receipt_data['dates'])} parking dates")
            
            with st.expander("View extracted receipt data"):
                st.write("**Dates found:**")
                for date in st.session_state.receipt_data['dates']:
                    st.write(f"- {date.strftime('%B %d, %Y')}")
                
                if st.session_state.receipt_data['locations']:
                    st.write("**Locations found:**")
                    for location in st.session_state.receipt_data['locations'][:5]:
                        st.write(f"- {location}")
    
    # Section 2: Upload Time Report
    st.header("📊 Step 2: Upload Time Report")
    
    uploaded_time_report = st.file_uploader(
        "Choose PDF file containing your time report",
        type=['pdf'],
        help="Upload a PDF file containing your time report with dates and client names."
    )
    
    if uploaded_time_report:
        with st.spinner("Processing time report..."):
            try:
                text = extract_text_from_pdf(uploaded_time_report)
                if text:
                    time_report_data = parse_time_report(text)
                    st.session_state.time_report_data = time_report_data
                    st.success(f"✓ Processed {uploaded_time_report.name}")
                else:
                    st.error("✗ Could not extract text from time report")
            except Exception as e:
                st.error(f"✗ Error processing time report: {str(e)}")
                st.error(f"Details: {traceback.format_exc()}")
        
        if st.session_state.time_report_data and st.session_state.time_report_data['dates']:
            st.success(f"Found {len(st.session_state.time_report_data['dates'])} work dates")
            
            with st.expander("View extracted work dates"):
                st.write("**Work dates found:**")
                for date in sorted(st.session_state.time_report_data['dates']):
                    st.write(f"- {date.strftime('%B %d, %Y')}")
    
    # Section 3: Add Your Clients and Addresses
    if st.session_state.time_report_data:
        st.header("🏢 Step 3: Add Your Clients and Addresses")
        st.write("Enter your client names and their business addresses or parking locations:")
        
        # Initialize client list in session state if not exists
        if 'manual_clients' not in st.session_state:
            st.session_state.manual_clients = []
        
        # Form to add new client
        with st.form("add_client_form"):
            st.subheader("Add a New Client")
            col1, col2 = st.columns(2)
            
            with col1:
                new_client_name = st.text_input(
                    "Client Name:",
                    placeholder="e.g., ABC Corporation",
                    help="Enter the name of your client"
                )
            
            with col2:
                new_client_address = st.text_input(
                    "Business Address/Parking Location:",
                    placeholder="e.g., 123 Main St, Downtown",
                    help="Enter where you typically park when visiting this client"
                )
            
            add_client = st.form_submit_button("Add Client", type="primary")
            
            if add_client and new_client_name.strip() and new_client_address.strip():
                client_entry = {
                    'name': new_client_name.strip(),
                    'address': new_client_address.strip()
                }
                
                # Check if client already exists
                existing_names = [c['name'] for c in st.session_state.manual_clients]
                if client_entry['name'] not in existing_names:
                    st.session_state.manual_clients.append(client_entry)
                    st.success(f"✓ Added {client_entry['name']}")
                else:
                    st.warning(f"Client '{client_entry['name']}' already exists")
        
        # Display current clients
        if st.session_state.manual_clients:
            st.subheader("Your Clients")
            
            for i, client in enumerate(st.session_state.manual_clients):
                col1, col2, col3 = st.columns([3, 4, 1])
                
                with col1:
                    st.write(f"**{client['name']}**")
                
                with col2:
                    st.write(client['address'])
                
                with col3:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.manual_clients.pop(i)
                        st.rerun()
            
            # Update the client-address mapping for the matching algorithm
            st.session_state.client_address_mapping = {
                client['name']: client['address'] 
                for client in st.session_state.manual_clients
            }
            
            # Create a simplified client list for the matching algorithm
            st.session_state.time_report_data['clients'] = [
                client['name'] for client in st.session_state.manual_clients
            ]
        
        else:
            st.info("👆 Add your first client above to get started")
    
    # Section 4: Generate Matches
    if (st.session_state.receipt_data and 
        st.session_state.time_report_data and 
        st.session_state.client_address_mapping):
        
        st.header("🔍 Step 4: Review Matches")
        
        if st.button("Generate Matches", type="primary"):
            with st.spinner("Matching receipt dates with work dates..."):
                matches = match_dates_to_clients(
                    st.session_state.receipt_data['dates'],
                    st.session_state.time_report_data,
                    st.session_state.client_address_mapping
                )
                
                st.session_state.matches = matches
        
        if 'matches' in st.session_state:
            total_receipts = len(st.session_state.receipt_data['dates'])
            matched_receipts = len(st.session_state.matches)
            st.success(f"✓ Generated {matched_receipts} matches from {total_receipts} parking receipts!")
            
            if matched_receipts < total_receipts:
                st.info(f"Note: {total_receipts - matched_receipts} parking receipts had no matching work dates and are excluded from the summary.")
            
            # Display matches in a table
            matches_df = pd.DataFrame(st.session_state.matches)
            
            if not matches_df.empty:
                st.dataframe(
                    matches_df,
                    use_container_width=True,
                    column_config={
                        "date": st.column_config.DateColumn("Date"),
                        "client": "Client",
                        "address": "Address",
                        "match_type": "Match Type"
                    }
                )
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    exact_matches = len([m for m in st.session_state.matches if m['match_type'] == 'exact'])
                    st.metric("Exact Matches", exact_matches)
                
                with col2:
                    near_matches = len([m for m in st.session_state.matches if '±' in m['match_type']])
                    st.metric("Near Matches (±1 day)", near_matches)
                
                with col3:
                    total_receipt_dates = len(st.session_state.receipt_data['dates'])
                    matched_dates = len(st.session_state.matches)
                    unmatched = total_receipt_dates - matched_dates
                    st.metric("Unmatched (Excluded)", unmatched)
                
                # Section 5: Download CSV
                st.header("📥 Step 5: Download Report")
                
                # Prepare CSV data
                csv_data = matches_df.copy()
                csv_data['date'] = csv_data['date'].astype(str)
                
                # Add metadata
                csv_data['generated_on'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                csv_data['total_entries'] = len(csv_data)
                
                # Convert to CSV
                csv_buffer = BytesIO()
                csv_data.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                
                st.download_button(
                    label="📊 Download CSV Report",
                    data=csv_buffer.getvalue(),
                    file_name=f"mileage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    type="primary"
                )
                
                st.info("""
                **Next Steps:**
                1. Review the downloaded CSV file
                2. Calculate mileage distances using your preferred mapping service
                3. Apply current IRS mileage rates for tax deductions
                4. Consult with your tax professional for compliance
                """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Built for self-employed consultants. All data is processed locally and not stored.*")

if __name__ == "__main__":
    main()
