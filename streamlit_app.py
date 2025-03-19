import base64
import io
import os
import zipfile

import requests
import streamlit as st


class MissingEnvironmentVariable(Exception):
    pass


def get_image_download_link(img: bytes, filename: str, text: str) -> str:
    img_str = base64.b64encode(img).decode()
    html_code = f'''
    
    <a href="data:file/txt;base64,{img_str}" download="{filename}">
        <figure>
            <img src="data:file/txt;base64,{img_str}" alt="{filename}"/>
            <figcaption>{filename}</figcaption>
        </figure>
    </a>
    
    '''
    return html_code


# check env
BACKEND_ROOT_URL = os.getenv("BACKEND_ROOT_URL", "http://localhost:8080")
if not BACKEND_ROOT_URL:
    print("BACKEND_ROOT_URL env var missing")
    exit(1)

server_conversion_url = f"{BACKEND_ROOT_URL}/pdf/metamorphose"

# A minimal layout
st.title("PDF Metamorphose")
st.markdown("""
<style>
    figure {
        display: inline-block;
        /*border: 5px dotted gray;*/
        margin: 20px;
        padding: 5px;
    }
    figure img {
        vertical-align: top;
    }
    figure figcaption {
        /*border: 5px dotted blue;*/
        text-align: center;
        color: gray;
    }
<style>
""", unsafe_allow_html=True
)
col1, col2 = st.columns(2)
with col1:
    img_format = st.selectbox(
        "Convert PDF to image format ..",
        ("JPEG", "PNG"),
    )
with col2:
    uploaded_pdf = st.file_uploader('Upload a PDF file', type="pdf")
    upload_pdf_btn = st.button("Upload PDF")

# logic
if upload_pdf_btn:
    if uploaded_pdf is not None:
        file = {"pdf_file": (uploaded_pdf.name, uploaded_pdf.getvalue(), uploaded_pdf.type)}
        response = requests.post(server_conversion_url, files=file,
                                 params={"format": img_format.lower()})

        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content), "r") as z:
            images = z.namelist()
            for col, name in zip(st.columns(len(images)), images):
                # st.image(z.read(name), caption=name)
                with col:
                    st.markdown(
                        get_image_download_link(z.read(name), name, 'Download ' + name),
                        unsafe_allow_html=True)
    else:
        st.error("Select a PDF file")
