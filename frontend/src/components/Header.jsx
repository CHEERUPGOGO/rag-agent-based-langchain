import React from 'react';
import { Globe, Database, Zap } from 'lucide-react';

/**
 * 顶部导航栏组件
 */
export default function Header({ 
  useRag, 
  setUseRag, 
  useWebSearch, 
  setUseWebSearch,
  isConnected = true,
}) {
  return (
    <header className="bg-dark-sidebar border-b border-dark-border px-6 py-3">
      <div className="flex items-center justify-between">
        {/* 左侧标题 */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
            <Zap size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-dark-text">LangChain RAG Agent</h1>
            <p className="text-xs text-dark-muted">基于 LangChain 1.0 构建</p>
          </div>
        </div>

        {/* 中间功能开关 */}
        <div className="flex items-center gap-4">
          {/* RAG开关 */}
          <label className="flex items-center gap-2 cursor-pointer group">
            <div className={`
              p-2 rounded-lg transition-colors
              ${useRag ? 'bg-primary-600/20 text-primary-400' : 'bg-dark-hover text-dark-muted'}
            `}>
              <Database size={18} />
            </div>
            <span className={`text-sm ${useRag ? 'text-primary-400' : 'text-dark-muted'}`}>
              知识库检索
            </span>
            <div 
              className={`
                relative w-10 h-5 rounded-full transition-colors cursor-pointer
                ${useRag ? 'bg-primary-600' : 'bg-dark-hover'}
              `}
              onClick={() => setUseRag(!useRag)}
            >
              <div className={`
                absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform
                ${useRag ? 'translate-x-5' : 'translate-x-0.5'}
              `} />
            </div>
          </label>

          {/* 联网搜索开关 */}
          <label className="flex items-center gap-2 cursor-pointer group">
            <div className={`
              p-2 rounded-lg transition-colors
              ${useWebSearch ? 'bg-green-600/20 text-green-400' : 'bg-dark-hover text-dark-muted'}
            `}>
              <Globe size={18} />
            </div>
            <span className={`text-sm ${useWebSearch ? 'text-green-400' : 'text-dark-muted'}`}>
              联网搜索
            </span>
            <div 
              className={`
                relative w-10 h-5 rounded-full transition-colors cursor-pointer
                ${useWebSearch ? 'bg-green-600' : 'bg-dark-hover'}
              `}
              onClick={() => setUseWebSearch(!useWebSearch)}
            >
              <div className={`
                absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform
                ${useWebSearch ? 'translate-x-5' : 'translate-x-0.5'}
              `} />
            </div>
          </label>
        </div>

        {/* 右侧状态 */}
        <div className="flex items-center gap-2">
          <div className={`
            w-2 h-2 rounded-full
            ${isConnected ? 'bg-green-500' : 'bg-red-500'}
          `} />
          <span className="text-sm text-dark-muted">
            {isConnected ? '已连接' : '未连接'}
          </span>
        </div>
      </div>
    </header>
  );
}
