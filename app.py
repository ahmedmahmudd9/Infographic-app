import streamlit as st
import google.generativeai as genai
import json
import re
from xhtml2pdf import pisa
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Medical Infographic Generator", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

# --- SIDEBAR: API KEY & CONFIG ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Google Gemini API Key", type="password", help="Enter your AI Studio API Key.")
    st.markdown("---")
    st.markdown("""
    **Pro Tip:** For permanent API key storage in Streamlit, create a `.streamlit/secrets.toml` file in your project folder and add:
    `GEMINI_API_KEY = "your_key_here"`
    """)

# --- HELPER FUNCTIONS ---

def extract_json_from_text(text):
    """Extracts JSON block from standard LLM markdown output."""
    match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Fallback if no markdown block is used
    return json.loads(text)

def generate_medical_images(prompts):
    """
    Placeholder for Image Generation API.
    Replace this logic with an active Vertex AI Imagen or DALL-E API call.
    Currently returns a clean, blue placeholder image URL to fit the aesthetic.
    """
    image_urls = []
    for _ in prompts:
        # Using a reliable placeholder service for a minimal blue and white aesthetic
        image_urls.append("https://placehold.co/400x300/0ea5e9/ffffff?text=Medical+Illustration")
    return image_urls

def generate_html_template(data, image_urls):
    """
    Compiles data into an xhtml2pdf-compatible HTML string.
    Uses a strict, minimal blue and white palette for clean, high-yield visual review.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @page {{ size: A4 portrait; margin: 2cm; }}
        body {{ font-family: Helvetica, sans-serif; color: #1e293b; line-height: 1.4; }}
        h1 {{ color: #0284c7; text-align: center; border-bottom: 2px solid #e0f2fe; padding-bottom: 10px; font-size: 24px; }}
        h2 {{ color: #0ea5e9; font-size: 16px; margin-top: 20px; }}
        .concept-box {{ background-color: #f8fafc; border-left: 4px solid #0ea5e9; padding: 12px; margin-bottom: 15px; }}
        .concept-title {{ font-weight: bold; color: #0369a1; font-size: 14px; margin-bottom: 5px; }}
        .concept-desc {{ font-size: 12px; margin: 0; }}
        .image-container {{ text-align: center; margin-top: 20px; }}
        .medical-img {{ width: 250px; border: 1px solid #cbd5e1; margin: 10px; }}
    </style>
    </head>
    <body>
        <h1>Ultra-Compressed Medical Review</h1>
    """
    
    # Inject concepts
    for concept in data.get("concepts", []):
        html_content += f"""
        <div class="concept-box">
            <div class="concept-title">{concept['title']}</div>
            <div class="concept-desc">{concept['description']}</div>
        </div>
        """
    
    # Inject images
    if image_urls:
        html_content += "<div class='image-container'>"
        for url in image_urls:
            html_content += f"<img src='{url}' class='medical-img' />"
        html_content += "</div>"

    html_content += "</body></html>"
    return html_content

def convert_html_to_pdf(source_html):
    """Converts HTML to PDF using xhtml2pdf in-memory."""
    result_file = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(source_html), dest=result_file)
    if pisa_status.err:
        raise Exception("PDF compilation failed.")
    return result_file.getvalue()

# --- MAIN APP UI ---

st.title("🩺 Medical Infographic Generator")
st.write("Upload a textbook chapter (.txt) to convert it into an ultra-compressed, high-yield PDF.")

uploaded_file = st.file_uploader("Upload Chapter Text File", type=["txt"])

if uploaded_file and api_key:
    if st.button("Generate Infographic PDF", type="primary"):
        with st.spinner("Processing chapter and extracting high-yield facts..."):
            try:
                # 1. Read File
                text_content = uploaded_file.read().decode("utf-8")
                
                # 2. Configure Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro')
                
                prompt = f"""
                You are a medical data extraction engine. Read the following textbook text and extract 10 to 15 ultra-compressed, high-yield core concepts, mechanisms, and exam-relevant facts.
                
                You must output ONLY a raw JSON object with the following structure:
                {{
                  "concepts": [
                    {{"title": "Concept Name", "description": "1-2 concise sentences."}}
                  ],
                  "image_prompts": [
                    "Prompt 1 for a clean, isolated medical illustration on a white background",
                    "Prompt 2 for a clean, isolated medical illustration on a white background"
                  ]
                }}
                
                Text to compress:
                {text_content}
                """
                
                # 3. Text Compression
                response = model.generate_content(prompt)
                extracted_data = extract_json_from_text(response.text)
                
                st.success("Text compressed successfully!")
                
                # 4. Image Generation Workflow
                with st.spinner("Generating medical illustrations..."):
                    image_urls = generate_medical_images(extracted_data.get("image_prompts", []))
                
                # 5. HTML Compilation
                with st.spinner("Compiling layout..."):
                    html_layout = generate_html_template(extracted_data, image_urls)
                
                # 6. PDF Conversion
                with st.spinner("Rendering vector PDF..."):
                    pdf_bytes = convert_html_to_pdf(html_layout)
                    st.session_state.pdf_data = pdf_bytes
                    
                st.success("Infographic generated successfully! Ready for download.")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

elif not api_key:
    st.info("Please enter your Gemini API Key in the sidebar to begin.")

# --- DOWNLOAD BUTTON ---
# Placed outside the button block so it persists after Streamlit reruns
if st.session_state.pdf_data:
    st.download_button(
        label="⬇️ Download Infographic PDF",
        data=st.session_state.pdf_data,
        file_name="high_yield_infographic.pdf",
        mime="application/pdf"
    )
