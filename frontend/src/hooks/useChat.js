import { useCallback, useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendMessageStream, getConversationHistory, getConversationState } from '../services/api';

/**
 * 聊天功能 Hook
 * 支持从后端持久化存储加载对话历史
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(() => uuidv4());
  const [userId, setUserId] = useState(() => {
    // 从 localStorage 读取或生成新的用户ID
    const stored = localStorage.getItem('userId');
    if (stored) return stored;
    const newId = uuidv4();
    localStorage.setItem('userId', newId);
    return newId;
  });
  const [currentThoughts, setCurrentThoughts] = useState([]);
  const [currentSources, setCurrentSources] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const abortControllerRef = useRef(null);
  const messagesRef = useRef([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  /**
   * 从后端加载对话历史
   * 当用户点击侧边栏中的既有对话时调用
   */
  const loadConversationHistory = useCallback(async (conversationId) => {
    setIsLoadingHistory(true);
    setError(null);
    try {
      const historyData = await getConversationHistory(conversationId, userId);
      if (historyData.messages && historyData.messages.length > 0) {
        const historyMessages = historyData.messages.map((msg, index) => ({
          id: `msg-${conversationId}-${index}`,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
        }));
        setMessages(historyMessages);
      } else {
        const stateData = await getConversationState(conversationId, userId);
        if (stateData && stateData.messages && stateData.messages.length > 0) {
          const historyMessages = stateData.messages
            .map((msg, index) => {
              let msgContent = msg;
              if (typeof msg === 'string') {
                try {
                  msgContent = JSON.parse(msg);
                } catch (e) {
                  msgContent = { type: 'unknown', content: msg };
                }
              }

              let role = 'system';
              if (msgContent.type === 'ai') role = 'assistant';
              else if (msgContent.type === 'human') role = 'user';
              else if (msgContent.type === 'tool') role = 'tool';

              return {
                id: `msg-${conversationId}-${index}`,
                role: role,
                content: msgContent.content || '',
                timestamp: new Date(),
                raw: msgContent,
              };
            })
            .filter((msg) => msg.role !== 'tool' && msg.role !== 'system');

          setMessages(historyMessages);
        } else {
          setMessages([]);
        }
      }
      setConversationId(conversationId);
    } catch (err) {
      console.error('Failed to load conversation history:', err);
      setError(`无法加载对话历史: ${err.message}`);
      setMessages([]);
      setConversationId(conversationId);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [userId]);

  /**
   * 发送消息
   */
  const sendMessage = useCallback(async (content, options = {}) => {
    const trimmedContent = content.trim();
    if (!trimmedContent || isLoading) {
      return;
    }

    const userMessage = {
      id: uuidv4(),
      role: 'user',
      content: trimmedContent,
      timestamp: new Date(),
    };

    const assistantMessageId = uuidv4();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      thoughts: [],
      sources: [],
      isStreaming: true,
    };

    const history = messagesRef.current
      .filter((msg) => !msg.isStreaming)
      .map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

    abortControllerRef.current = new AbortController();
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);
    setError(null);
    setCurrentThoughts([]);
    setCurrentSources([]);

    let fullContent = '';
    const thoughts = [];
    const sources = [];

    try {
      for await (const chunk of sendMessageStream(trimmedContent, {
        conversationId,
        userId,
        history,
        useRag: options.useRag !== false,
        useWebSearch: options.useWebSearch !== false,
        signal: abortControllerRef.current.signal,
      })) {
        switch (chunk.type) {
          case 'token':
            fullContent += chunk.content;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullContent }
                  : msg
              )
            );
            break;

          case 'thought':
            thoughts.push(chunk.content);
            setCurrentThoughts([...thoughts]);
            break;

          case 'source':
            sources.push(chunk.content);
            setCurrentSources([...sources]);
            break;

          case 'done':
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      content: fullContent,
                      thoughts: chunk.thoughts || thoughts,
                      sources: chunk.sources || sources,
                      isStreaming: false,
                    }
                  : msg
              )
            );
            setCurrentThoughts([]);
            setCurrentSources([]);
            break;

          case 'error':
            throw new Error(chunk.content);

          default:
            break;
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: fullContent,
                  thoughts,
                  sources,
                  isStreaming: false,
                }
              : msg
          )
        );
      } else {
        let errorMessage = err.message || '请求失败';
        if (errorMessage.includes('Authentication') || errorMessage.includes('governor')) {
          errorMessage = 'API认证失败，请检查API密钥配置';
        }
        setError(errorMessage);
        setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId));
      }
      setCurrentThoughts([]);
      setCurrentSources([]);
    } finally {
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, [conversationId, isLoading, userId]);

  /**
   * 停止生成
   */
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  /**
   * 清空对话
   */
  const clearMessages = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setMessages([]);
    setConversationId(uuidv4());
    setError(null);
    setCurrentThoughts([]);
    setCurrentSources([]);
    setIsLoading(false);
  }, []);

  /**
   * 重新生成最后一条回复
   */
  const regenerateLastMessage = useCallback(async () => {
    const currentMessages = messagesRef.current;
    if (currentMessages.length < 2 || isLoading) {
      return;
    }

    const lastUserMessage = [...currentMessages].reverse().find((msg) => msg.role === 'user');
    if (!lastUserMessage) {
      return;
    }

    setMessages((prev) => prev.slice(0, -1));
    await sendMessage(lastUserMessage.content);
  }, [isLoading, sendMessage]);

  return {
    messages,
    isLoading,
    isLoadingHistory,
    error,
    conversationId,
    currentThoughts,
    currentSources,
    sendMessage,
    stopGeneration,
    clearMessages,
    regenerateLastMessage,
    loadConversationHistory,
    userId,
  };
}
