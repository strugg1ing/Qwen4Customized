## 下载qwen2-7b-instruct-q5_k_m.gguf到本地 

```
链接: https://pan.baidu.com/s/1HBfeneVZLh4eazFoi0FrNw?pwd=y6rg 提取码: y6rg 
```
## 配置环境
```pip install llama-cpp-python
   pip install openai
   pip install uvicorn
   pip install starlette
   pip install fastapi
   pip install sse_starlette
   pip install starlette_context
   pip install pydantic_settings
   pip install llama-cpp-python
```
## 启动Qwen2大模型
#### n_ctx=20480代表单次回话最大20480个Token数量
    python -m llama_cpp.server \
    --host 0.0.0.0 \
    --model ./qwen2-7b-instruct-q5_k_m.gguf \
    --n_ctx 20480
## 启动后端
    python testPDF.py
