"""
Tests para el módulo de IA.

Incluye tests para:
- OllamaClient
- AIService
- PromptGenerator
- Modo sin IA
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Importar módulos a testear
from src.ai.ollama_client import OllamaClient, OllamaResponse
from src.ai.ai_service import AIService, AIMode, QuestionResult
from src.ai.prompts import PromptGenerator, PromptTemplate, PromptType


class TestOllamaClient:
    """Tests para el cliente Ollama."""
    
    def test_init_default_values(self):
        """Test inicialización con valores por defecto."""
        client = OllamaClient()
        
        assert client.model == "llama3.2"
        assert client.timeout == 120
        assert client.max_retries == 3
        assert "localhost" in client.base_url
    
    def test_init_custom_values(self):
        """Test inicialización con valores personalizados."""
        client = OllamaClient(
            host="http://192.168.1.100",
            port=8080,
            model="mistral",
            timeout=60
        )
        
        assert "192.168.1.100:8080" in client.base_url
        assert client.model == "mistral"
        assert client.timeout == 60
    
    def test_api_urls(self):
        """Test generación de URLs de API."""
        client = OllamaClient(host="http://localhost", port=11434)
        
        assert "/api/generate" in client.api_url
        assert "/api/tags" in client.models_url
        assert "/api/chat" in client.chat_url
    
    @patch('src.ai.ollama_client.HTTPX_AVAILABLE', False)
    @patch('src.ai.ollama_client.REQUESTS_AVAILABLE', False)
    def test_is_available_no_http_client(self):
        """Test que retorna False si no hay cliente HTTP."""
        client = OllamaClient()
        # Debería manejar la ausencia de cliente HTTP
        assert client.is_available() is False


class TestOllamaResponse:
    """Tests para la clase OllamaResponse."""
    
    def test_create_response(self):
        """Test creación de respuesta."""
        response = OllamaResponse(
            text="Esta es la respuesta",
            model="llama3.2",
            done=True,
            total_duration=1_000_000_000,  # 1 segundo en nanosegundos
            eval_count=50
        )
        
        assert response.text == "Esta es la respuesta"
        assert response.model == "llama3.2"
        assert response.done is True
        assert response.tokens_generated == 50
    
    def test_generation_time_seconds(self):
        """Test conversión de tiempo de generación."""
        response = OllamaResponse(
            text="Test",
            model="test",
            done=True,
            total_duration=2_500_000_000  # 2.5 segundos
        )
        
        assert response.generation_time_seconds == 2.5
    
    def test_generation_time_zero(self):
        """Test tiempo cero si no hay duración."""
        response = OllamaResponse(
            text="Test",
            model="test",
            done=True,
            total_duration=None
        )
        
        assert response.generation_time_seconds == 0.0


class TestPromptGenerator:
    """Tests para el generador de prompts."""
    
    @pytest.fixture
    def generator(self):
        """Fixture con generador de prompts."""
        return PromptGenerator()
    
    def test_generate_question_prompt(self, generator):
        """Test generación de prompt para preguntas."""
        prompts = generator.generate_question_prompt(
            description="Ventas nacionales",
            account_code="70100000",
            period_base="FY23",
            period_compare="FY24",
            value_base=1000000,
            value_compare=1500000,
            variation_abs=500000,
            variation_pct=50.0,
            variation_type="aumento_significativo",
            category="Revenue"
        )
        
        assert 'system' in prompts
        assert 'user' in prompts
        assert "Ventas nacionales" in prompts['user']
        assert "70100000" in prompts['user']
        assert "FY23" in prompts['user']
        assert "FY24" in prompts['user']
    
    def test_generate_analysis_prompt(self, generator):
        """Test generación de prompt de análisis."""
        prompts = generator.generate_analysis_prompt(
            description="Gastos de personal",
            account_type="gasto",
            period_base="FY23",
            period_compare="FY24",
            value_base=-100000,
            value_compare=-150000,
            variation_pct=50.0
        )
        
        assert 'system' in prompts
        assert 'user' in prompts
        assert "Gastos de personal" in prompts['user']
    
    def test_get_rule_based_question_increase(self):
        """Test pregunta basada en reglas para incremento."""
        question = PromptGenerator.get_rule_based_question(
            description="Ventas",
            variation_type="aumento_significativo",
            variation_pct=50.0,
            period_base="FY23",
            period_compare="FY24"
        )
        
        assert "incremento" in question.lower()
        assert "50.0%" in question
        assert "Ventas" in question
    
    def test_get_rule_based_question_decrease(self):
        """Test pregunta basada en reglas para disminución."""
        question = PromptGenerator.get_rule_based_question(
            description="Gastos",
            variation_type="disminucion_significativa",
            variation_pct=-30.0,
            period_base="FY23",
            period_compare="FY24"
        )
        
        assert "reducción" in question.lower()
        assert "30.0%" in question
    
    def test_get_rule_based_question_new_item(self):
        """Test pregunta basada en reglas para item nuevo."""
        question = PromptGenerator.get_rule_based_question(
            description="Nuevo concepto",
            variation_type="nuevo",
            variation_pct=100.0,
            period_base="FY23",
            period_compare="FY24"
        )
        
        assert "nuevo" in question.lower()


class TestAIService:
    """Tests para el servicio de IA."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock de Settings."""
        settings = Mock()
        settings.ai = Mock()
        settings.ai.enabled = True
        settings.ai.provider = "ollama"
        settings.ai.host = "http://localhost"
        settings.ai.port = 11434
        settings.ai.default_model = "llama3.2"
        settings.ai.temperature = 0.7
        settings.ai.request_timeout = 120
        settings.ai.max_retries = 3
        settings.ai.retry_delay = 1.0
        settings.ai.auto_fallback = True
        return settings
    
    def test_init_rule_based_mode(self, mock_settings):
        """Test inicialización en modo reglas."""
        service = AIService(mode=AIMode.RULE_BASED, settings=mock_settings)
        
        assert service.mode == AIMode.RULE_BASED
        assert service.is_ai_enabled is False
    
    def test_generate_question_rules(self, mock_settings):
        """Test generación de pregunta con reglas."""
        service = AIService(mode=AIMode.RULE_BASED, settings=mock_settings)
        
        result = service.generate_question(
            description="Ventas nacionales",
            account_code="70100000",
            period_base="FY23",
            period_compare="FY24",
            value_base=1000000,
            value_compare=1500000,
            variation_pct=50.0,
            variation_type="aumento_significativo"
        )
        
        assert isinstance(result, QuestionResult)
        # Acepta 'rules' o 'rules_rag' si RAG está habilitado
        assert result.generated_by in ("rules", "rules_rag")
        assert result.question is not None
        assert len(result.question) > 0
        assert "?" in result.question
    
    def test_generate_question_force_rules(self, mock_settings):
        """Test forzar modo reglas."""
        service = AIService(mode=AIMode.FULL_AI, settings=mock_settings)
        
        result = service.generate_question(
            description="Gastos",
            account_code="62000000",
            period_base="FY23",
            period_compare="FY24",
            value_base=-100000,
            value_compare=-150000,
            variation_pct=50.0,
            force_rules=True
        )
        
        # Acepta 'rules' o 'rules_rag' si RAG está habilitado
        assert result.generated_by in ("rules", "rules_rag")
    
    def test_get_status_disabled(self, mock_settings):
        """Test estado cuando está deshabilitado."""
        mock_settings.ai.enabled = False
        service = AIService(mode=AIMode.AUTO, settings=mock_settings)
        
        status = service.get_status()
        
        assert "mode" in status
        assert "ai_enabled" in status
    
    def test_generate_batch_questions(self, mock_settings):
        """Test generación de múltiples preguntas."""
        service = AIService(mode=AIMode.RULE_BASED, settings=mock_settings)
        
        variations = [
            {
                "description": "Ventas",
                "account_code": "70100000",
                "period_base": "FY23",
                "period_compare": "FY24",
                "value_base": 1000000,
                "value_compare": 1500000,
                "variation_pct": 50.0,
                "variation_type": "aumento"
            },
            {
                "description": "Gastos",
                "account_code": "62000000",
                "period_base": "FY23",
                "period_compare": "FY24",
                "value_base": -100000,
                "value_compare": -80000,
                "variation_pct": -20.0,
                "variation_type": "disminucion"
            }
        ]
        
        results = service.generate_batch_questions(variations)
        
        assert len(results) == 2
        assert all(isinstance(r, QuestionResult) for r in results)


class TestQuestionResult:
    """Tests para QuestionResult."""
    
    def test_create_result(self):
        """Test creación de resultado."""
        result = QuestionResult(
            question="¿Por qué aumentaron las ventas?",
            generated_by="ai",
            confidence=0.9,
            model_used="llama3.2",
            processing_time=1.5
        )
        
        assert result.question == "¿Por qué aumentaron las ventas?"
        assert result.generated_by == "ai"
        assert result.confidence == 0.9
        assert result.model_used == "llama3.2"
    
    def test_result_without_ai(self):
        """Test resultado sin IA."""
        result = QuestionResult(
            question="Pregunta generada por reglas",
            generated_by="rules",
            confidence=0.7
        )
        
        assert result.model_used is None
        assert result.processing_time is None


class TestPromptTemplate:
    """Tests para PromptTemplate."""
    
    def test_create_template(self):
        """Test creación de template."""
        template = PromptTemplate(
            name="test_template",
            prompt_type=PromptType.QUESTION_GENERATION,
            system_prompt="Eres un asistente.",
            user_prompt="Analiza $concepto con valor $valor"
        )
        
        assert template.name == "test_template"
        assert template.prompt_type == PromptType.QUESTION_GENERATION
    
    def test_format_template(self):
        """Test formateo de template."""
        template = PromptTemplate(
            name="test",
            prompt_type=PromptType.QUESTION_GENERATION,
            system_prompt="Sistema: $role",
            user_prompt="Concepto: $concepto, Valor: $valor"
        )
        
        result = template.format(
            role="analista",
            concepto="Ventas",
            valor="1000000"
        )
        
        assert result['system'] == "Sistema: analista"
        assert "Ventas" in result['user']
        assert "1000000" in result['user']


class TestAIModeIntegration:
    """Tests de integración para diferentes modos de IA."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock de Settings."""
        settings = Mock()
        settings.ai = Mock()
        settings.ai.enabled = True
        settings.ai.provider = "ollama"
        settings.ai.host = "http://localhost"
        settings.ai.port = 11434
        settings.ai.default_model = "llama3.2"
        settings.ai.temperature = 0.7
        settings.ai.request_timeout = 120
        settings.ai.max_retries = 3
        settings.ai.retry_delay = 1.0
        settings.ai.auto_fallback = True
        return settings
    
    def test_auto_mode_fallback_to_rules(self, mock_settings):
        """Test que modo AUTO hace fallback a reglas si Ollama no está."""
        # En este test, Ollama no estará disponible
        service = AIService(mode=AIMode.AUTO, settings=mock_settings)
        
        # Debería usar reglas porque Ollama no está corriendo
        result = service.generate_question(
            description="Test",
            account_code="70000000",
            period_base="FY23",
            period_compare="FY24",
            value_base=100,
            value_compare=200,
            variation_pct=100.0
        )
        
        # Debería generar con reglas ya que Ollama no está disponible
        assert result.question is not None
        assert len(result.question) > 0
    
    def test_disabled_ai_uses_rules(self, mock_settings):
        """Test que IA deshabilitada usa reglas."""
        mock_settings.ai.enabled = False
        
        service = AIService(mode=AIMode.AUTO, settings=mock_settings)
        
        assert service.mode == AIMode.RULE_BASED
        
        result = service.generate_question(
            description="Concepto test",
            account_code="70000000",
            period_base="FY23",
            period_compare="FY24",
            value_base=100,
            value_compare=150,
            variation_pct=50.0
        )
        
        # Acepta 'rules' o 'rules_rag' si RAG está habilitado
        assert result.generated_by in ("rules", "rules_rag")
