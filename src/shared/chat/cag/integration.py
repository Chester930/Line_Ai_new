class CAGIntegrator:
    def __init__(self, rag_system, context_manager):
        self.rag = rag_system
        self.context = context_manager
        
    async def process_query(self, query: str) -> dict:
        """整合 RAG 與上下文處理流程"""
        # 新增上下文感知檢索
        enriched_query = await self.context.enrich_query(query)
        search_results = await self.rag.retrieve(enriched_query)
        
        # 加入優先級過濾
        prioritized = self._apply_priority(search_results)
        
        # 生成最終回應
        return await self._generate_response(prioritized)
    
    def _apply_priority(self, results: list) -> list:
        """根據上下文優先級過濾結果"""
        return sorted(
            results, 
            key=lambda x: x['score'] * self.context.get_priority(x['topic']),
            reverse=True
        )[:5] 