# Sistema Inteligente de Organização e Revisão de Estudos

## Descrição

Sistema web desenvolvido em Python/Flask que implementa a técnica de **Spaced Repetition** (Repetição Espaçada) para otimizar a memorização e o desempenho acadêmico de estudantes.

## Objetivos

- Permitir cadastro de matérias e tópicos estudados
- Programar revisões automáticas baseadas na curva do esquecimento
- Enviar lembretes nos momentos ideais de revisão
- Ajustar cronograma conforme desempenho do aluno
- Gerar relatórios visuais de progresso

## Funcionalidades

### Sistema de Usuários
- Registro e login de usuários
- Autenticação segura com hash de senhas
- Sessões persistentes

### Gestão de Estudos
- Cadastro de matérias e tópicos
- Sistema de revisões automáticas (1, 3, 7, 14, 30 dias)
- Marcação de revisões como concluídas

### Interface Web
- Dashboard responsivo com Bootstrap 5
- Visualização de revisões urgentes e próximas
- Interface moderna e intuitiva

### Notificações
- Sistema de lembretes por email (configurável)
- Verificação automática de revisões pendentes

## Tecnologias Utilizadas

- **Backend**: Python 3.x, Flask
- **Banco de Dados**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Gráficos**: Matplotlib
- **Email**: SMTP (Gmail)

## Instalação

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos para Instalação

1. **Clone ou baixe o projeto**
   ```bash
   git clone [URL_DO_REPOSITORIO]
   cd sistema_revisao
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente (opcional)**
   Crie um arquivo `.env` na raiz do projeto:
   ```
   EMAIL_REMETENTE=seu_email@gmail.com
   SENHA_EMAIL=sua_senha_de_app
   ```

## Como Executar

### Inicialização Rápida (Recomendado)
```bash
python start.py
```
Este script irá:
- Verificar e instalar dependências
- Configurar o banco de dados
- Criar dados de demonstração
- Iniciar o servidor automaticamente

### Aplicação Web Principal
```bash
python app.py
```
Acesse: http://localhost:5000

### Aplicação de Console (Alternativa)
```bash
python main.py
```

### Sistema de Lembretes (Opcional)
```bash
python lembretes.py
```

### Dados de Demonstração
```bash
python demo_sistema.py
```
Cria um usuário de teste com dados de exemplo.

## 📖 Como Usar

### 1. Primeiro Acesso
- Acesse http://localhost:5000
- **Opção 1**: Use as credenciais de demonstração
  - Email: `joao@demo.com`
  - Senha: `123456`
- **Opção 2**: Clique em "Registre-se aqui" e crie uma nova conta

### 2. Cadastrar Estudos
- Faça login no sistema
- Clique em "Cadastrar Novo Estudo"
- Informe a matéria e o tópico estudado
- O sistema criará automaticamente 5 revisões (1, 3, 7, 14, 30 dias)

### 3. Gerenciar Revisões
- No dashboard, visualize suas revisões pendentes
- Revisões urgentes (vencem hoje) aparecem em destaque
- Clique em "Marcar como Feita" quando concluir uma revisão

### 4. Acompanhar Progresso
- O sistema mostra revisões urgentes e próximas
- Use a aplicação de console para gerar gráficos de desempenho

## Estrutura do Banco de Dados

### Tabelas Principais
- **usuarios**: Dados dos usuários
- **estudos**: Matérias e tópicos cadastrados
- **revisoes**: Cronograma de revisões
- **configuracoes_email**: Configurações de notificação

## Estrutura do Projeto

```
sistema_revisao/
├── app.py                # Aplicação web principal
├── main.py              # Aplicação de console
├── start.py             # Script de inicialização rápida
├── demo_sistema.py      # Script de demonstração
├── test_sistema.py      # Script de testes
├── config.py            # Configurações do sistema
├── lembretes.py         # Sistema de notificações
├── requirements.txt     # Dependências do projeto
├── env_example.txt      # Exemplo de variáveis de ambiente
├── revisao_estudos.db  # Banco de dados SQLite
├── static/             # Arquivos estáticos
│   ├── js/
│   │   └── app.js      # JavaScript da aplicação
│   └── manifest.json   # Manifesto PWA
└── templates/          # Templates HTML
    ├── index.html      # Dashboard principal
    ├── login.html      # Página de login
    ├── register.html   # Página de registro
    └── cadastrar.html  # Formulário de cadastro
```

## Configuração de Email (Opcional)

Para ativar as notificações por email:

1. Configure um email Gmail
2. Ative a verificação em duas etapas
3. Gere uma senha de aplicativo
4. Configure as variáveis no arquivo `.env`
5. Execute `python lembretes.py` em segundo plano

## Solução de Problemas

### Erro de Importação
```bash
pip install flask matplotlib python-dotenv
```

### Banco de Dados Corrompido
```bash
# Remova o arquivo e reinicie a aplicação
rm revisao_estudos.db
python app.py
```

### Problemas de Sessão
- Limpe os cookies do navegador
- Verifique se o `secret_key` está configurado

## Relatórios e Análises

O sistema oferece:
- Visualização de revisões pendentes
- Categorização por urgência
- Histórico de desempenho (via console)
- Gráficos de progresso

## Contribuição

Para contribuir com o projeto:
1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.

## Desenvolvido por

Sistema desenvolvido como projeto acadêmico para as disciplinas:
- Lógica de Programação
- Banco de Dados
- Desenvolvimento Web
- Projetos de Sistemas

---

**FATEC - Faculdade de Tecnologia**
