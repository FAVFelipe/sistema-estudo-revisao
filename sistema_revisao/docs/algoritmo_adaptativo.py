#!/usr/bin/env python3
"""
Algoritmo Adaptativo de Repetição Espaçada
Sistema Inteligente de Revisão de Estudos

Este módulo implementa um algoritmo de repetição espaçada adaptativo
baseado no SM-2, mas expandido com:
- Nível de confiança do aluno
- Tempo de resposta
- Modo intensivo (pré-prova)
- Histórico de desempenho

Referências Acadêmicas:
- Ebbinghaus, H. (1885). Memory: A Contribution to Experimental Psychology
- Wozniak, P. A., & Gorzelanczyk, E. J. (1994). SuperMemo Algorithm SM-2
- Cepeda et al. (2006). Distributed practice in verbal recall tasks

Autor: Sistema de Revisão Adaptativa
Data: 2025
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict
import math


class AlgoritmoAdaptativo:
    """
    Classe que implementa o algoritmo adaptativo de repetição espaçada.
    
    Combina múltiplos fatores para calcular o intervalo ideal:
    - Quality: Qualidade da resposta (0-5)
    - Confidence: Nível de confiança (1-5)
    - Response Time: Tempo de resposta
    - History: Histórico de desempenho
    - Intensive Mode: Modo pré-prova ativado
    """
    
    # Constantes do algoritmo
    EF_MIN = 1.3  # Fator de facilidade mínimo
    EF_MAX = 2.5  # Fator de facilidade máximo
    EF_INICIAL = 2.5  # Fator inicial
    
    # Intervalos base (em dias)
    INTERVALO_ERRO = 1  # Quando erra completamente
    INTERVALO_DUVIDA = 3  # Quando acerta com dúvida
    INTERVALO_BOM = 7  # Quando acerta bem
    INTERVALO_PERFEITO = 14  # Quando acerta perfeitamente
    
    # Modificadores para modo intensivo
    FATOR_INTENSIVO = 0.5  # Reduz intervalos pela metade
    
    def __init__(self, modo_intensivo: bool = False):
        """
        Inicializa o algoritmo.
        
        Args:
            modo_intensivo: Se True, reduz intervalos para revisão intensiva
        """
        self.modo_intensivo = modo_intensivo
    
    def calcular_proxima_revisao(
        self,
        quality: int,
        nivel_confianca: int,
        ef: float = EF_INICIAL,
        interval: int = 1,
        repetition: int = 0,
        tempo_resposta: int = None,
        tempo_esperado: int = 60
    ) -> Tuple[float, int, int]:
        """
        Calcula a próxima revisão baseada em múltiplos fatores.
        
        Args:
            quality: Qualidade da resposta (0-5)
                0-2: Não lembrou
                3: Lembrou com dificuldade
                4: Lembrou bem
                5: Lembrou perfeitamente
            nivel_confianca: Confiança do aluno (1-5)
                1: Muito inseguro
                2: Inseguro
                3: Neutro
                4: Confiante
                5: Muito confiante
            ef: Fator de facilidade atual
            interval: Intervalo atual em dias
            repetition: Número de repetições consecutivas corretas
            tempo_resposta: Tempo de resposta em segundos
            tempo_esperado: Tempo esperado para resposta (padrão 60s)
        
        Returns:
            Tupla (novo_ef, novo_intervalo, nova_repetition)
        
        Exemplo:
            >>> alg = AlgoritmoAdaptativo()
            >>> ef, intervalo, rep = alg.calcular_proxima_revisao(
            ...     quality=4, nivel_confianca=3, ef=2.5, interval=1, repetition=0
            ... )
            >>> print(f"Próxima revisão em {intervalo} dias")
        """
        
        # 1. CALCULAR NOVO EF baseado em quality e confiança
        novo_ef = self._calcular_ef(quality, nivel_confianca, ef)
        
        # 2. DETERMINAR SE RESETOU (errou)
        if quality < 3:
            # Resetou: volta ao início
            nova_repetition = 0
            novo_intervalo = self.INTERVALO_ERRO
        else:
            # Acertou: avança
            nova_repetition = repetition + 1
            novo_intervalo = self._calcular_intervalo(
                quality, nivel_confianca, novo_ef, interval, nova_repetition
            )
        
        # 3. AJUSTAR POR TEMPO DE RESPOSTA (se fornecido)
        if tempo_resposta is not None:
            novo_intervalo = self._ajustar_por_tempo(
                novo_intervalo, tempo_resposta, tempo_esperado
            )
        
        # 4. APLICAR MODO INTENSIVO (se ativado)
        if self.modo_intensivo:
            novo_intervalo = max(1, int(novo_intervalo * self.FATOR_INTENSIVO))
        
        # 5. GARANTIR LIMITES
        novo_intervalo = max(1, novo_intervalo)  # Mínimo 1 dia
        novo_ef = max(self.EF_MIN, min(self.EF_MAX, novo_ef))
        
        return novo_ef, novo_intervalo, nova_repetition
    
    def _calcular_ef(self, quality: int, confianca: int, ef_atual: float) -> float:
        """
        Calcula o novo fator de facilidade (EF).
        
        Combina quality (0-5) e confiança (1-5) para ajustar o EF.
        
        Fórmula adaptada do SM-2:
        EF' = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        Modificação: Adiciona peso da confiança
        """
        # Fórmula SM-2 original
        delta_quality = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        
        # Adicionar peso da confiança (normalizado para -0.1 a +0.1)
        delta_confianca = (confianca - 3) * 0.05  # -0.1, -0.05, 0, +0.05, +0.1
        
        # Combinar deltas
        delta_total = delta_quality + delta_confianca
        
        novo_ef = ef_atual + delta_total
        
        return novo_ef
    
    def _calcular_intervalo(
        self,
        quality: int,
        confianca: int,
        ef: float,
        interval_atual: int,
        repetition: int
    ) -> int:
        """
        Calcula o intervalo em dias até a próxima revisão.
        
        Usa uma abordagem híbrida:
        - Primeiras repetições: intervalos fixos baseados em quality
        - Repetições subsequentes: crescimento exponencial com EF
        """
        
        # Primeiras 3 repetições: intervalos baseados em quality e confiança
        if repetition <= 3:
            # Mapear quality + confiança para intervalo base
            if quality == 5 and confianca >= 4:
                intervalo = self.INTERVALO_PERFEITO
            elif quality >= 4 and confianca >= 3:
                intervalo = self.INTERVALO_BOM
            elif quality >= 3:
                intervalo = self.INTERVALO_DUVIDA
            else:
                intervalo = self.INTERVALO_ERRO
            
            # Ajustar por repetição
            intervalo = intervalo * (repetition + 1) // 2
        else:
            # Repetições avançadas: crescimento exponencial
            intervalo = int(interval_atual * ef)
        
        return intervalo
    
    def _ajustar_por_tempo(
        self,
        intervalo: int,
        tempo_resposta: int,
        tempo_esperado: int
    ) -> int:
        """
        Ajusta o intervalo baseado no tempo de resposta.
        
        Se respondeu muito rápido: pode aumentar intervalo (domínio)
        Se respondeu muito devagar: pode reduzir intervalo (dificuldade)
        """
        
        ratio = tempo_resposta / tempo_esperado
        
        if ratio < 0.5:
            # Respondeu muito rápido (< 50% do tempo esperado)
            # Aumenta intervalo em até 20%
            fator = 1.2
        elif ratio > 2.0:
            # Respondeu muito devagar (> 200% do tempo esperado)
            # Reduz intervalo em até 20%
            fator = 0.8
        else:
            # Tempo normal
            fator = 1.0
        
        return int(intervalo * fator)
    
    def calcular_prioridade(
        self,
        data_revisao: str,
        ef: float,
        repetition: int,
        historico_acertos: float
    ) -> int:
        """
        Calcula a prioridade de uma revisão (0-100).
        
        Maior prioridade = mais urgente
        
        Fatores:
        - Dias até revisão (urgência)
        - EF baixo (dificuldade)
        - Poucas repetições (novidade)
        - Histórico de erros
        
        Returns:
            Prioridade de 0 (baixa) a 100 (alta)
        """
        
        # 1. Urgência (0-40 pontos)
        hoje = datetime.now().date()
        data_rev = datetime.strptime(data_revisao, "%Y-%m-%d").date()
        dias_restantes = (data_rev - hoje).days
        
        if dias_restantes < 0:
            urgencia = 40  # Atrasada
        elif dias_restantes == 0:
            urgencia = 35  # Hoje
        elif dias_restantes <= 2:
            urgencia = 25  # Próximos dias
        else:
            urgencia = max(0, 20 - dias_restantes)
        
        # 2. Dificuldade (0-30 pontos)
        dificuldade = int((self.EF_MAX - ef) / (self.EF_MAX - self.EF_MIN) * 30)
        
        # 3. Novidade (0-20 pontos)
        novidade = max(0, 20 - repetition * 3)
        
        # 4. Histórico (0-10 pontos)
        historico = int((1 - historico_acertos) * 10)
        
        prioridade = urgencia + dificuldade + novidade + historico
        
        return min(100, max(0, prioridade))


def exemplo_uso():
    """
    Exemplo de uso do algoritmo adaptativo.
    """
    print("=" * 60)
    print("EXEMPLO DE USO DO ALGORITMO ADAPTATIVO")
    print("=" * 60)
    
    # Criar instância
    alg = AlgoritmoAdaptativo(modo_intensivo=False)
    
    # Simular sequência de revisões
    print("\n[SIMULACAO] Sequencia de revisoes:\n")
    
    ef, interval, repetition = 2.5, 1, 0
    
    cenarios = [
        (4, 4, 45, "Acertou bem, confiante, rápido"),
        (5, 5, 30, "Perfeito, muito confiante, muito rápido"),
        (3, 2, 90, "Acertou com dúvida, inseguro, devagar"),
        (2, 1, 120, "Errou, muito inseguro, muito devagar"),
        (4, 3, 60, "Acertou bem, neutro, tempo normal"),
    ]
    
    for i, (quality, confianca, tempo, descricao) in enumerate(cenarios, 1):
        ef, interval, repetition = alg.calcular_proxima_revisao(
            quality=quality,
            nivel_confianca=confianca,
            ef=ef,
            interval=interval,
            repetition=repetition,
            tempo_resposta=tempo,
            tempo_esperado=60
        )
        
        print(f"Revisao {i}: {descricao}")
        print(f"  Quality: {quality}/5 | Confianca: {confianca}/5 | Tempo: {tempo}s")
        print(f"  => EF: {ef:.2f} | Intervalo: {interval} dias | Repeticao: {repetition}")
        print()
    
    # Comparar modo normal vs intensivo
    print("\n[COMPARACAO] Modo Normal vs Modo Intensivo\n")
    
    alg_normal = AlgoritmoAdaptativo(modo_intensivo=False)
    alg_intensivo = AlgoritmoAdaptativo(modo_intensivo=True)
    
    ef_n, int_n, rep_n = alg_normal.calcular_proxima_revisao(4, 4, 2.5, 7, 2)
    ef_i, int_i, rep_i = alg_intensivo.calcular_proxima_revisao(4, 4, 2.5, 7, 2)
    
    print(f"Modo Normal:    Proxima revisao em {int_n} dias")
    print(f"Modo Intensivo: Proxima revisao em {int_i} dias")
    print(f"Reducao: {((int_n - int_i) / int_n * 100):.0f}%")


if __name__ == "__main__":
    exemplo_uso()
