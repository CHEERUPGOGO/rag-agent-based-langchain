import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';

/**
 * 消息列表组件
 */
export default function MessageList({ 
  messages, 
  isLoading,
  currentThoughts,
  currentSources,
}) {
  const messagesEndRef = useRef(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentThoughts]);

  // 空状态
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md px-6">
          <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg 
              className="w-10 h-10 text-white" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" 
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-dark-text mb-3">
            你好，有什么可以帮助你的？
          </h2>
          <p className="text-dark-muted mb-6">
            我是基于 LangChain 1.0 构建的 RAG Agent，可以帮你检索知识库内容，也可以联网搜索最新信息。
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-dark-card p-4 rounded-xl text-left hover:bg-dark-hover transition-colors cursor-pointer">
              <p className="text-primary-400 font-medium mb-1">知识库问答</p>
              <p className="text-dark-muted text-xs">基于上传的文档回答问题</p>
            </div>
            <div className="bg-dark-card p-4 rounded-xl text-left hover:bg-dark-hover transition-colors cursor-pointer">
              <p className="text-green-400 font-medium mb-1">联网搜索</p>
              <p className="text-dark-muted text-xs">获取最新的网络信息</p>
            </div>
            <div className="bg-dark-card p-4 rounded-xl text-left hover:bg-dark-hover transition-colors cursor-pointer">
              <p className="text-purple-400 font-medium mb-1">混合检索</p>
              <p className="text-dark-muted text-xs">结合多个来源给出答案</p>
            </div>
            <div className="bg-dark-card p-4 rounded-xl text-left hover:bg-dark-hover transition-colors cursor-pointer">
              <p className="text-orange-400 font-medium mb-1">效果评估</p>
              <p className="text-dark-muted text-xs">使用RAGAS评估RAG效果</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto py-6 px-4 space-y-6">
        {messages.map((message, index) => (
          <MessageItem 
            key={message.id} 
            message={message}
            isLast={index === messages.length - 1}
          />
        ))}
        
        {/* 当前思考过程展示 */}
        {isLoading && currentThoughts.length > 0 && (
          <div className="bg-dark-card/50 rounded-xl p-4 border border-dark-border">
            <p className="text-sm text-primary-400 font-medium mb-2">正在思考...</p>
            {currentThoughts.map((thought, index) => (
              <div key={index} className="text-xs text-dark-muted mb-1">
                步骤 {thought.step}: {thought.action}
              </div>
            ))}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
