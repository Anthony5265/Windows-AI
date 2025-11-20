"""
RAG Evaluation Plugin
Evaluate RAG system performance with various metrics
"""

from typing import Dict, Any, Optional, List


class RAGEvaluationPlugin:
    """Plugin for evaluating RAG system quality"""

    name = "rag_evaluation"
    version = "1.0.0"
    description = "Evaluate RAG performance with retrieval and generation metrics"
    author = "Windows AI Team"

    def __init__(self):
        self.evaluation_history = []
        self.benchmarks = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the RAG Evaluation plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing RAG Evaluation plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a RAG Evaluation action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "evaluate_retrieval":
                return self._evaluate_retrieval(params)
            elif action == "evaluate_generation":
                return self._evaluate_generation(params)
            elif action == "evaluate_end_to_end":
                return self._evaluate_end_to_end(params)
            elif action == "calculate_metrics":
                return self._calculate_metrics(params)
            elif action == "benchmark":
                return self._benchmark(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _evaluate_retrieval(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate retrieval quality"""
        query = params.get("query", "")
        retrieved_docs = params.get("retrieved_docs", [])
        relevant_docs = params.get("relevant_docs", [])
        k = params.get("k", len(retrieved_docs))

        # Calculate retrieval metrics
        retrieved_ids = set([doc.get("id") or doc.get("doc_id") for doc in retrieved_docs[:k]])
        relevant_ids = set(relevant_docs)

        # Precision@K
        true_positives = len(retrieved_ids & relevant_ids)
        precision = true_positives / k if k > 0 else 0.0

        # Recall@K
        recall = true_positives / len(relevant_ids) if relevant_ids else 0.0

        # F1@K
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, doc in enumerate(retrieved_docs[:k], 1):
            doc_id = doc.get("id") or doc.get("doc_id")
            if doc_id in relevant_ids:
                mrr = 1.0 / i
                break

        # NDCG (simplified)
        dcg = 0.0
        idcg = sum(1.0 / (i + 1) for i in range(min(len(relevant_ids), k)))

        for i, doc in enumerate(retrieved_docs[:k]):
            doc_id = doc.get("id") or doc.get("doc_id")
            if doc_id in relevant_ids:
                dcg += 1.0 / (i + 2)  # i+2 because enumerate starts at 0

        ndcg = dcg / idcg if idcg > 0 else 0.0

        # MAP (Mean Average Precision)
        avg_precision = 0.0
        num_relevant_seen = 0

        for i, doc in enumerate(retrieved_docs[:k], 1):
            doc_id = doc.get("id") or doc.get("doc_id")
            if doc_id in relevant_ids:
                num_relevant_seen += 1
                precision_at_i = num_relevant_seen / i
                avg_precision += precision_at_i

        map_score = avg_precision / len(relevant_ids) if relevant_ids else 0.0

        metrics = {
            "precision@k": round(precision, 4),
            "recall@k": round(recall, 4),
            "f1@k": round(f1, 4),
            "mrr": round(mrr, 4),
            "ndcg@k": round(ndcg, 4),
            "map": round(map_score, 4)
        }

        return {
            "success": True,
            "query": query,
            "k": k,
            "metrics": metrics,
            "num_retrieved": len(retrieved_docs),
            "num_relevant": len(relevant_ids),
            "true_positives": true_positives
        }

    def _evaluate_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate generated answer quality"""
        query = params.get("query", "")
        generated_answer = params.get("generated_answer", "")
        reference_answer = params.get("reference_answer", "")
        context = params.get("context", [])

        metrics = {}

        # Faithfulness (answer grounded in context)
        faithfulness = self._calculate_faithfulness(generated_answer, context)
        metrics["faithfulness"] = round(faithfulness, 4)

        # Answer relevance to query
        answer_relevance = self._calculate_relevance(query, generated_answer)
        metrics["answer_relevance"] = round(answer_relevance, 4)

        # Context relevance to query
        context_relevance = self._calculate_context_relevance(query, context)
        metrics["context_relevance"] = round(context_relevance, 4)

        # Answer similarity to reference (if provided)
        if reference_answer:
            similarity = self._calculate_similarity(generated_answer, reference_answer)
            metrics["answer_similarity"] = round(similarity, 4)

        # Answer completeness
        completeness = self._calculate_completeness(generated_answer, reference_answer)
        metrics["completeness"] = round(completeness, 4)

        # Answer conciseness
        conciseness = self._calculate_conciseness(generated_answer)
        metrics["conciseness"] = round(conciseness, 4)

        return {
            "success": True,
            "query": query,
            "metrics": metrics,
            "generated_answer_length": len(generated_answer),
            "context_docs": len(context)
        }

    def _evaluate_end_to_end(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate complete RAG pipeline"""
        query = params.get("query", "")
        retrieved_docs = params.get("retrieved_docs", [])
        relevant_docs = params.get("relevant_docs", [])
        generated_answer = params.get("generated_answer", "")
        reference_answer = params.get("reference_answer", "")

        # Evaluate retrieval
        retrieval_eval = self._evaluate_retrieval({
            "query": query,
            "retrieved_docs": retrieved_docs,
            "relevant_docs": relevant_docs
        })

        # Evaluate generation
        generation_eval = self._evaluate_generation({
            "query": query,
            "generated_answer": generated_answer,
            "reference_answer": reference_answer,
            "context": retrieved_docs
        })

        # Combined score
        retrieval_score = (
            retrieval_eval["metrics"]["precision@k"] * 0.3 +
            retrieval_eval["metrics"]["recall@k"] * 0.3 +
            retrieval_eval["metrics"]["ndcg@k"] * 0.4
        )

        generation_score = (
            generation_eval["metrics"]["faithfulness"] * 0.4 +
            generation_eval["metrics"]["answer_relevance"] * 0.4 +
            generation_eval["metrics"].get("answer_similarity", 0.0) * 0.2
        )

        overall_score = (retrieval_score * 0.4 + generation_score * 0.6)

        return {
            "success": True,
            "query": query,
            "retrieval_metrics": retrieval_eval["metrics"],
            "generation_metrics": generation_eval["metrics"],
            "retrieval_score": round(retrieval_score, 4),
            "generation_score": round(generation_score, 4),
            "overall_score": round(overall_score, 4)
        }

    def _calculate_faithfulness(self, answer: str, context: List) -> float:
        """Calculate how well answer is grounded in context"""
        if not context or not answer:
            return 0.0

        # Simplified: check if answer words appear in context
        answer_words = set(answer.lower().split())
        context_text = " ".join([str(doc.get("text", "")) for doc in context]).lower()
        context_words = set(context_text.split())

        if not answer_words:
            return 0.0

        overlap = len(answer_words & context_words) / len(answer_words)
        return min(overlap * 1.2, 1.0)  # Slight boost

    def _calculate_relevance(self, query: str, answer: str) -> float:
        """Calculate relevance of answer to query"""
        if not query or not answer:
            return 0.0

        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words & answer_words) / len(query_words)
        return min(overlap * 1.3, 1.0)

    def _calculate_context_relevance(self, query: str, context: List) -> float:
        """Calculate relevance of context to query"""
        if not context or not query:
            return 0.0

        query_words = set(query.lower().split())
        relevance_scores = []

        for doc in context:
            doc_text = str(doc.get("text", "")).lower()
            doc_words = set(doc_text.split())

            if not doc_words:
                continue

            overlap = len(query_words & doc_words) / len(query_words)
            relevance_scores.append(overlap)

        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_completeness(self, answer: str, reference: str) -> float:
        """Calculate how complete the answer is"""
        if not reference or not answer:
            return 0.5

        ref_words = set(reference.lower().split())
        ans_words = set(answer.lower().split())

        if not ref_words:
            return 1.0

        coverage = len(ref_words & ans_words) / len(ref_words)
        return coverage

    def _calculate_conciseness(self, answer: str) -> float:
        """Calculate conciseness of answer"""
        if not answer:
            return 0.0

        # Ideal answer length: 50-200 words
        word_count = len(answer.split())

        if 50 <= word_count <= 200:
            return 1.0
        elif word_count < 50:
            return word_count / 50
        else:
            return max(0.5, 200 / word_count)

    def _calculate_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate custom metrics"""
        metric_type = params.get("type", "retrieval")
        data = params.get("data", {})

        if metric_type == "retrieval":
            return self._evaluate_retrieval(data)
        elif metric_type == "generation":
            return self._evaluate_generation(data)
        elif metric_type == "end_to_end":
            return self._evaluate_end_to_end(data)
        else:
            return {"success": False, "error": f"Unknown metric type: {metric_type}"}

    def _benchmark(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run benchmark on dataset"""
        dataset = params.get("dataset", [])
        benchmark_name = params.get("name", "custom_benchmark")

        results = []
        aggregate_metrics = {
            "precision": [],
            "recall": [],
            "f1": [],
            "ndcg": [],
            "faithfulness": [],
            "answer_relevance": []
        }

        for sample in dataset:
            # Evaluate sample
            eval_result = self._evaluate_end_to_end(sample)

            if eval_result["success"]:
                results.append(eval_result)

                # Collect metrics
                ret_metrics = eval_result["retrieval_metrics"]
                gen_metrics = eval_result["generation_metrics"]

                aggregate_metrics["precision"].append(ret_metrics.get("precision@k", 0))
                aggregate_metrics["recall"].append(ret_metrics.get("recall@k", 0))
                aggregate_metrics["f1"].append(ret_metrics.get("f1@k", 0))
                aggregate_metrics["ndcg"].append(ret_metrics.get("ndcg@k", 0))
                aggregate_metrics["faithfulness"].append(gen_metrics.get("faithfulness", 0))
                aggregate_metrics["answer_relevance"].append(gen_metrics.get("answer_relevance", 0))

        # Calculate averages
        avg_metrics = {
            metric: round(sum(values) / len(values), 4) if values else 0.0
            for metric, values in aggregate_metrics.items()
        }

        benchmark_result = {
            "name": benchmark_name,
            "num_samples": len(dataset),
            "num_evaluated": len(results),
            "average_metrics": avg_metrics,
            "timestamp": "now"
        }

        self.benchmarks[benchmark_name] = benchmark_result

        return {
            "success": True,
            "benchmark": benchmark_result,
            "individual_results": results
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.evaluation_history = []
        self.benchmarks = {}
        return True
