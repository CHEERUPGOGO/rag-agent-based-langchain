"""
评估路由模块
处理RAG系统评估请求
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import EvaluationRequest, EvaluationResponse, EvaluationSample
from app.evaluation import evaluate_rag_pipeline

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    """
    评估RAG系统效果
    
    Args:
        request: 评估请求
        
    Returns:
        评估结果
    """
    try:
        # 转换样本格式
        samples = [
            EvaluationSample(
                question=sample.question,
                answer=sample.answer,
                contexts=sample.contexts,
                ground_truth=sample.ground_truth
            )
            for sample in request.samples
        ]
        
        # 执行评估
        result = await evaluate_rag_pipeline(samples, request.metrics)
        
        return EvaluationResponse(
            success=result["success"],
            message=result["message"],
            metrics=result.get("metrics"),
            details=result.get("details")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_available_metrics():
    """
    获取可用的评估指标列表
    
    Returns:
        评估指标信息
    """
    return {
        "metrics": [
            {
                "name": "faithfulness",
                "description": "忠实度 - 评估答案是否忠实于提供的上下文"
            },
            {
                "name": "answer_relevancy",
                "description": "答案相关性 - 评估答案与问题的相关程度"
            },
            {
                "name": "context_precision",
                "description": "上下文精确度 - 评估检索到的上下文与问题的相关性"
            },
            {
                "name": "context_recall",
                "description": "上下文召回率 - 评估是否检索到所有相关的上下文"
            }
        ]
    }


@router.post("/evaluate/quick")
async def quick_evaluate(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str = None
):
    """
    快速评估单个样本
    
    Args:
        question: 问题
        answer: 回答
        contexts: 上下文列表
        ground_truth: 标准答案（可选）
        
    Returns:
        评估结果
    """
    try:
        sample = EvaluationSample(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth
        )
        
        result = await evaluate_rag_pipeline([sample])
        
        return EvaluationResponse(
            success=result["success"],
            message=result["message"],
            metrics=result.get("metrics"),
            details=result.get("details")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
