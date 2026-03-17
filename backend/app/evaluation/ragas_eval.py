"""
RAGAS 评估模块
使用 RAGAS 框架评估 RAG 系统的效果
"""

from typing import List, Dict, Any, Optional
import asyncio
import os

from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset

from app.config import settings
from app.models.schemas import EvaluationSample, EvaluationMetrics


class RAGASEvaluator:
    """RAGAS评估器"""
    
    # 可用的评估指标
    AVAILABLE_METRICS = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
    }
    
    def __init__(self):
        """初始化评估器"""
        # 根据配置选择 API 提供商用于评估
        if settings.default_provider == "openrouter" and settings.openrouter_api_key:
            # 使用 OpenRouter
            # 设置环境变量以确保 RAGAS 能访问 API密钥
            os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
            os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
            self.llm = ChatOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                model=settings.openrouter_model,
                temperature=0,
                timeout=30,
                max_retries=3
            )
        else:
            # 使用 DeepSeek（默认或备用）
            # 设置环境变量以确保 RAGAS 能访问 API密钥
            os.environ["OPENAI_API_KEY"] = settings.deepseek_api_key
            os.environ["OPENAI_BASE_URL"] = settings.deepseek_base_url
            self.llm = ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=settings.deepseek_model,
                temperature=0,
            )
    
    def _prepare_dataset(
        self, 
        samples: List[EvaluationSample]
    ) -> EvaluationDataset:
        """
        准备评估数据集
        
        Args:
            samples: 评估样本列表
            
        Returns:
            RAGAS评估数据集
        """
        ragas_samples = []
        
        for sample in samples:
            ragas_sample = SingleTurnSample(
                user_input=sample.question,
                response=sample.answer,
                retrieved_contexts=sample.contexts,
                reference=sample.ground_truth if sample.ground_truth else None,
            )
            ragas_samples.append(ragas_sample)
        
        return EvaluationDataset(samples=ragas_samples)
    
    def _get_metrics(self, metric_names: List[str]):
        """
        获取评估指标
        
        Args:
            metric_names: 指标名称列表
            
        Returns:
            指标列表
        """
        metrics = []
        for name in metric_names:
            if name in self.AVAILABLE_METRICS:
                metrics.append(self.AVAILABLE_METRICS[name])
        return metrics
    
    async def evaluate(
        self,
        samples: List[EvaluationSample],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行评估
        
        Args:
            samples: 评估样本列表
            metrics: 要使用的指标名称列表
            
        Returns:
            评估结果字典
        """
        if metrics is None:
            metrics = list(self.AVAILABLE_METRICS.keys())
        
        # 准备数据集
        dataset = self._prepare_dataset(samples)
        
        # 获取指标
        metric_objects = self._get_metrics(metrics)
        
        if not metric_objects:
            return {
                "success": False,
                "message": "没有有效的评估指标",
                "metrics": None,
                "details": None
            }
        
        try:
            # 执行评估
            result = evaluate(
                dataset=dataset,
                metrics=metric_objects,
                llm=self.llm,
            )
            
            # 获取详细结果（从 pandas DataFrame）
            details = None
            faithfulness_score = None
            answer_relevancy_score = None
            context_precision_score = None
            context_recall_score = None
            
            if hasattr(result, "to_pandas"):
                try:
                    df = result.to_pandas()
                    details = df.to_dict(orient="records")
                    
                    # 从 DataFrame 计算平均分
                    if 'faithfulness' in df.columns:
                        faithfulness_score = df['faithfulness'].mean()
                    if 'answer_relevancy' in df.columns:
                        answer_relevancy_score = df['answer_relevancy'].mean()
                    if 'context_precision' in df.columns:
                        context_precision_score = df['context_precision'].mean()
                    if 'context_recall' in df.columns:
                        context_recall_score = df['context_recall'].mean()
                except Exception as e:
                    print(f"解析评估结果时出错：{e}")
                    details = None
            
            # 创建指标结果对象
            metrics_result = EvaluationMetrics(
                faithfulness=faithfulness_score,
                answer_relevancy=answer_relevancy_score,
                context_precision=context_precision_score,
                context_recall=context_recall_score,
            )
            
            return {
                "success": True,
                "message": "评估完成",
                "metrics": metrics_result,
                "details": details
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"评估失败: {str(e)}",
                "metrics": None,
                "details": None
            }
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        评估单个样本
        
        Args:
            question: 问题
            answer: 回答
            contexts: 上下文列表
            ground_truth: 标准答案
            metrics: 评估指标
            
        Returns:
            评估结果
        """
        sample = EvaluationSample(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth
        )
        
        # 使用asyncio运行异步方法
        return asyncio.run(self.evaluate([sample], metrics))


async def evaluate_rag_pipeline(
    samples: List[EvaluationSample],
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    评估RAG管道
    
    Args:
        samples: 评估样本列表
        metrics: 评估指标
        
    Returns:
        评估结果
    """
    evaluator = RAGASEvaluator()
    return await evaluator.evaluate(samples, metrics)
