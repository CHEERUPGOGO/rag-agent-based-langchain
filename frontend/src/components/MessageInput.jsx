import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Paperclip } from 'lucide-react';

/**
 * 消息输入组件
 */
export default function MessageInput({
  onSendMessage,
  isLoading,
  onStopGeneration,
  disabled = false,
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // 自动调整高度
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [input]);

  // 发送消息
  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  // 键盘快捷键
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-dark-border bg-dark-sidebar p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative flex items-end gap-3">
          {/* 附件按钮 */}
          <button
            type="button"
            className="p-3 rounded-xl bg-dark-card hover:bg-dark-hover transition-colors text-dark-muted hover:text-dark-text"
            title="上传文件"
          >
            <Paperclip size={20} />
          </button>

          {/* 输入框容器 */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息，按 Enter 发送，Shift + Enter 换行..."
              disabled={disabled}
              rows={1}
              className="
                w-full px-4 py-3 pr-12
                bg-dark-card border border-dark-border rounded-xl
                text-dark-text placeholder-dark-muted
                resize-none
                focus:outline-none focus:border-primary-500
                input-focus
                disabled:opacity-50 disabled:cursor-not-allowed
              "
              style={{ maxHeight: '200px' }}
            />
          </div>

          {/* 发送/停止按钮 */}
          {isLoading ? (
            <button
              type="button"
              onClick={onStopGeneration}
              className="
                p-3 rounded-xl
                bg-red-600 hover:bg-red-700
                transition-colors text-white
                btn-hover
              "
              title="停止生成"
            >
              <Square size={20} />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || disabled}
              className={`
                p-3 rounded-xl transition-colors btn-hover
                ${input.trim() && !disabled
                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                  : 'bg-dark-card text-dark-muted cursor-not-allowed'
                }
              `}
              title="发送消息"
            >
              <Send size={20} />
            </button>
          )}
        </div>

        {/* 提示信息 */}
        <p className="text-xs text-dark-muted text-center mt-2">
          基于 LangChain 1.0 + DeepSeek 构建，支持知识库检索和联网搜索
        </p>
      </form>
    </div>
  );
}
