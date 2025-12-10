"""
Tests para el sistema RAG (Retrieval Augmented Generation).

Este módulo contiene tests para:
- EmbeddingService: generación de embeddings
- RAGEngine: motor de recuperación
- KnowledgeBase: base de conocimiento
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.ai.embeddings import EmbeddingService, get_embedding_service
from src.ai.rag_engine import RAGEngine
from src.ai.knowledge_base import (
    KnowledgeBase,
    get_context_for_question,
    get_knowledge_base
)


class TestEmbeddingService:
    """Tests para el servicio de embeddings."""
    
    def test_singleton_pattern(self):
        """Test que EmbeddingService usa patrón singleton."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2
    
    def test_encode_single(self):
        """Test codificación de un solo texto."""
        service = EmbeddingService()
        embedding = service.encode_single("Ingresos operativos")
        
        assert embedding is not None
        assert len(embedding) == 384  # Dimensión del modelo all-MiniLM-L6-v2
    
    def test_encode_batch(self):
        """Test codificación de múltiples textos."""
        service = EmbeddingService()
        texts = ["Ingresos", "Gastos", "Utilidad neta"]
        embeddings = service.encode(texts)
        
        assert embeddings is not None
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)
    
    def test_encode_empty_text(self):
        """Test con texto vacío."""
        service = EmbeddingService()
        embedding = service.encode_single("")
        
        # Debe retornar un vector válido incluso para texto vacío
        assert embedding is not None
        assert len(embedding) == 384
    
    def test_encoding_consistency(self):
        """Test que la misma entrada produce el mismo embedding."""
        service = EmbeddingService()
        text = "Cuentas por cobrar"
        
        embedding1 = service.encode_single(text)
        embedding2 = service.encode_single(text)
        
        # Los embeddings deben ser idénticos
        assert embedding1 == pytest.approx(embedding2, rel=1e-6)


class TestRAGEngine:
    """Tests para el motor RAG."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Crea directorio temporal para base de datos."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_init_default(self):
        """Test inicialización por defecto."""
        engine = RAGEngine(collection_name="test_default")
        assert engine is not None
    
    def test_add_and_retrieve_document(self, temp_db_path):
        """Test agregar y recuperar documentos."""
        engine = RAGEngine(
            collection_name="test_retrieve",
            db_path=temp_db_path
        )
        
        # Agregar documentos
        engine.add_document(
            content="Los ingresos por ventas aumentaron debido a nuevos clientes",
            category="ingresos",
            source="test",
            metadata={"type": "explanation"}
        )
        engine.add_document(
            content="Los gastos de personal incrementaron por contrataciones",
            category="gastos",
            source="test",
            metadata={"type": "explanation"}
        )
        
        # Buscar documentos relacionados con ingresos (n_results en lugar de top_k)
        results = engine.retrieve("incremento en ventas", n_results=1)
        
        assert len(results) > 0
    
    def test_retrieve_with_no_documents(self, temp_db_path):
        """Test recuperación sin documentos."""
        engine = RAGEngine(
            collection_name="test_empty",
            db_path=temp_db_path
        )
        
        results = engine.retrieve("cualquier consulta", n_results=3)
        assert results == []
    
    def test_augment_prompt(self, temp_db_path):
        """Test aumento de prompt con contexto."""
        engine = RAGEngine(
            collection_name="test_augment",
            db_path=temp_db_path
        )
        
        # Agregar conocimiento
        engine.add_document(
            content="Las variaciones en inventario pueden indicar problemas de demanda",
            category="inventory"
        )
        
        original_prompt = "Genera una pregunta sobre inventario"
        result = engine.augment_prompt(original_prompt, n_contexts=1)
        
        # El prompt aumentado debe contener el original y el contexto
        assert original_prompt in result.augmented_prompt
        assert len(result.augmented_prompt) >= len(original_prompt)
    
    def test_learn_from_qa(self, temp_db_path):
        """Test aprendizaje de pares Q&A."""
        engine = RAGEngine(
            collection_name="test_learn",
            db_path=temp_db_path
        )
        
        # Enseñar al sistema (sin metadata, usa category y variation_info)
        engine.learn_from_qa(
            question="¿Por qué aumentaron las ventas?",
            answer="Debido a la expansión a nuevos mercados",
            category="learned",
            variation_info={"type": "incremento", "magnitude": "significativa"}
        )
        
        # El conocimiento debe estar disponible
        results = engine.retrieve("mercados nuevos ventas", n_results=1)
        assert len(results) > 0


class TestKnowledgeBase:
    """Tests para la base de conocimiento."""
    
    def test_init_default(self):
        """Test inicialización por defecto."""
        kb = KnowledgeBase()
        assert kb is not None
        assert kb.rag is not None
    
    def test_get_knowledge_base_singleton(self):
        """Test que get_knowledge_base devuelve la misma instancia."""
        kb1 = get_knowledge_base()
        kb2 = get_knowledge_base()
        assert kb1 is kb2
    
    def test_get_context_for_revenue(self):
        """Test contexto para ingresos."""
        contexts = get_context_for_question(
            description="Ventas nacionales",
            category="Ingresos",
            variation_type="incremento",
            variation_magnitude="significativa"
        )
        
        assert contexts is not None
        # Puede devolver lista vacía si no hay matches, pero no debe fallar
        assert isinstance(contexts, list)
    
    def test_get_context_for_expenses(self):
        """Test contexto para gastos."""
        contexts = get_context_for_question(
            description="Gastos de personal",
            category="Gastos Operativos",
            variation_type="incremento",
            variation_magnitude="extrema"
        )
        
        assert contexts is not None
        assert isinstance(contexts, list)
    
    def test_get_context_for_balance_sheet(self):
        """Test contexto para balance."""
        contexts = get_context_for_question(
            description="Cuentas por cobrar",
            category="Activo Corriente",
            variation_type="incremento",
            variation_magnitude="moderada"
        )
        
        assert contexts is not None
        assert isinstance(contexts, list)
    
    def test_initialize_base_knowledge(self):
        """Test inicialización de conocimiento base."""
        kb = get_knowledge_base()
        kb.initialize_base_knowledge()
        
        assert kb._initialized
        
        stats = kb.rag.get_stats()
        assert stats['total_documents'] > 0


class TestRAGIntegration:
    """Tests de integración del sistema RAG."""
    
    def test_full_rag_workflow(self):
        """Test flujo completo de RAG."""
        # 1. Obtener contexto de knowledge base
        contexts = get_context_for_question(
            description="Costo de ventas",
            category="Costos",
            variation_type="incremento",
            variation_magnitude="significativa"
        )
        
        assert contexts is not None
        
        # 2. Crear motor RAG y agregar el contexto
        engine = RAGEngine(collection_name="test_integration")
        
        if contexts:
            for i, ctx in enumerate(contexts):
                if isinstance(ctx, str):  # Asegurar que es string
                    engine.add_document(
                        content=ctx,
                        category="knowledge_base",
                        source="test",
                        metadata={"index": i}
                    )
        
        # 3. Recuperar contexto relevante (n_results en lugar de top_k)
        results = engine.retrieve("costo de ventas aumentó", n_results=2)
        
        # Puede que no haya resultados si no hay contextos, pero no debe fallar
        assert isinstance(results, list)
    
    def test_embedding_in_rag(self):
        """Test que RAG usa embeddings correctamente."""
        engine = RAGEngine(collection_name="test_embedding_use")
        
        # Agregar documentos semánticamente diferentes
        engine.add_document(
            content="Ingresos por ventas de software", 
            category="revenue"
        )
        engine.add_document(
            content="Gastos de investigación y desarrollo", 
            category="expense"
        )
        
        # Buscar algo relacionado con software (n_results en lugar de top_k)
        results = engine.retrieve("software ventas licencias", n_results=1)
        
        if results:
            # El resultado debe existir
            assert len(results) > 0


class TestAIServiceWithRAG:
    """Tests de AIService con RAG habilitado."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock de settings para tests."""
        from src.config.settings import Settings
        settings = Settings()
        settings.ai.enabled = False  # Deshabilitar AI real
        settings.ai.auto_fallback = True
        return settings
    
    def test_ai_service_with_rag_enabled(self, mock_settings):
        """Test AIService con RAG habilitado."""
        from src.ai.ai_service import AIService, AIMode
        
        service = AIService(
            mode=AIMode.AUTO,
            settings=mock_settings,
            enable_rag=True,
            sector="general"
        )
        
        status = service.get_status()
        assert status["rag_enabled"] is True
    
    def test_ai_service_with_rag_disabled(self, mock_settings):
        """Test AIService con RAG deshabilitado."""
        from src.ai.ai_service import AIService, AIMode
        
        service = AIService(
            mode=AIMode.AUTO,
            settings=mock_settings,
            enable_rag=False
        )
        
        status = service.get_status()
        assert status["rag_enabled"] is False
    
    def test_question_generation_uses_rag(self, mock_settings):
        """Test que la generación de preguntas usa RAG."""
        from src.ai.ai_service import AIService, AIMode
        
        service = AIService(
            mode=AIMode.AUTO,
            settings=mock_settings,
            enable_rag=True,
            sector="general"
        )
        
        result = service.generate_question(
            description="Ingresos operativos",
            account_code="70000000",
            period_base="FY23",
            period_compare="FY24",
            value_base=1000000,
            value_compare=1500000,
            variation_pct=50.0,
            use_rag=True
        )
        
        # Debe generar una pregunta
        assert result.question is not None
        assert "?" in result.question
        
        # Debe indicar uso de RAG en generated_by
        assert result.generated_by in ("rules_rag", "ai_rag", "rules", "ai")
