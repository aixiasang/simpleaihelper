"""
simpleaihelper 包的使用示例与流式接口测试
"""

import os
import sys
from simpleaihelper import AI

def get_silicon_client():
    """获取硅谷的客户端"""
    api_key = os.environ.get("SILICON_API_KEY")
    if not api_key:
        raise ValueError("请设置SILICON_API_KEY环境变量")
    return AI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1",
        default_model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    )

def get_doubao_client():
    """获取豆包客户端"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    return AI(
        api_key=api_key,
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        default_model="deepseek-r1-distill-qwen-32b-250120"
    )


def test_stream_ask(client):
    """测试普通流式输出接口"""
    print("\n===== 测试 stream_ask 接口 =====")
    prompt = "简单介绍一下什么是并发编程"
    print(f"提问: {prompt}\n")
    
    print("开始流式输出:")
    # 直接输出每个流式块，实现打字机效果
    for text_chunk in client.stream_ask(prompt):
        print(text_chunk, end="", flush=True)
    print("\n\n流式输出完成")

def test_stream_think(client):
    """测试流式思考接口"""
    print("\n===== 测试 stream_think 接口 =====")
    prompt = "解释一下ABA问题以及如何在无锁数据结构中解决它"
    print(f"提问: {prompt}\n")
    
    print("开始流式思考输出:")
    
    # 跟踪当前类型
    current_type = None
    
    # 直接处理每个流式块
    for chunk in client.stream_think(prompt):
        chunk_type = chunk["type"]
        content = chunk["content"]
        
        # 处理状态转换
        if chunk_type == "transition":
            print("\n----- 开始回答 -----\n")
            current_type = "answer"
            continue
        
        # 首次切换类型时显示标签
        if current_type != chunk_type:
            if chunk_type == "reasoning":
                print("\n[思考]", end=" ")
            elif chunk_type == "answer":
                print("\n[回答]", end=" ")
            current_type = chunk_type
        
        # 直接输出内容，实现打字机效果
        print(content, end="", flush=True)
    
    print("\n\n流式思考完成")

def test_think(client):
    """测试完整思考结果接口"""
    print("\n===== 测试 think 接口 =====")
    prompt = "解释一下什么是读写锁以及它们的使用场景"
    print(f"提问: {prompt}\n")
    
    print("获取完整思考结果...\n")
    result = client.think(prompt)
    
    print("思考过程:")
    print(result['reasoning'])
    
    print("\n最终答案:")
    print(result['answer'])

def test_thinking_display(client):
    """测试优雅的思考显示接口"""
    print("\n===== 测试 thinking_display 接口 =====")
    prompt = "讨论一下无锁队列的实现方法和挑战"
    print(f"提问: {prompt}\n")
    
    print("使用优雅API获取结果...\n")
    result = client.thinking_display(prompt)
    
    print(f"思考过程 ({len(result['reasoning'])} 字符):")
    # 如果思考过程太长，只显示前300个字符
    if len(result['reasoning']) > 300:
        print(result['reasoning'][:300] + "...")
    else:
        print(result['reasoning'])
    
    print(f"\n最终答案 ({len(result['answer'])} 字符):")
    print(result['answer'])

def test_session_stream(client):
    """测试会话流式接口"""
    print("\n===== 测试会话流式接口 =====")
    
    # 创建会话
    system_prompt = "你是一位并发编程专家，精通各种线程安全和无锁数据结构的实现。"
    session = client.session(system_prompt=system_prompt)
    
    # 第一个问题
    prompt1 = "什么是内存屏障，它在并发编程中的作用是什么？"
    print(f"会话问题1: {prompt1}\n")
    
    print("会话流式思考输出:")
    
    # 跟踪当前类型
    current_type = None
    
    # 直接处理每个流式块
    for chunk in session.stream_think(prompt1):
        chunk_type = chunk["type"]
        content = chunk["content"]
        
        # 处理状态转换
        if chunk_type == "transition":
            print("\n----- 开始回答 -----\n")
            current_type = "answer"
            continue
        
        # 首次切换类型时显示标签
        if current_type != chunk_type:
            if chunk_type == "reasoning":
                print("\n[思考]", end=" ")
            elif chunk_type == "answer":
                print("\n[回答]", end=" ")
            current_type = chunk_type
        
        # 直接输出内容
        print(content, end="", flush=True)
    
    # 第二个问题 - 维持会话上下文
    prompt2 = "基于你上面解释的内存屏障，它如何帮助解决ABA问题？"
    print(f"\n\n会话问题2: {prompt2}\n")
    
    # 使用thinking_display获取结果
    result = session.thinking_display(prompt2)
    
    print("思考过程:")
    print(result['reasoning'][:300] + "..." if len(result['reasoning']) > 300 else result['reasoning'])
    
    print("\n最终答案:")
    print(result['answer'])
    
    # 显示会话历史
    print("\n会话历史:")
    for msg in session.get_history():
        role = msg['role']
        content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        print(f"- {role}: {content}")
    
    return session

def test_json_api(client):
    """测试JSON格式响应接口"""
    print("\n===== 测试 ask_json 接口 =====")
    prompt = "列出5种常见的并发模式及其简要描述。以JSON格式返回，包含name和description字段"
    print(f"提问: {prompt}\n")
    
    print("获取JSON格式响应...\n")
    result = client.ask_json(prompt)
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))

def test_native_qwq_think(client):
    """测试原生支持思考过程的模型"""
    # 确认是百炼(QwQ)客户端
    if "dashscope.aliyuncs.com" not in (client.base_url or ""):
        print("此测试函数仅适用于百炼(QwQ)模型")
        return
    
    print("\n===== 测试原生QwQ思考流式输出 =====")
    prompt = "9.9和9.11谁大?"
    print(f"提问: {prompt}\n")
    
    print("开始流式思考输出:")
    
    # 跟踪当前类型
    current_type = None
    
    # 直接处理每个流式块
    for chunk in client.stream_think(prompt):
        chunk_type = chunk["type"]
        content = chunk["content"]
        
        # 处理状态转换
        if chunk_type == "transition":
            print("\n----- 开始回答 -----\n")
            current_type = "answer"
            continue
        
        # 首次切换类型时显示标签
        if current_type != chunk_type:
            if chunk_type == "reasoning":
                print("\n[思考]", end=" ")
            elif chunk_type == "answer":
                print("\n[回答]", end=" ")
            current_type = chunk_type
        
        # 直接输出内容
        print(content, end="", flush=True)
    
    print("\n\n流式思考完成")

if __name__ == "__main__":
    try:
        # 依次尝试不同的客户端
        
   
        client = get_doubao_client()
        print("使用硅谷模型进行测试")
            
        
        if client:
            # 测试普通流式输出
            test_stream_ask(client)
            
            # 测试流式思考
            test_stream_think(client)
            
            # 测试完整思考结果
            test_think(client)
            
            # 测试优雅的思考显示
            test_thinking_display(client)
            
            # 测试会话流式接口
            session = test_session_stream(client)
            
            # 测试JSON格式响应
            test_json_api(client)
        else:
            print("未能初始化任何客户端")
        
    except Exception as e:
        import traceback
        print(f"\n发生错误: {e}")
        traceback.print_exc()
