import streamlit as st
import whisper
import tempfile
import librosa
import os
from io import BytesIO
from docx import Document

# Título de la app
st.title("Transcriptor de Audio a Texto con Whisper")

# Carga del modelo solo una vez
@st.cache_resource
def load_model():
    return whisper.load_model("small")

model = load_model()

# Subida de archivo
uploaded_file = st.file_uploader("Sube un archivo de audio (.wav o .mp4)", type=["wav", "mp4"])

if uploaded_file is not None:
    st.success("Archivo recibido. Procesando...")

    # Guardar temporalmente el archivo
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name[-4:]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Convertir y cargar el audio con librosa
    try:
        audio, sr = librosa.load(tmp_path, sr=16000, mono=True)
        st.write("Audio cargado correctamente.")
    except Exception as e:
        st.error(f"Error al procesar el audio: {e}")
        os.remove(tmp_path)
        st.stop()

    # Transcribir con Whisper
    st.info("Transcribiendo, espera un momento...")
    try:
        result = model.transcribe(audio)
        transcript = result["text"]
        st.subheader("Transcripción:")
        st.write(transcript)

        # Descargar como TXT
        txt_bytes = transcript.encode("utf-8")
        st.download_button("📄 Descargar como .txt", data=txt_bytes, file_name="transcripcion.txt", mime="text/plain")

        # Descargar como DOCX
        doc = Document()
        doc.add_heading("Transcripción de Audio", level=1)
        doc.add_paragraph(transcript)
        docx_io = BytesIO()
        doc.save(docx_io)
        docx_io.seek(0)
        st.download_button("📝 Descargar como .docx", data=docx_io, file_name="transcripcion.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    except Exception as e:
        st.error(f"Error durante la transcripción: {e}")
    finally:
        os.remove(tmp_path)
