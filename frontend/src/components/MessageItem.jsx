import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  User, 
  Bot, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp,
  Globe,
  Database,
  RefreshCw
} from 'lucide-react';

/**
 * 单条消息组件
 */
export default function MessageItem({ message, isLast }) {
  const [copied, setCopied] = useState(false);
  const [showThoughts, setShowThoughts] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  // 复制内容
  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Markdown 渲染配置
  const markdownComponents = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={match[1]}
          PreTag="div"
          className="rounded-lg my-2"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
  };

  return (
    <div className={`message-enter flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* 头像 */}
      <div className={`
        flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
        ${isUser 
          ? 'bg-gradient-to-br from-purple-500 to-purple-700' 
          : 'bg-gradient-to-br from-primary-500 to-primary-700'
        }
      `}>
        {isUser ? <User size={20} className="text-white" /> : <Bot size={20} className="text-white" />}
      </div>

      {/* 消息内容 */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        {/* 消息气泡 */}
        <div className={`
          inline-block rounded-2xl px-4 py-3 text-left
          ${isUser 
            ? 'bg-primary-600 text-white' 
            : 'bg-dark-card text-dark-text'
          }
        `}>
          {/* 打字指示器 */}
          {isStreaming && !message.content && (
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          )}

          {/* 消息内容 */}
          {message.content && (
            <div className={`markdown-content ${isUser ? 'text-white' : ''}`}>
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <ReactMarkdown components={markdownComponents}>
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          )}

          {/* 流式加载光标 */}
          {isStreaming && message.content && (
            <span className="inline-block w-2 h-4 bg-primary-400 ml-1 animate-pulse" />
          )}
        </div>

        {/* 消息操作区 */}
        {!isUser && message.content && !isStreaming && (
          <div className="mt-2 flex items-center gap-2 text-xs text-dark-muted">
            {/* 复制按钮 */}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-dark-text transition-colors p-1 rounded"
              title="复制"
            >
              {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
              {copied && <span className="text-green-400">已复制</span>}
            </button>

            {/* 思考过程 */}
            {message.thoughts && message.thoughts.length > 0 && (
              <button
                onClick={() => setShowThoughts(!showThoughts)}
                className="flex items-center gap-1 hover:text-primary-400 transition-colors p-1 rounded"
              >
                <RefreshCw size={14} />
                <span>思考过程</span>
                {showThoughts ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            )}

            {/* 引用来源 */}
            {message.sources && message.sources.length > 0 && (
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1 hover:text-green-400 transition-colors p-1 rounded"
              >
                {message.sources.some(s => s.source === 'web') ? <Globe size={14} /> : <Database size={14} />}
                <span>引用来源 ({message.sources.length})</span>
                {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            )}
          </div>
        )}

        {/* 思考过程展开区域 */}
        {showThoughts && message.thoughts && (
          <div className="mt-3 p-3 bg-dark-bg rounded-xl border border-dark-border text-left">
            <h4 className="text-sm font-medium text-primary-400 mb-2">思考过程</h4>
            <div className="space-y-2">
              {message.thoughts.map((thought, index) => (
                <div key={index} className="text-xs">
                  <div className="flex items-center gap-2 text-dark-text">
                    <span className="bg-primary-600/20 text-primary-400 px-2 py-0.5 rounded">
                      步骤 {thought.step}
                    </span>
                    <span className="font-medium">{thought.action}</span>
                  </div>
                  {thought.action_input && (
                    <p className="text-dark-muted mt-1 ml-4">输入: {thought.action_input}</p>
                  )}
                  {thought.observation && (
                    <p className="text-dark-muted mt-1 ml-4 line-clamp-2">结果: {thought.observation}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 引用来源展开区域 */}
        {showSources && message.sources && (
          <div className="mt-3 p-3 bg-dark-bg rounded-xl border border-dark-border text-left">
            <h4 className="text-sm font-medium text-green-400 mb-2">引用来源</h4>
            <div className="space-y-2">
              {message.sources.map((source, index) => (
                <div key={index} className="text-xs p-2 bg-dark-card rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    {source.source === 'web' ? (
                      <Globe size={12} className="text-green-400" />
                    ) : (
                      <Database size={12} className="text-primary-400" />
                    )}
                    <span className={source.source === 'web' ? 'text-green-400' : 'text-primary-400'}>
                      {source.source === 'web' ? '网络搜索' : '知识库'}
                    </span>
                  </div>
                  <p className="text-dark-muted line-clamp-3">{source.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
