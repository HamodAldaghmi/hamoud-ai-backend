from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from textblob import TextBlob

app = Flask(__name__)
CORS(app)


# 1. إعداد قاعدة البيانات والجدول
def init_db():
    conn = sqlite3.connect('data_smart.db')
    cursor = conn.cursor()
    # تأكد من كتابة الاستعلام بشكل صحيح ومنظم
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS entries
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       content
                       TEXT,
                       category
                       TEXT
                   )
                   ''')
    conn.commit()
    conn.close()


# 2. منطق التحليل الذكي (الذي يجمع بين القواعد والذكاء الاصطناعي)
def classify_logic(text):
    if not text:
        return "نص فارغ"

    text_lower = text.lower().strip()

    # قائمة الكلمات المفتاحية (Rule-based Classification)
    tech_keywords = ['ريناد', 'عطل', 'خطأ', 'تعليق', 'خربان', 'error', 'bug', 'slow', 'بطيء']
    finance_keywords = ['سعر', 'فلوس', 'دفع', 'كم', 'اشتراك', 'price', 'payment', 'cost']
    welcome_keywords = ['هلا', 'مرحبا', 'سلام', 'شكرا', 'hi', 'hello', 'thanks']

    # فحص الكلمات المفتاحية أولاً (Rule-based)
    if any(word in text_lower for word in tech_keywords):
        return "دعم بوسسااات 🛠️"
    elif any(word in text_lower for word in finance_keywords):
        return "استفسار مالي 💰"
    elif any(word in text_lower for word in welcome_keywords):
        return "تواصل اجتماعي 👋"

    # إذا لم يجد كلمات، يستخدم تحليل المشاعر (Sentiment Analysis)
    try:
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0:
            return "إيجابي / عام 😊"
        elif analysis.sentiment.polarity < 0:
            return "سلبي / عام 😡"
        else:
            return "عام / محايد 📝"
    except:
        return "عام / محايد 📝"


# 3. استقبال البيانات من React وحفظها
@app.route('/add_data', methods=['POST'])
def add_data():
    try:
        data = request.json
        user_text = data.get('content', '').strip()

        if not user_text:
            return jsonify({"status": "error", "message": "لم يتم إرسال نص!"}), 400

        # تنفيذ عملية التحليل
        category_result = classify_logic(user_text)

        # الحفظ في SQLite
        conn = sqlite3.connect('data_smart.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO entries (content, category) VALUES (?, ?)", (user_text, category_result))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "category": category_result,
            "message": "تم الحفظ والتحليل بنجاح"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    init_db()  # إنشاء القاعدة عند التشغيل
    print("------------------------------------------")
    print("سيرفر بايثون المطور شغال الآن على البورت 5000")
    print("------------------------------------------")
    app.run(debug=True, port=5000)