from flask import Flask, request, jsonify, render_template, stream_with_context, Response
from openai import OpenAI

app = Flask(__name__, template_folder='/var/www/html')

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="not-needed")

history = [{"role": "system", "content": "你是中山大学人事处智能助理。Your answers are always easy to understand, correct, useful and the content is very concise"}]

@app.route('/')
def index():
    return render_template('index.html')

# 处理聊天消息，支持流式返回
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # 获取前端发送的用户消息 (GET 请求中数据来自 query 参数)
    if request.method == 'GET':
        user_message = request.args.get("message", "")
    else:
        data = request.get_json()
        user_message = data.get("message", "")

    # 添加用户消息到对话历史
    history.append({"role": "user", "content": user_message})

    # 调用 OpenAI API 生成回复 (流式支持可加入)
    completion = client.chat.completions.create(
        model="local-model",
        messages=history,
        temperature=0.7,
        stream=True,
    )

    # 初始化机器人回复
    def generate():
        new_message = {"role": "assistant", "content": ""}
        for chunk in completion:
            if chunk.choices[0].delta.content:
                # 每个 chunk 的内容
                yield f"data: {chunk.choices[0].delta.content}\n\n"
                new_message["content"] += chunk.choices[0].delta.content

        # 将完整的回复添加到对话历史中
        history.append(new_message)

    # 使用流式响应返回数据
    return app.response_class(generate(), content_type='text/event-stream')
if __name__ == '__main__':
    app.run(debug=True, port=5000)
