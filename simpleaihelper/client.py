"""
OpenAI API交互的核心客户端实现
"""

import os
import json
from typing import List, Dict, Any, Optional, Union, Generator, Callable

try:
    import openai
    from openai.types.chat import ChatCompletion, ChatCompletionChunk
except ImportError:
    raise ImportError("需要安装OpenAI包。请使用命令安装: pip install openai")

from .session import Session
from .db.sqlite_manager import SQLiteManager
from .db.json_manager import JSONManager


class AI:
    """
    用于与OpenAI API交互的高性能客户端。
    
    此类提供了一个优化的接口，用于向OpenAI发送请求，
    支持单条消息、流式输出和会话管理。
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
        **kwargs
    ):
        """
        初始化AI客户端。
        
        参数:
            api_key: OpenAI API密钥
            base_url: 可选的API基础URL
            default_model: 默认使用的模型
            **kwargs: 传递给OpenAI客户端的其他参数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.kwargs = kwargs
        
        # 配置OpenAI客户端
        self.client_kwargs = {"api_key": api_key}
        if base_url:
            self.client_kwargs["base_url"] = base_url
            
        self.client = openai.OpenAI(**self.client_kwargs)
    
    def _prepare_messages(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        准备发送给OpenAI API的消息。
        
        参数:
            prompt: 当前的提示语
            messages: 可选的历史消息
            
        返回:
            消息字典列表
        """
        if messages is None:
            messages = []
            
        # 添加当前用户提示
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def _prepare_completion_kwargs(self, **kwargs) -> Dict[str, Any]:
        """
        准备用于补全API的关键字参数。
        
        参数:
            **kwargs: 补全的其他参数
            
        返回:
            参数字典
        """
        completion_kwargs = self.kwargs.copy()
        completion_kwargs.update(kwargs)
        
        # 如果未提供模型，设置默认模型
        if "model" not in completion_kwargs:
            completion_kwargs["model"] = self.default_model
            
        return completion_kwargs
    
    def ask(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None, 
        **kwargs
    ) -> str:
        """
        Send a request to the OpenAI API and get a response.
        
        Args:
            prompt: The prompt to send
            messages: Optional previous messages for context
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            The response text
        """
        prepared_messages = self._prepare_messages(prompt, messages)
        completion_kwargs = self._prepare_completion_kwargs(**kwargs)
        
        response = self.client.chat.completions.create(
            messages=prepared_messages,
            **completion_kwargs
        )
        
        return response.choices[0].message.content
    
    def stream_ask(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None, 
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream a response from the OpenAI API in real-time.
        
        Args:
            prompt: The prompt to send
            messages: Optional previous messages for context
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Yields:
            Chunks of the response text as they become available
        """
        prepared_messages = self._prepare_messages(prompt, messages)
        completion_kwargs = self._prepare_completion_kwargs(**kwargs)
        
        # Set streaming parameter
        completion_kwargs["stream"] = True
        
        response = self.client.chat.completions.create(
            messages=prepared_messages,
            **completion_kwargs
        )
        
        # 直接返回原始流式内容
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def stream_think(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None, 
        **kwargs
    ) -> Generator[Dict[str, str], None, None]:
        """
        流式输出带有推理步骤的响应(思考过程)。
        
        此方法以流式方式实时输出响应，并将思考过程与最终答案分开。
        它能处理两种情况：
        1. 原生支持思考过程的模型(通过reasoning_content属性)
        2. 普通模型(通过文本标记"思考过程："和"回复内容："来区分)
        
        参数:
            prompt: 要发送的提示语
            messages: 可选的历史消息上下文
            **kwargs: 传递给API的其他参数
            
        生成:
            包含'type'和'content'键的字典，其中type可能是：
            - 'reasoning': 表示思考过程
            - 'transition': 表示从思考到回答的转换点
            - 'answer': 表示最终答案
        """
        # 准备消息
        prepared_messages = self._prepare_messages(prompt, messages)
        completion_kwargs = self._prepare_completion_kwargs(**kwargs)
        
        # 添加系统指令以显示推理过程(对于不原生支持思考过程的模型)
        system_msg = {
            "role": "system", 
            "content": "First think step-by-step about the problem, exploring different angles thoroughly. Start your thinking with '思考过程：'. Once you've reached a conclusion, present your final answer starting with '回复内容：'."
        }
        
        # 在开头插入系统消息
        if messages and messages[0].get("role") == "system":
            # 如果已有系统消息，附加我们的指令
            original_content = messages[0].get("content", "")
            messages[0]["content"] = f"{original_content}\n\n{system_msg['content']}"
        else:
            # 否则，在开头添加我们的系统消息
            prepared_messages.insert(0, system_msg)
        
        # 设置流式输出
        completion_kwargs["stream"] = True
        
        # 流式输出响应
        response = self.client.chat.completions.create(
            messages=prepared_messages,
            **completion_kwargs
        )
        
        # 状态跟踪
        is_reasoning = True  # 默认在思考阶段
        seen_reasoning_prefix = False  # 是否已看到"思考过程："前缀
        has_reasoning_attribute = False  # 模型是否支持reasoning_content属性
        
        for chunk in response:
            if not chunk.choices:
                continue
            
            delta = chunk.choices[0].delta
            
            # 检查是否有reasoning_content属性(对于原生支持思考过程的模型)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                has_reasoning_attribute = True
                yield {"type": "reasoning", "content": delta.reasoning_content}
                continue
            
            # 如果已经确认模型支持reasoning_content，则当content不为空时视为回答
            if has_reasoning_attribute and hasattr(delta, 'content') and delta.content:
                # 首次收到content时，发送转换信号
                if is_reasoning:
                    yield {"type": "transition", "content": ""}
                    is_reasoning = False
                
                yield {"type": "answer", "content": delta.content}
                continue
            
            # 如果模型不支持reasoning_content，使用基于文本的判断(适用于普通模型)
            if not has_reasoning_attribute and hasattr(delta, 'content') and delta.content:
                content = delta.content
                
                # 检查是否包含回复内容标记
                if is_reasoning and "回复内容：" in content:
                    # 分离思考和回答部分
                    parts = content.split("回复内容：", 1)
                    
                    # 如果标记前有思考内容，先输出
                    if parts[0]:
                        thought = parts[0]
                        if not seen_reasoning_prefix and "思考过程：" in thought:
                            thought = thought.replace("思考过程：", "", 1)
                            seen_reasoning_prefix = True
                        yield {"type": "reasoning", "content": thought}
                    
                    # 发送转换信号
                    yield {"type": "transition", "content": ""}
                    
                    # 切换到回答阶段
                    is_reasoning = False
                    
                    # 如果标记后有回答内容，再输出
                    if len(parts) > 1 and parts[1]:
                        yield {"type": "answer", "content": parts[1]}
                
                # 处理普通思考内容
                elif is_reasoning:
                    # 移除前缀标记(仅一次)
                    if not seen_reasoning_prefix and "思考过程：" in content:
                        content = content.replace("思考过程：", "", 1)
                        seen_reasoning_prefix = True
                    yield {"type": "reasoning", "content": content}
                
                # 处理普通回答内容
                else:
                    yield {"type": "answer", "content": content}

    def think(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        请求带有推理步骤的详细响应(QwQ风格思考)。
        
        此方法将思考过程与最终答案分开，模仿QwQ等模型提供明确的推理过程。
        
        参数:
            prompt: 要发送的提示语
            messages: 可选的历史消息上下文
            **kwargs: 传递给OpenAI API的其他参数
            
        返回:
            包含'reasoning'和'answer'键的字典
        """
        reasoning_content = ""
        answer_content = ""
        
        # 使用stream_think生成器构建完整响应
        for chunk in self.stream_think(prompt, messages, **kwargs):
            if chunk["type"] == "reasoning":
                reasoning_content += chunk["content"]
            elif chunk["type"] == "answer":
                answer_content += chunk["content"]
        
        return {
            "reasoning": reasoning_content.strip(),
            "answer": answer_content.strip()
        }
    
    def ask_json(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Request a response in JSON format.
        
        Args:
            prompt: The prompt to send
            messages: Optional previous messages for context
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            Parsed JSON object
        """
        # Add system message for JSON format
        system_msg = {"role": "system", "content": "Provide your response in valid JSON format only."}
        msgs = messages.copy() if messages else []
        msgs.insert(0, system_msg)
        
        response = self.ask(prompt, msgs, **kwargs)
        
        try:
            # Clean response and parse JSON
            cleaned_response = response.strip()
            # Remove markdown code blocks if present
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
                
            return json.loads(cleaned_response.strip())
        except json.JSONDecodeError:
            # Fallback - return as text if JSON parsing fails
            return {"error": "Failed to parse JSON", "text": response}
    
    def session(self, system_prompt: str = "", **kwargs) -> "Session":
        """
        Create a new conversation session.
        
        Args:
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to pass to the session
            
        Returns:
            A Session object
        """
        return Session(self, system_prompt, **kwargs)
    
    def load_db(self, db_path: str, **kwargs) -> SQLiteManager:
        """
        Load a database for session management.
        
        Args:
            db_path: Path to the database file
            **kwargs: Additional parameters
            
        Returns:
            A database manager
        """
        return SQLiteManager(db_path, self, **kwargs)
    
    def load_json(self, json_path: str, **kwargs) -> JSONManager:
        """
        Load a JSON file for session management.
        
        Args:
            json_path: Path to the JSON file
            **kwargs: Additional parameters
            
        Returns:
            A JSON manager
        """
        return JSONManager(json_path, self, **kwargs)
    
    def thinking_display(
        self, 
        prompt: str, 
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        优雅地获取思考过程和结果。
        
        此方法提供了一种简洁的方式来获取结构化的思考过程和最终答案，
        返回一个包含'reasoning'和'answer'键的字典。
        
        参数:
            prompt: 要发送的提示语
            messages: 可选的历史消息上下文
            **kwargs: 传递给OpenAI API的其他参数
            
        返回:
            包含'reasoning'和'answer'键的字典
        """
        # 直接使用think方法获取结构化结果
        result = self.think(prompt, messages, **kwargs)
        return result 