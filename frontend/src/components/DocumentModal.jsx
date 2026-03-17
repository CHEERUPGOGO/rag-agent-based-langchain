import React, { useState, useCallback, useEffect } from 'react';
import { X, Upload, FileText, Trash2, AlertCircle, CheckCircle } from 'lucide-react';
import { uploadDocument, getDocuments, deleteDocument, getDocumentStats } from '../services/api';

/**
 * 文档管理弹窗组件
 */
export default function DocumentModal({ isOpen, onClose }) {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // 加载文档列表
  const loadDocuments = useCallback(async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      const docStats = await getDocumentStats();
      setStats(docStats);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadDocuments();
    }
  }, [isOpen, loadDocuments]);

  // 处理文件上传
  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      for (const file of files) {
        await uploadDocument(file);
      }
      setSuccess(`成功上传 ${files.length} 个文件`);
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // 处理拖拽
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(Array.from(e.dataTransfer.files));
    }
  };

  // 处理删除
  const handleDelete = async (docId) => {
    if (!window.confirm('确定要删除这个文档吗？')) return;

    try {
      await deleteDocument(docId);
      setSuccess('文档已删除');
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-dark-sidebar w-full max-w-2xl max-h-[80vh] rounded-2xl shadow-2xl overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <div>
            <h2 className="text-xl font-bold text-dark-text">文档管理</h2>
            <p className="text-sm text-dark-muted mt-1">
              上传文档到知识库，支持 PDF、DOCX、TXT、MD 格式
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-dark-hover transition-colors text-dark-muted"
          >
            <X size={24} />
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* 统计信息 */}
          {stats && (
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-dark-card p-4 rounded-xl">
                <p className="text-2xl font-bold text-primary-400">{stats.total_documents}</p>
                <p className="text-sm text-dark-muted">文档数量</p>
              </div>
              <div className="bg-dark-card p-4 rounded-xl">
                <p className="text-2xl font-bold text-green-400">{stats.total_chunks}</p>
                <p className="text-sm text-dark-muted">文本块数量</p>
              </div>
            </div>
          )}

          {/* 上传区域 */}
          <div
            className={`dropzone p-8 text-center mb-6 ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload size={48} className="mx-auto mb-4 text-primary-400" />
            <p className="text-dark-text mb-2">拖拽文件到此处上传</p>
            <p className="text-sm text-dark-muted mb-4">或点击下方按钮选择文件</p>
            <label className="inline-block">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md"
                className="hidden"
                onChange={(e) => handleUpload(Array.from(e.target.files))}
                disabled={uploading}
              />
              <span className={`
                inline-block px-6 py-2 rounded-lg cursor-pointer transition-colors
                ${uploading 
                  ? 'bg-dark-hover text-dark-muted cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 text-white'
                }
              `}>
                {uploading ? '上传中...' : '选择文件'}
              </span>
            </label>
          </div>

          {/* 提示信息 */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-900 rounded-xl mb-4">
              <AlertCircle className="text-red-400" size={20} />
              <p className="text-red-400">{error}</p>
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 p-4 bg-green-900/20 border border-green-900 rounded-xl mb-4">
              <CheckCircle className="text-green-400" size={20} />
              <p className="text-green-400">{success}</p>
            </div>
          )}

          {/* 文档列表 */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-dark-muted">已上传文档</h3>
            {documents.length === 0 ? (
              <p className="text-center text-dark-muted py-8">暂无文档</p>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 bg-dark-card rounded-xl"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="text-primary-400" size={24} />
                    <div>
                      <p className="text-dark-text font-medium">{doc.filename}</p>
                      <p className="text-xs text-dark-muted">
                        {formatFileSize(doc.file_size)} · {doc.chunk_count} 个文本块
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 rounded-lg hover:bg-red-900/30 transition-colors text-red-400"
                    title="删除"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
