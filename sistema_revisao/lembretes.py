#!/usr/bin/env python3
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class SistemaLembretes:
    def __init__(self):
        # Configurações de email
        self.email_remetente = os.getenv('EMAIL_REMETENTE')
        self.senha_email = os.getenv('SENHA_EMAIL')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

        # Configurações do sistema
        self.database_path = os.getenv('DATABASE_PATH', 'revisao_estudos.db')
        self.intervalo_verificacao = int(os.getenv('INTERVALO_VERIFICACAO', '3600'))  # 1 hora por padrão

        # Conectar ao banco de dados
        self.conn = sqlite3.connect(self.database_path)
        self.cursor = self.conn.cursor()

        print("Sistema de lembretes iniciado...")
        print(f"Verificando a cada {self.intervalo_verificacao} segundos")

    def enviar_email(self, destinatario, assunto, mensagem):
        """Envia email usando SMTP"""
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_remetente
            msg['To'] = destinatario
            msg['Subject'] = assunto

            # Adicionar corpo do email
            msg.attach(MIMEText(mensagem, 'html'))

            # Conectar ao servidor SMTP
            servidor = smtplib.SMTP(self.smtp_server, self.smtp_port)
            servidor.starttls()
            servidor.login(self.email_remetente, self.senha_email)

            # Enviar email
            servidor.send_message(msg)
            servidor.quit()

            print(f"Email enviado para {destinatario}")
            return True

        except Exception as e:
            print(f"Erro ao enviar email para {destinatario}: {str(e)}")
            return False

    def obter_revisoes_pendentes(self, usuario_id, dias_aviso=1):
        """Obtém revisões pendentes para um usuário"""
        hoje = datetime.now().date()
        data_limite = hoje + timedelta(days=dias_aviso)

        self.cursor.execute('''
            SELECT r.id, e.materia, e.topico, r.tipo, r.data_revisao
            FROM revisoes r
            JOIN estudos e ON r.id_estudo = e.id
            WHERE r.feito = 0
            AND e.usuario_id = ?
            AND date(r.data_revisao) <= ?
            ORDER BY r.data_revisao ASC
        ''', (usuario_id, data_limite.strftime("%Y-%m-%d")))

        return self.cursor.fetchall()

    def verificar_e_enviar_lembretes(self):
        """Verifica revisões pendentes e envia lembretes"""
        print(f"\n[{datetime.now()}] Verificando lembretes...")

        # Obter usuários com notificações ativas
        self.cursor.execute('''
            SELECT DISTINCT u.id, u.nome, u.email, ce.email_notificacao
            FROM usuarios u
            JOIN configuracoes_email ce ON u.id = ce.usuario_id
            WHERE ce.ativo = 1
        ''')

        usuarios = self.cursor.fetchall()

        for usuario_id, nome, email_principal, email_notificacao in usuarios:
            # Usar email de notificação se disponível, senão o principal
            email_destino = email_notificacao if email_notificacao else email_principal

            # Obter revisões pendentes
            revisoes = self.obter_revisoes_pendentes(usuario_id)

            if revisoes:
                # Criar mensagem de lembrete
                assunto = "Lembrete de Revisões - Sistema de Estudos"

                base_url = os.getenv('BASE_URL', 'http://localhost:5000')
                mensagem = f"""
                <html>
                <body>
                    <h2>Olá {nome}!</h2>
                    <p>Você tem revisões pendentes no Sistema de Revisão de Estudos:</p>
                    <ul>
                """

                for rev_id, materia, topico, tipo, data_revisao in revisoes:
                    data_rev = datetime.strptime(data_revisao, "%Y-%m-%d").date()
                    hoje = datetime.now().date()
                    dias_restantes = (data_rev - hoje).days

                    if dias_restantes < 0:
                        status = "VENCIDA"
                    elif dias_restantes == 0:
                        status = "HOJE"
                    else:
                        status = f"em {dias_restantes} dia(s)"

                    mensagem += f"""
                        <li>
                            <strong>{materia} - {topico}</strong><br>
                            {tipo} - Vence {status}
                        </li>
                    """

                mensagem += f"""
                    </ul>
                    <p>
                        <a href="{base_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            Acessar Sistema
                        </a>
                    </p>
                    <p>Continue estudando! 📚</p>
                </body>
                </html>
                """

                # Enviar email
                if self.enviar_email(email_destino, assunto, mensagem):
                    print(f"Lembrete enviado para {nome} ({email_destino})")
                else:
                    print(f"Falha ao enviar lembrete para {nome}")

    def executar(self):
        """Executa o sistema de lembretes em loop ou uma única vez (RUN_ONCE)"""
        if not self.email_remetente or not self.senha_email:
            print("ERRO: Configurações de email não encontradas!")
            print("Configure EMAIL_REMETENTE e SENHA_EMAIL nas variáveis de ambiente")
            return

        print("Iniciando monitoramento de lembretes...")

        try:
            run_once = os.getenv('RUN_ONCE', 'false').lower() in ('1', 'true', 'yes')
            if run_once:
                self.verificar_e_enviar_lembretes()
                return
            while True:
                self.verificar_e_enviar_lembretes()
                time.sleep(self.intervalo_verificacao)

        except KeyboardInterrupt:
            print("\nSistema de lembretes interrompido pelo usuário.")
        except Exception as e:
            print(f"Erro no sistema de lembretes: {str(e)}")
        finally:
            self.conn.close()

def main():
    """Função principal"""
    sistema = SistemaLembretes()
    sistema.executar()

if __name__ == "__main__":
    main()
