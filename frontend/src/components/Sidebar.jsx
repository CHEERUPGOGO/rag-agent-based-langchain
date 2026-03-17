import React from 'react';
import { 
  MessageSquare, 
  Plus, 
  Trash2, 
  FileText, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Upload,
  BarChart3,
  X
} from 'lucide-react';

/**
 * 侧边栏组件
 * 包含对话列表、文档管理、设置等功能
 */
export default function Sidebar({ 
  isOpen, 
  onToggle, 
  onNewChat, 
  onClearChat,
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  isLoadingConversations,
  onOpenDocuments,
  onOpenSettings,
  onOpenEvaluation,
}) {
  return (
    <div 
      className={`
        sidebar-transition bg-dark-sidebar h-full flex flex-col
        ${isOpen ? 'w-64' : 'w-16'}
        border-r border-dark-border
      `}
    >
      {/* 头部 */}
      <div className="p-4 border-b border-dark-border flex items-center justify-between">
        {isOpen && (
          <h1 className="text-lg font-bold text-primary-400">RAG Agent</h1>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-dark-hover transition-colors"
          title={isOpen ? "收起侧边栏" : "展开侧边栏"}
        >
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* 新建对话按钮 */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className={`
            w-full flex items-center gap-3 p-3 rounded-lg
            bg-primary-600 hover:bg-primary-700 transition-colors
            btn-hover text-white font-medium
          `}
        >
          <Plus size={20} />
          {isOpen && <span>新建对话</span>}
        </button>
      </div>

      {/* 对话列表 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoadingConversations ? (
          isOpen && (
            <div className="text-center text-dark-muted text-sm py-8">
              加载中...
            </div>
          )
        ) : conversations.length > 0 ? (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`
                flex items-center gap-2 p-3 rounded-lg text-left
                transition-colors text-sm group
                ${conv.id === currentConversationId 
                  ? 'bg-dark-hover text-primary-400' 
                  : 'hover:bg-dark-hover text-dark-text'
                }
              `}
            >
              <MessageSquare size={18} className="flex-shrink-0" />
              <button
                onClick={() => onSelectConversation?.(conv.id)}
                className="flex-1 truncate hover:text-primary-400 transition-colors text-left"
                title={conv.title || '新对话'}
              >
                {conv.title || '新对话'}
              </button>
              {isOpen && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation?.(conv.id);
                  }}
                  className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-900/50 transition-all"
                  title="删除对话"
                >
                  <X size={16} className="text-red-400" />
                </button>
              )}
            </div>
          ))
        ) : isOpen ? (
          <div className="text-center text-dark-muted text-sm py-8">
            暂无对话记录
          </div>
        ) : null}
      </div>

      {/* 底部功能区 */}
      <div className="border-t border-dark-border p-3 space-y-2">
        {/* 文档管理 */}
        <button
          onClick={onOpenDocuments}
          className={`
            w-full flex items-center gap-3 p-3 rounded-lg
            hover:bg-dark-hover transition-colors text-dark-text
          `}
          title="文档管理"
        >
          <Upload size={20} />
          {isOpen && <span>文档管理</span>}
        </button>

        {/* 评估功能 */}
        <button
          onClick={onOpenEvaluation}
          className={`
            w-full flex items-center gap-3 p-3 rounded-lg
            hover:bg-dark-hover transition-colors text-dark-text
          `}
          title="RAG评估"
        >
          <BarChart3 size={20} />
          {isOpen && <span>RAG评估</span>}
        </button>

        {/* 清空对话 */}
        <button
          onClick={onClearChat}
          className={`
            w-full flex items-center gap-3 p-3 rounded-lg
            hover:bg-red-900/30 transition-colors text-red-400
          `}
          title="清空当前对话"
        >
          <Trash2 size={20} />
          {isOpen && <span>清空对话</span>}
        </button>

        {/* 设置 */}
        <button
          onClick={onOpenSettings}
          className={`
            w-full flex items-center gap-3 p-3 rounded-lg
            hover:bg-dark-hover transition-colors text-dark-text
          `}
          title="设置"
        >
          <Settings size={20} />
          {isOpen && <span>设置</span>}
        </button>
      </div>
    </div>
  );
}
