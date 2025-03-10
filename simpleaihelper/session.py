"""
OpenAI API对话会话管理
"""

import time
import uuid
from typing import List, Dict, Any, Optional, Generator, Union

class Session:
    """
    用于管理与OpenAI API对话的会话。
    
    此类维护对话历史并提供在会话上下文中
    与API交互的方法。
    """
    
    def __init__(self, client, system_prompt: str = "", **kwargs):
        """
        初始化新会话。
        
        参数:
            client: AI客户端实例
            system_prompt: 可选的系统提示语
            **kwargs: API请求的其他参数
        """
        self.client = client
        self.messages = []
        self.kwargs = kwargs
        self.session_id = str(uuid.uuid4())
        self.created_at = time.time()
        
        # 如果提供了系统提示语，则添加
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
            
    def ask(self, prompt: str, **kwargs) -> str:
        """
        Send a request to the OpenAI API and get a response within this session.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            The response text
        """
        # Combine session kwargs with call-specific kwargs
        request_kwargs = self.kwargs.copy()
        request_kwargs.update(kwargs)
        
        # Get response using the client
        response = self.client.ask(prompt, self.messages, **request_kwargs)
        
        # Update conversation history
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": response})
        
        return response
        
    def stream_ask(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """
        Stream a response from the OpenAI API within this session.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Yields:
            Chunks of the response text as they become available
        """
        # Combine session kwargs with call-specific kwargs
        request_kwargs = self.kwargs.copy()
        request_kwargs.update(kwargs)
        
        # Add the user message to history
        self.messages.append({"role": "user", "content": prompt})
        
        # Stream the response
        response_chunks = []
        for chunk in self.client.stream_ask(prompt, self.messages[:-1], **request_kwargs):
            response_chunks.append(chunk)
            yield chunk
            
        # Combine chunks and add to conversation history
        full_response = "".join(response_chunks)
        self.messages.append({"role": "assistant", "content": full_response})
    
    def stream_think(self, prompt: str, **kwargs) -> Generator[Dict[str, str], None, None]:
        """
        在此会话中流式输出带有推理步骤的详细响应(QwQ风格)。
        
        参数:
            prompt: 要发送的提示语
            **kwargs: 传递给OpenAI API的其他参数
            
        生成:
            包含'type'(可能是'reasoning'或'answer')和'content'键的字典
        """
        # 合并会话kwargs和调用特定的kwargs
        request_kwargs = self.kwargs.copy()
        request_kwargs.update(kwargs)
        
        # 将用户消息添加到历史记录
        self.messages.append({"role": "user", "content": prompt})
        
        # 跟踪累积的内容以便稍后存储在历史记录中
        accumulated_reasoning = ""
        accumulated_answer = ""
        
        # 用于去重
        seen_answer_text = set()
        transition_emitted = False
        
        # 流式输出思考过程
        for chunk in self.client.stream_think(prompt, self.messages[:-1], **request_kwargs):
            # 特殊处理转换标记，确保只发出一次
            if chunk["type"] == "transition" and not transition_emitted:
                transition_emitted = True
                yield chunk
                continue
            elif chunk["type"] == "transition":
                # 已经发出过转换标记，跳过
                continue
            
            # 为历史记录累积内容
            if chunk["type"] == "reasoning":
                accumulated_reasoning += chunk["content"]
                # 直接传递推理块
                yield chunk
            elif chunk["type"] == "answer":
                # 对答案块进行去重
                content = chunk["content"]
                if not content in seen_answer_text:
                    seen_answer_text.add(content)
                    accumulated_answer += content
                    # 传递唯一的答案块
                    yield chunk
        
        # 清理可能的重复前缀
        answer_parts = accumulated_answer.split("回复内容：")
        if len(answer_parts) > 1:
            # 如果存在多个"回复内容："前缀，只保留最后一部分
            accumulated_answer = answer_parts[-1]
        
        # 流式输出完成后，用完整响应更新对话历史
        self.messages.append({
            "role": "assistant", 
            "content": f"思考过程：\n{accumulated_reasoning}\n\n回复内容：\n{accumulated_answer}"
        })
    
    def think(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        在此会话中请求带有推理步骤的详细响应(QwQ风格)。
        
        参数:
            prompt: 要发送的提示语
            **kwargs: 传递给OpenAI API的其他参数
            
        返回:
            包含'reasoning'和'answer'键的字典
        """
        # 合并会话kwargs和调用特定的kwargs
        request_kwargs = self.kwargs.copy()
        request_kwargs.update(kwargs)
        
        # 跟踪累积的内容
        reasoning_content = ""
        answer_content = ""
        seen_answer_text = set()  # 用集合追踪已见过的答案文本
        
        # 流式输出并累积响应
        for chunk in self.stream_think(prompt, **request_kwargs):
            if chunk["type"] == "reasoning":
                reasoning_content += chunk["content"]
            elif chunk["type"] == "answer":
                # 使用集合去重
                if not chunk["content"] in seen_answer_text:
                    seen_answer_text.add(chunk["content"])
                    answer_content += chunk["content"]
        
        # 清理可能的重复前缀
        answer_parts = answer_content.split("回复内容：")
        if len(answer_parts) > 1:
            # 如果存在多个"回复内容："前缀，只保留最后一部分
            answer_content = answer_parts[-1]
        
        return {
            "reasoning": reasoning_content.strip(),
            "answer": answer_content.strip()
        }
    
    def ask_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Request a response in JSON format within this session.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            Parsed JSON object
        """
        # Combine session kwargs with call-specific kwargs
        request_kwargs = self.kwargs.copy()
        request_kwargs.update(kwargs)
        
        # Get JSON response
        result = self.client.ask_json(prompt, self.messages, **request_kwargs)
        
        # Update conversation history
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": str(result)})
        
        return result
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        获取对话历史。
        
        返回:
            消息字典列表
        """
        return self.messages.copy()
    
    def clear_history(self, keep_system: bool = True) -> None:
        """
        清除对话历史。
        
        参数:
            keep_system: 是否保留系统消息
        """
        if keep_system and self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []
            
    def thinking_display(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        优雅地获取思考过程和结果。
        
        这提供了一个更简洁的接口来获取思考过程和结果，
        返回一个包含推理过程和答案的字典。
        
        参数:
            prompt: 要发送的提示语
            **kwargs: 其他API参数
            
        返回:
            包含'reasoning'和'answer'键的字典
        
        示例:
            # 获取思考结果
            result = session.thinking_display("如何解决ABA问题?")
            print(f"推理过程: {result['reasoning']}")
            print(f"最终答案: {result['answer']}")
        """
        # 直接使用think方法获取结果
        return self.think(prompt, **kwargs) 