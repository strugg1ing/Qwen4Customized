from flask import Flask, request, jsonify, render_template, stream_with_context, Response
from openai import OpenAI
from PyPDF2 import PdfReader
import os
import uuid
import logging
from flask_cors import CORS

app = Flask(__name__, template_folder='/var/www/html')
CORS(app)  # 允许跨域请求

# 配置日志
logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="not-needed")

# 初始化对话历史
history = [{
    "role": "system",
    "content": "你是中山大学人事处智能助理,你的回复是准确、精简高效的"
}]
PDF_message=""
@app.route('/')
def index():
    return render_template('index.html')

# 上传文件并保存
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    if file:
        # 检查文件类型
        if not file.filename.endswith('.pdf'):
            logging.error("Invalid file type")
            return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

        # 使用 uuid4 来生成唯一文件名，防止文件名冲突
        unique_filename = str(uuid.uuid4()) + "_" + file.filename
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        logging.info(f"File uploaded successfully: {unique_filename}")
        return jsonify({"fileName": unique_filename})

# 处理PDF文件
@app.route('/process-file', methods=['GET'])
def process_file():
    filename = request.args.get('filename')
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        logging.error("File not found: %s", filename)
        return jsonify({"error": "File not found"}), 404

    try:
        # 从PDF提取文本
        text = extract_text_from_pdf(file_path)
        if not text:
            logging.error("Failed to extract text from PDF")
            return jsonify({"error": "Failed to extract text from PDF"}), 400
        
        # 将提取的文本存入会话中，方便后续使用
        history.append({"role": "assistant", "content": text})  # 将提取的内容添加到对话历史中

        return jsonify({"output": text})
    
    except Exception as e:
        logging.exception("An error occurred while processing the file")
        return jsonify({"error": str(e)}), 500

def extract_text_from_pdf(pdf_file_path):
    global PDF_message
    """ 从PDF文件中提取文本 """
    try:
        with open(pdf_file_path, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ''
            PDF_message = PDF_message + text
            return text
    except Exception as e:
        raise Exception(f"Error reading PDF file: {e}")

# 处理聊天消息，支持流式返回
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global PDF_message
    user_message =""
    if request.method == 'GET':
        user_message = request.args.get("message", "") + user_message
    else:
        data = request.get_json()
        user_message = data.get("message", "") +  user_message

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    user_message = PDF_message + "\n"+ user_message
    print(user_message)
    # 添加用户消息到对话历史
    history.append({"role": "user", "content": user_message})

    # 调用 OpenAI API 生成回复 (支持流式输出)
    try:
        completion = client.chat.completions.create(
            model="local-model",
            messages=history,
            temperature=0.7,
            stream=True,  # 启用流式输出
        )
    except Exception as e:
        logging.exception("Error during model call")
        return jsonify({"error": f"Error during model call: {e}"}), 500

    # 初始化机器人回复，流式返回数据
    def generate():
        new_message = {"role": "assistant", "content": ""}
        try:
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
                    new_message["content"] += chunk.choices[0].delta.content
            # 将完整的回复添加到对话历史中
            history.append(new_message)
        except Exception as e:
            yield f"data: Error: {e}\n\n"
    PDF_message = ""
    # 使用流式响应返回数据
    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
