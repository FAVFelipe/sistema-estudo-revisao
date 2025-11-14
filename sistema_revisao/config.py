#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações do sistema"""
    
    # Configurações do Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_aqui')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Configurações do banco de dados
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'revisao_estudos.db')
    
    # Configurações de email (opcional)
    EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
    SENHA_EMAIL = os.getenv('SENHA_EMAIL')
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    
    # Configurações de revisão
    DIAS_REVISAO = [1, 3, 7, 14, 30]  # Dias para cada revisão
    TIPOS_REVISAO = ["1ª revisão", "2ª revisão", "3ª revisão", "4ª revisão", "5ª revisão"]
    
    # Configurações de interface
    ITENS_POR_PAGINA = 10
    DIAS_URGENTE = 0  # Revisões vencidas
    DIAS_AVISO = 3    # Revisões próximas do vencimento

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

