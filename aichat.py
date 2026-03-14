# ==============================
#      aichat.py - Back-end
#      Ready for Render Deploy
# ==============================
import os
import uuid
import PyPDF2
from flask import Flask, request, jsonify
from flask_cors import CORS
from chromadb import Client, Settings
import google.generativeai as genai

app = Flask(__name__)

# ==============================
# 🔥 [أهم خطوة] حل CORS الجوهري
# هذا السطر يفتح الأبواب لـ Vercel ولجوالك ولأي مكان
# ==============================
CORS(app)

# ==============================
# 🔑 إعدادات Gemini و ChromaDB
# ==============================
# تأكد إن الـ API Key حقك صح
genai.configure(api_key="ضع_هنا_API_KEY_الخاص_بك_من_GEMINI")
model = genai.GenerativeModel('gemini-1.5-flash')

# ChromaDB Client
chroma_client = Client(Settings(allow_reset=True))


# Create a unique collection for each PDF
def get_pdf_collection(pdf_id):
    return chroma_client.get_or_create_collection(name=f"pdf_{pdf_id}")


# ==============================
# 📄 دوال معالجة الـ PDF
# ==============================
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def split_text_into_chunks(text, chunk_size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks


# ==============================
# 🛡️ النقاط الطرفية (Endpoints)
# ==============================
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            # Generate a unique ID for this PDF
            pdf_id = str(uuid.uuid4())
            text = extract_text_from_pdf(file)
            chunks = split_text_into_chunks(text)

            # Use ChromaDB for storage
            collection = get_pdf_collection(pdf_id)
            ids = [f"id_{i}" for i in range(len(chunks))]
            collection.add(documents=chunks, ids=ids)

            # Return pdf_id to the frontend
            return jsonify({"message": "تم الاستيعاب بنجاح! ✅", "pdf_id": pdf_id}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')
    pdf_id = data.get('pdf_id')

    if not question or not pdf_id:
        return jsonify({"error": "Question or PDF ID missing"}), 400

    try:
        # 1. Retrieve the most relevant chunks from ChromaDB
        collection = get_pdf_collection(pdf_id)
        results = collection.query(query_texts=[question], n_results=3)
        relevant_chunks = results['documents'][0]

        # 2. Construct the prompt for Gemini
        context = "\n".join(relevant_chunks)
        prompt = f"""
        استناداً إلى السياق التالي من ملف PDF المرفوع:
        ---
        {context}
        ---
        السؤال: {question}
        ---
        يرجى تقديم إجابة دقيقة وبناءة بناءً على هذا السياق فقط. إذا لم تكن الإجابة موجودة، قل "لا يمكنني العثور على الإجابة في هذا المستند".
        """

        # 3. Get the answer from Gemini
        response = model.generate_content(prompt)
        answer = response.text

        return jsonify({"message": answer}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================
# ✨ نقطة النهاية لفحص الصحة (Health Check)
# جرب تفتح هذا الرابط: / (بدون أي شي بعده)
# ==============================
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Server is Live 🚀", "message": "Backend for HAMOUD AI"}), 200


# ==============================
# ⚙️ تشغيل السيرفر
# ==============================
if __name__ == '__main__':
    # تأكد إن البورت مرفوع لـ 10000 ليتوافق مع Render
    app.run(host='0.0.0.0', port=10000)