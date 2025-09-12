FROM docker.m.daocloud.io/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 创建非特权用户
RUN useradd --create-home --shell /bin/bash app

# 复制requirements.txt并安装依赖（利用Docker层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录并设置权限
RUN mkdir -p logs && \
    chown -R app:app /app

# 暴露端口（虽然此应用不直接监听端口，但保留以备将来扩展）
EXPOSE 5000

# 切换到非特权用户
USER app

# 设置入口点
ENTRYPOINT ["python", "main.py"]
