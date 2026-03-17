import React, { useState } from 'react';
import { X, Play, BarChart3, Info } from 'lucide-react';
import { evaluateRAG, getEvaluationMetrics } from '../services/api';

/**
 * RAG 评估面板组件
 */
export default function EvaluationPanel({ isOpen, onClose }) {
  const [samples, setSamples] = useState([
    {
      question: '',
      answer: '',
      contexts: [''],
      ground_truth: ''
    }
  ]);
  const [metrics, setMetrics] = useState([]);
  const [availableMetrics, setAvailableMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 获取可用的评估指标
  React.useEffect(() => {
    if (isOpen) {
      loadMetrics();
    }
  }, [isOpen]);

  const loadMetrics = async () => {
    try {
      const data = await getEvaluationMetrics();
      setAvailableMetrics(data.metrics || []);
    } catch (err) {
      console.error('加载指标失败:', err);
    }
  };

  // 添加样本
  const addSample = () => {
    setSamples([
      ...samples,
      {
        question: '',
        answer: '',
        contexts: [''],
        ground_truth: ''
      }
    ]);
  };

  // 删除样本
  const removeSample = (index) => {
    setSamples(samples.filter((_, i) => i !== index));
  };

  // 更新样本字段
  const updateSample = (index, field, value) => {
    const newSamples = [...samples];
    newSamples[index][field] = value;
    setSamples(newSamples);
  };

  // 更新上下文
  const updateContext = (sampleIndex, contextIndex, value) => {
    const newSamples = [...samples];
    newSamples[sampleIndex].contexts[contextIndex] = value;
    setSamples(newSamples);
  };

  // 添加上下文
  const addContext = (sampleIndex) => {
    const newSamples = [...samples];
    newSamples[sampleIndex].contexts.push('');
    setSamples(newSamples);
  };

  // 删除上下文
  const removeContext = (sampleIndex, contextIndex) => {
    const newSamples = [...samples];
    newSamples[sampleIndex].contexts.splice(contextIndex, 1);
    setSamples(newSamples);
  };

  // 切换指标选择
  const toggleMetric = (metricName) => {
    if (metrics.includes(metricName)) {
      setMetrics(metrics.filter(m => m !== metricName));
    } else {
      setMetrics([...metrics, metricName]);
    }
  };

  // 执行评估
  const handleEvaluate = async () => {
    // 验证输入
    const validSamples = samples.filter(s => s.question && s.answer && s.contexts.some(c => c.trim()));
    if (validSamples.length === 0) {
      setError('请至少填写一个完整的评估样本（问题、答案和上下文）');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const evalResult = await evaluateRAG(validSamples, metrics.length > 0 ? metrics : null);
      setResult(evalResult);
    } catch (err) {
      setError(`评估失败：${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-card rounded-xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <div className="flex items-center gap-3">
            <BarChart3 className="text-primary-400" size={24} />
            <h2 className="text-2xl font-bold text-dark-text">RAG 效果评估</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
          >
            <X size={20} className="text-dark-muted" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* 评估指标选择 */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-dark-text mb-3 flex items-center gap-2">
              <Info size={18} className="text-primary-400" />
              选择评估指标
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {availableMetrics.map((metric) => (
                <label
                  key={metric.name}
                  className={`
                    p-3 rounded-lg border cursor-pointer transition-all
                    ${metrics.includes(metric.name)
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-dark-border bg-dark-card hover:border-primary-500/50'
                    }
                  `}
                >
                  <input
                    type="checkbox"
                    checked={metrics.includes(metric.name)}
                    onChange={() => toggleMetric(metric.name)}
                    className="mr-2"
                  />
                  <span className="text-sm text-dark-text">{metric.name}</span>
                  <p className="text-xs text-dark-muted mt-1">{metric.description}</p>
                </label>
              ))}
            </div>
          </div>

          {/* 评估样本输入 */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-dark-text">评估样本</h3>
              <button
                onClick={addSample}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors text-sm"
              >
                + 添加样本
              </button>
            </div>

            <div className="space-y-4">
              {samples.map((sample, sampleIndex) => (
                <div
                  key={sampleIndex}
                  className="bg-dark-sidebar p-4 rounded-lg border border-dark-border"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-primary-400">样本 {sampleIndex + 1}</h4>
                    {samples.length > 1 && (
                      <button
                        onClick={() => removeSample(sampleIndex)}
                        className="text-red-400 hover:text-red-300 text-sm"
                      >
                        删除
                      </button>
                    )}
                  </div>

                  {/* 问题 */}
                  <div className="mb-3">
                    <label className="block text-sm text-dark-muted mb-1">问题 *</label>
                    <textarea
                      value={sample.question}
                      onChange={(e) => updateSample(sampleIndex, 'question', e.target.value)}
                      className="w-full bg-dark-card border border-dark-border rounded-lg p-2 text-dark-text text-sm focus:outline-none focus:border-primary-500"
                      rows={2}
                      placeholder="请输入问题..."
                    />
                  </div>

                  {/* 答案 */}
                  <div className="mb-3">
                    <label className="block text-sm text-dark-muted mb-1">答案 *</label>
                    <textarea
                      value={sample.answer}
                      onChange={(e) => updateSample(sampleIndex, 'answer', e.target.value)}
                      className="w-full bg-dark-card border border-dark-border rounded-lg p-2 text-dark-text text-sm focus:outline-none focus:border-primary-500"
                      rows={3}
                      placeholder="请输入模型生成的答案..."
                    />
                  </div>

                  {/* 上下文 */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-sm text-dark-muted">检索到的上下文 *</label>
                      <button
                        onClick={() => addContext(sampleIndex)}
                        className="text-xs text-primary-400 hover:text-primary-300"
                      >
                        + 添加上下文
                      </button>
                    </div>
                    {sample.contexts.map((context, contextIndex) => (
                      <div key={contextIndex} className="flex gap-2 mb-2">
                        <textarea
                          value={context}
                          onChange={(e) => updateContext(sampleIndex, contextIndex, e.target.value)}
                          className="flex-1 bg-dark-card border border-dark-border rounded-lg p-2 text-dark-text text-sm focus:outline-none focus:border-primary-500"
                          rows={2}
                          placeholder="请输入检索到的上下文内容..."
                        />
                        {sample.contexts.length > 1 && (
                          <button
                            onClick={() => removeContext(sampleIndex, contextIndex)}
                            className="p-2 text-red-400 hover:text-red-300"
                          >
                            <X size={16} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* 标准答案（可选） */}
                  <div>
                    <label className="block text-sm text-dark-muted mb-1">
                      标准答案（可选）
                    </label>
                    <textarea
                      value={sample.ground_truth}
                      onChange={(e) => updateSample(sampleIndex, 'ground_truth', e.target.value)}
                      className="w-full bg-dark-card border border-dark-border rounded-lg p-2 text-dark-text text-sm focus:outline-none focus:border-primary-500"
                      rows={2}
                      placeholder="如果有标准答案，请输入..."
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 执行按钮 */}
          <button
            onClick={handleEvaluate}
            disabled={loading}
            className={`
              w-full py-3 rounded-lg flex items-center justify-center gap-2
              transition-colors font-medium
              ${loading
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-primary-600 hover:bg-primary-700 text-white'
              }
            `}
          >
            <Play size={18} />
            {loading ? '评估中...' : '开始评估'}
          </button>

          {/* 错误提示 */}
          {error && (
            <div className="mt-4 bg-red-900/30 border border-red-500 rounded-lg p-4 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* 评估结果展示 */}
          {result && result.success && result.metrics && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-dark-text mb-4">评估结果</h3>
              
              {/* 总体指标 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {result.metrics.faithfulness !== null && (
                  <div className="bg-dark-sidebar p-4 rounded-lg border border-dark-border">
                    <p className="text-xs text-dark-muted mb-1">忠实度</p>
                    <p className="text-2xl font-bold text-primary-400">
                      {result.metrics.faithfulness.toFixed(3)}
                    </p>
                  </div>
                )}
                {result.metrics.answer_relevancy !== null && (
                  <div className="bg-dark-sidebar p-4 rounded-lg border border-dark-border">
                    <p className="text-xs text-dark-muted mb-1">答案相关性</p>
                    <p className="text-2xl font-bold text-green-400">
                      {result.metrics.answer_relevancy.toFixed(3)}
                    </p>
                  </div>
                )}
                {result.metrics.context_precision !== null && (
                  <div className="bg-dark-sidebar p-4 rounded-lg border border-dark-border">
                    <p className="text-xs text-dark-muted mb-1">上下文精确度</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {result.metrics.context_precision.toFixed(3)}
                    </p>
                  </div>
                )}
                {result.metrics.context_recall !== null && (
                  <div className="bg-dark-sidebar p-4 rounded-lg border border-dark-border">
                    <p className="text-xs text-dark-muted mb-1">上下文召回率</p>
                    <p className="text-2xl font-bold text-orange-400">
                      {result.metrics.context_recall.toFixed(3)}
                    </p>
                  </div>
                )}
              </div>

              {/* 详细结果 */}
              {result.details && result.details.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-dark-muted mb-2">详细评估结果</h4>
                  <div className="bg-dark-sidebar rounded-lg border border-dark-border overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-dark-card">
                        <tr>
                          <th className="text-left p-3 text-dark-text">问题</th>
                          <th className="text-left p-3 text-dark-text">忠实度</th>
                          <th className="text-left p-3 text-dark-text">相关性</th>
                          <th className="text-left p-3 text-dark-text">精确度</th>
                          <th className="text-left p-3 text-dark-text">召回率</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.details.map((detail, index) => (
                          <tr key={index} className="border-t border-dark-border hover:bg-dark-hover">
                            <td className="p-3 text-dark-text max-w-xs truncate">
                              {detail.user_input}
                            </td>
                            <td className="p-3 text-primary-400">
                              {detail.faithfulness?.toFixed(3) || '-'}
                            </td>
                            <td className="p-3 text-green-400">
                              {detail.answer_relevancy?.toFixed(3) || '-'}
                            </td>
                            <td className="p-3 text-blue-400">
                              {detail.context_precision?.toFixed(3) || '-'}
                            </td>
                            <td className="p-3 text-orange-400">
                              {detail.context_recall?.toFixed(3) || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
