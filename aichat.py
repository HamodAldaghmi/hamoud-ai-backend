import os
import google.generativeai as genai
from flask import Flask, request, jsonify
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions

from flask_cors import CORS

app = Flask(__name__)
# هذا السطر يسمح للـ React يكلم السيرفر من أي مكان
CORS(app, resources={r"/*": {"origins": "*"}})

# --- 1. إعداد Gemini بمفتاحك الجديد ---
API_KEY = "AIzaSyC50y3Dkor20IV3CXnLKIVQDKF_5I3_PPU"
genai.configure(api_key=API_KEY)

# --- 2. حل مشكلة الـ 404: اختيار الموديل المتاح تلقائياً ---
try:
    # الكود هنا بيسأل قوقل: "وش الموديلات اللي أقدر استخدمها؟"
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # بيختار أول موديل شغال (غالباً بيكون gemini-pro أو gemini-1.5-flash)
    model_to_use = available_models[0] if available_models else 'gemini-pro'
    llm_model = genai.GenerativeModel(model_to_use)
    print(f"--- [SUCCESS] Using Model: {model_to_use} ---")
except Exception as e:
    print(f"--- [ERROR] Model selection failed: {e} ---")
    llm_model = genai.GenerativeModel('gemini-pro')

# --- 3. إعداد الذاكرة (ChromaDB) ---
client = chromadb.PersistentClient(path="./my_ai_memory")
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_or_create_collection(name="hamoud_docs", embedding_function=default_ef)


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"status": "error"}), 400
    file = request.files['file']
    try:
        text_content = ""
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages: text_content += page.extract_text()
        chunks = [text_content[i:i + 600] for i in range(0, len(text_content), 600)]
        ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
        collection.add(documents=chunks, ids=ids, metadatas=[{"source": file.filename}] * len(chunks))
        return jsonify({"status": "success", "message": "تم الاستيعاب!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('question', '').strip()
    try:
        # استرجاع 5 نتائج لضمان الدقة
        results = collection.query(query_texts=[user_query], n_results=5)
        context = " ".join(results['documents'][0]) if results['documents'] else ""

        prompt = f"أجب باختصار من النص التالي:\n{context}\nالسؤال: {user_query}"
        response = llm_model.generate_content(prompt)

        return jsonify({"response": response.text})
    except Exception as e:
        if "429" in str(e): return jsonify({"response": "السيرفر مضغوط، انتظر دقيقة."})
        return jsonify({"response": f"حدث خطأ: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)