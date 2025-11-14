#!/usr/bin/env python3
"""
Script de Migração do Banco de Dados
Sistema Inteligente de Revisão de Estudos

Este script adiciona as colunas necessárias para as funcionalidades expandidas:
- Modos de revisão (Flashcard, Quiz)
- Nível de confiança
- Modo pré-prova
- Métricas de desempenho

Autor: Sistema de Revisão Adaptativa
Data: 2025
"""

import sqlite3
import os

def executar_migracoes():
    """
    Executa todas as migrações necessárias no banco de dados.
    
    Migrações são idempotentes (podem ser executadas múltiplas vezes).
    """
    
    # Conectar ao banco
    db_path = 'revisao_estudos.db'
    if not os.path.exists(db_path):
        print("[ERRO] Banco de dados nao encontrado!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("[INFO] Iniciando migracoes do banco de dados...\n")
    
    # ========================================
    # MIGRACAO 1: Campos de conteudo em estudos
    # ========================================
    print("[1/4] Migracao 1: Adicionar campos de conteudo")
    
    migracoes_estudos = [
        ("pergunta", "TEXT", "Campo para perguntas de flashcard/quiz"),
        ("resposta", "TEXT", "Campo para resposta correta"),
        ("opcoes", "TEXT", "JSON com opcoes de multipla escolha"),
        ("tipo_conteudo", "TEXT DEFAULT 'simples'", "Tipo: simples, flashcard, quiz")
    ]
    
    for coluna, tipo, descricao in migracoes_estudos:
        try:
            cursor.execute(f'ALTER TABLE estudos ADD COLUMN {coluna} {tipo}')
            conn.commit()
            print(f"  [OK] {coluna}: {descricao}")
        except sqlite3.OperationalError:
            print(f"  [SKIP] {coluna}: ja existe")
    
    # ========================================
    # MIGRACAO 2: Campos de desempenho em revisoes
    # ========================================
    print("\n[2/4] Migracao 2: Adicionar campos de desempenho")
    
    migracoes_revisoes = [
        ("modo_revisao", "TEXT DEFAULT 'simples'", "Modo usado: simples, flashcard, quiz"),
        ("nivel_confianca", "INTEGER", "Nivel de confianca do aluno (1-5)"),
        ("tempo_resposta", "INTEGER", "Tempo de resposta em segundos"),
        ("tentativas", "INTEGER DEFAULT 1", "Numero de tentativas ate acertar")
    ]
    
    for coluna, tipo, descricao in migracoes_revisoes:
        try:
            cursor.execute(f'ALTER TABLE revisoes ADD COLUMN {coluna} {tipo}')
            conn.commit()
            print(f"  [OK] {coluna}: {descricao}")
        except sqlite3.OperationalError:
            print(f"  [SKIP] {coluna}: ja existe")
    
    # ========================================
    # MIGRACAO 3: Modo intensivo em usuarios
    # ========================================
    print("\n[3/4] Migracao 3: Adicionar modo pre-prova")
    
    migracoes_usuarios = [
        ("modo_intensivo", "INTEGER DEFAULT 0", "Modo pre-prova ativado (0/1)"),
        ("data_prova", "TEXT", "Data da prova para modo intensivo"),
        ("materias_prova", "TEXT", "JSON com materias da prova")
    ]
    
    for coluna, tipo, descricao in migracoes_usuarios:
        try:
            cursor.execute(f'ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}')
            conn.commit()
            print(f"  [OK] {coluna}: {descricao}")
        except sqlite3.OperationalError:
            print(f"  [SKIP] {coluna}: ja existe")
    
    # ========================================
    # MIGRACAO 4: Tabela de estatisticas
    # ========================================
    print("\n[4/4] Migracao 4: Criar tabela de estatisticas")
    
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS estatisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            data DATE,
            total_revisoes INTEGER DEFAULT 0,
            acertos INTEGER DEFAULT 0,
            erros INTEGER DEFAULT 0,
            tempo_total INTEGER DEFAULT 0,
            confianca_media REAL DEFAULT 0,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        ''')
        conn.commit()
        print("  [OK] Tabela estatisticas criada")
    except sqlite3.OperationalError:
        print("  [SKIP] Tabela estatisticas ja existe")
    
    # ========================================
    # VERIFICACAO FINAL
    # ========================================
    print("\n[VERIFICACAO] Estrutura do banco...")
    
    # Verificar colunas de estudos
    cursor.execute("PRAGMA table_info(estudos)")
    colunas_estudos = [col[1] for col in cursor.fetchall()]
    print(f"\n[ESTUDOS] {len(colunas_estudos)} colunas:")
    print(f"   {', '.join(colunas_estudos)}")
    
    # Verificar colunas de revisoes
    cursor.execute("PRAGMA table_info(revisoes)")
    colunas_revisoes = [col[1] for col in cursor.fetchall()]
    print(f"\n[REVISOES] {len(colunas_revisoes)} colunas:")
    print(f"   {', '.join(colunas_revisoes)}")
    
    # Verificar colunas de usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas_usuarios = [col[1] for col in cursor.fetchall()]
    print(f"\n[USUARIOS] {len(colunas_usuarios)} colunas:")
    print(f"   {', '.join(colunas_usuarios)}")
    
    conn.close()
    
    print("\n[SUCESSO] Migracoes concluidas!")
    print("\n[PROXIMOS PASSOS]")
    print("   1. Reinicie o servidor Flask")
    print("   2. Teste o cadastro de estudos com novos campos")
    print("   3. Implemente os modos de revisao (Flashcard/Quiz)")

if __name__ == "__main__":
    executar_migracoes()
