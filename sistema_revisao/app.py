from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
import sqlite3
import hashlib
import io
import csv
import json
from datetime import datetime, timedelta 
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Alterar em produção

# Conexão com o banco
conn = sqlite3.connect('revisao_estudos.db', check_same_thread=False)
cursor = conn.cursor()

# Tabela de usuários
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabela de estudos
cursor.execute('''
CREATE TABLE IF NOT EXISTS estudos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT,
    topico TEXT,
    data_estudo TEXT,
    usuario_id INTEGER,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
)
''')

# Tabela de revisões
cursor.execute('''
CREATE TABLE IF NOT EXISTS revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudo INTEGER,
    data_revisao TEXT,
    tipo TEXT,
    feito INTEGER DEFAULT 0,
    ef REAL DEFAULT 2.5,
    repetition INTEGER DEFAULT 0,
    interval INTEGER DEFAULT 1,
    FOREIGN KEY(id_estudo) REFERENCES estudos(id)
)
''')

# Tabela de configurações de email
cursor.execute('''
CREATE TABLE IF NOT EXISTS configuracoes_email (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    email_notificacao TEXT,
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
)
''')

conn.commit()

# Migração: adicionar coluna quality se não existir
try:
    cursor.execute('ALTER TABLE revisoes ADD COLUMN quality INTEGER')
    conn.commit()
    print("Migração: coluna 'quality' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe, tudo bem
    pass

# Migração: adicionar coluna ef se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN ef REAL DEFAULT 2.5")
    conn.commit()
    print("Migração: coluna 'ef' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe
    pass

# Migração: adicionar coluna tempo_resposta (segundos) se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN tempo_resposta INTEGER")
    conn.commit()
    print("Migração: coluna 'tempo_resposta' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe
    pass

# Migração: adicionar coluna repetition se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN repetition INTEGER DEFAULT 0")
    conn.commit()
    print("Migração: coluna 'repetition' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe
    pass

# Migração: adicionar coluna interval se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN interval INTEGER DEFAULT 1")
    conn.commit()
    print("Migração: coluna 'interval' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe
    pass

# Migração: adicionar coluna nivel_confianca se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN nivel_confianca INTEGER")
    conn.commit()
    print("Migração: coluna 'nivel_confianca' adicionada")
except sqlite3.OperationalError:
    # Coluna já existe
    pass

# Migração: adicionar colunas em estudos se não existirem
try:
    cursor.execute("ALTER TABLE estudos ADD COLUMN tipo_conteudo TEXT")
    conn.commit()
    print("Migração: coluna 'tipo_conteudo' adicionada em estudos")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE estudos ADD COLUMN pergunta TEXT")
    conn.commit()
    print("Migração: coluna 'pergunta' adicionada em estudos")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE estudos ADD COLUMN resposta TEXT")
    conn.commit()
    print("Migração: coluna 'resposta' adicionada em estudos")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE estudos ADD COLUMN opcoes TEXT")
    conn.commit()
    print("Migração: coluna 'opcoes' adicionada em estudos")
except sqlite3.OperationalError:
    pass

# Migração: adicionar coluna modo_revisao em revisoes se não existir
try:
    cursor.execute("ALTER TABLE revisoes ADD COLUMN modo_revisao TEXT")
    conn.commit()
    print("Migração: coluna 'modo_revisao' adicionada em revisoes")
except sqlite3.OperationalError:
    pass

def hash_senha(senha):
    """Hash da senha usando SHA-256"""
    return hashlib.sha256(senha.encode()).hexdigest()

# Função SM-2 mínima
def sm2(quality, ef=2.5, interval=1, repetition=0):
    """
    quality: 0-5
    retorna (ef, interval_days, repetition)
    """
    if quality < 3:
        repetition = 0
        interval = 1
    else:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ef))
        repetition += 1
    ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    return ef, interval, repetition

def schedule_next_review(id_estudo, current_ef, current_interval, current_repetition, quality):
    """
    Gera uma nova revisao (linha) com a data calculada pelo SM-2.
    """
    ef, interval_days, repetition = sm2(quality, ef=current_ef, interval=current_interval, repetition=current_repetition)
    proxima = (datetime.now() + timedelta(days=interval_days)).strftime("%Y-%m-%d")
    # Descobrir o modo de revisão a partir do estudo
    try:
        cursor.execute('SELECT COALESCE(tipo_conteudo, "simples") FROM estudos WHERE id = ?', (id_estudo,))
        modo_revisao = cursor.fetchone()[0] or 'simples'
    except Exception:
        modo_revisao = 'simples'

    try:
        cursor.execute('''
            INSERT INTO revisoes (id_estudo, data_revisao, tipo, feito, ef, repetition, interval, modo_revisao)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?)
        ''', (id_estudo, proxima, 'SM-2', ef, repetition, interval_days, modo_revisao))
    except sqlite3.OperationalError:
        # Banco legado sem coluna modo_revisao
        cursor.execute('''
            INSERT INTO revisoes (id_estudo, data_revisao, tipo, feito, ef, repetition, interval)
            VALUES (?, ?, ?, 0, ?, ?, ?)
        ''', (id_estudo, proxima, 'SM-2', ef, repetition, interval_days))
    conn.commit()
    return proxima

@app.route('/export.csv')
def export_csv():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['materia', 'topico', 'data_estudo'])
    cursor.execute("SELECT materia, topico, data_estudo FROM estudos WHERE usuario_id = ?", (session['usuario_id'],))
    for row in cursor.fetchall():
        cw.writerow(row)
    output = si.getvalue()
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=estudos.csv"})

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    hoje = datetime.now().strftime("%Y-%m-%d")
    pre_exam = session.get('pre_exam_mode', False)
    if pre_exam:
        # Priorizar baixa confiança quando modo pré-prova ativo (usar coluna só no ORDER BY)
        cursor.execute('''
        SELECT 
            revisoes.id,
            estudos.materia,
            estudos.topico,
            revisoes.tipo,
            revisoes.data_revisao,
            COALESCE(estudos.tipo_conteudo, 'simples') as tipo_conteudo,
            estudos.pergunta,
            estudos.resposta,
            estudos.opcoes
        FROM revisoes
        JOIN estudos ON revisoes.id_estudo = estudos.id
        WHERE revisoes.feito = 0 AND estudos.usuario_id = ? AND revisoes.data_revisao <= ?
        ORDER BY revisoes.data_revisao ASC, COALESCE(revisoes.nivel_confianca, 3) ASC
        ''', (session['usuario_id'], hoje))
    else:
        cursor.execute('''
        SELECT 
            revisoes.id,
            estudos.materia,
            estudos.topico,
            revisoes.tipo,
            revisoes.data_revisao,
            COALESCE(estudos.tipo_conteudo, 'simples') as tipo_conteudo,
            estudos.pergunta,
            estudos.resposta,
            estudos.opcoes
        FROM revisoes
        JOIN estudos ON revisoes.id_estudo = estudos.id
        WHERE revisoes.feito = 0 AND estudos.usuario_id = ? AND revisoes.data_revisao <= ?
        ORDER BY revisoes.data_revisao ASC
        ''', (session['usuario_id'], hoje))
    revisoes = cursor.fetchall()

    hoje_dt = datetime.strptime(hoje, "%Y-%m-%d")
    urgentes = []
    proximas = []

    for rev_id, materia, topico, tipo, data_revisao, tipo_conteudo, pergunta, resposta, opcoes_json in revisoes:
        data_rev_dt = datetime.strptime(data_revisao, "%Y-%m-%d")
        dias_restantes = (data_rev_dt - hoje_dt).days
        opcoes = None
        if opcoes_json:
            try:
                opcoes = json.loads(opcoes_json)
            except Exception:
                opcoes = None
        if dias_restantes <= 0:
            urgentes.append((rev_id, materia, topico, tipo, dias_restantes, tipo_conteudo, pergunta, resposta, opcoes))
        else:
            proximas.append((rev_id, materia, topico, tipo, dias_restantes, tipo_conteudo, pergunta, resposta, opcoes))

    return render_template('index.html', urgentes=urgentes, proximas=proximas, pre_exam=pre_exam)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        senha_hash = hash_senha(senha)
        
        cursor.execute('SELECT id, nome FROM usuarios WHERE email = ? AND senha = ?', 
                       (email, senha_hash))
        usuario = cursor.fetchone()
        
        if usuario:
            session['usuario_id'] = usuario[0]
            session['usuario_nome'] = usuario[1]
            session['usuario_email'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Email ou senha inválidos')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            return render_template('register.html', erro='As senhas não coincidem')
        
        # Verificar se email já existe
        cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
        if cursor.fetchone():
            return render_template('register.html', erro='Email já cadastrado')
        
        senha_hash = hash_senha(senha)
        cursor.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                     (nome, email, senha_hash))
        conn.commit()
        
        # Configurar email de notificação
        usuario_id = cursor.lastrowid
        cursor.execute('INSERT INTO configuracoes_email (usuario_id, email_notificacao) VALUES (?, ?)',
                     (usuario_id, email))
        conn.commit()
        
        session['usuario_id'] = usuario_id
        session['usuario_nome'] = nome
        session['usuario_email'] = email
        
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Rotas para ativar/desativar o Modo pré-prova
@app.route('/pre-exam/on')
def pre_exam_on():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    session['pre_exam_mode'] = True
    return redirect(url_for('index'))

@app.route('/pre-exam/off')
def pre_exam_off():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    session['pre_exam_mode'] = False
    return redirect(url_for('index'))

# Página de configurações (GET exibe, POST salva)
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Toggle modo pré-prova
        pre_exam = request.form.get('pre_exam') == 'on'
        session['pre_exam_mode'] = pre_exam
        # Fator pre-exam
        try:
            fator = float(request.form.get('pre_exam_factor', '0.6'))
        except ValueError:
            fator = 0.6
        # Limites de segurança 0.4–0.8
        fator = max(0.4, min(0.8, fator))
        session['pre_exam_factor'] = fator
        # Tema (dark mode)
        dark_mode = request.form.get('dark_mode') == 'on'
        session['theme'] = 'dark' if dark_mode else 'light'
        return redirect(url_for('settings'))
    # GET
    pre_exam = session.get('pre_exam_mode', False)
    fator = session.get('pre_exam_factor', 0.6)
    return render_template('settings.html', pre_exam=pre_exam, pre_exam_factor=fator)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('cadastrar.html')
    
    try:
        data = request.get_json()
        materia = data.get('materia')
        topico = data.get('topico')
        tipo_conteudo = (data.get('tipo_conteudo') or 'simples').strip().lower()
        pergunta = data.get('pergunta')
        resposta = data.get('resposta')
        data_estudo = datetime.now().strftime("%Y-%m-%d")
        
        if tipo_conteudo == 'flashcard':
            cursor.execute('''
                INSERT INTO estudos (materia, topico, data_estudo, usuario_id, tipo_conteudo, pergunta, resposta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (materia, topico, data_estudo, session['usuario_id'], 'flashcard', pergunta, resposta))
        elif tipo_conteudo == 'quiz':
            # Espera: quiz_pergunta, opcoes (dict com A-D), quiz_resposta_correta (A-D)
            quiz_pergunta = data.get('quiz_pergunta')
            opcoes = data.get('opcoes') or {}
            resposta_correta = data.get('quiz_resposta_correta')
            cursor.execute('''
                INSERT INTO estudos (materia, topico, data_estudo, usuario_id, tipo_conteudo, pergunta, resposta, opcoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                materia, topico, data_estudo, session['usuario_id'], 'quiz',
                quiz_pergunta, resposta_correta, json.dumps(opcoes)
            ))
        else:
            cursor.execute('INSERT INTO estudos (materia, topico, data_estudo, usuario_id, tipo_conteudo) VALUES (?, ?, ?, ?, ?)',
                           (materia, topico, data_estudo, session['usuario_id'], 'simples'))
        conn.commit()
        
        id_estudo = cursor.lastrowid
        dias = [1, 3, 7, 14, 30]
        tipos = ["1ª revisão", "2ª revisão", "3ª revisão", "4ª revisão", "5ª revisão"]
        modo_revisao = tipo_conteudo if tipo_conteudo in ('flashcard','quiz') else 'simples'

        # Criar revisão imediata para hoje, para permitir estudar logo após cadastrar
        hoje = datetime.now().strftime("%Y-%m-%d")
        try:
            cursor.execute('INSERT INTO revisoes (id_estudo, data_revisao, tipo, modo_revisao) VALUES (?, ?, ?, ?)',
                           (id_estudo, hoje, 'Revisão inicial', modo_revisao))
        except sqlite3.OperationalError:
            cursor.execute('INSERT INTO revisoes (id_estudo, data_revisao, tipo) VALUES (?, ?, ?)',
                           (id_estudo, hoje, 'Revisão inicial'))
        
        for d, t in zip(dias, tipos):
            data_revisao = (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%d")
            try:
                cursor.execute('INSERT INTO revisoes (id_estudo, data_revisao, tipo, modo_revisao) VALUES (?, ?, ?, ?)',
                               (id_estudo, data_revisao, t, modo_revisao))
            except sqlite3.OperationalError:
                # Caso a coluna não exista no banco legado, insere sem o campo
                cursor.execute('INSERT INTO revisoes (id_estudo, data_revisao, tipo) VALUES (?, ?, ?)',
                               (id_estudo, data_revisao, t))
        conn.commit()
        
        return jsonify({'status': 'sucesso'})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)})

@app.route('/marcar/<int:revisao_id>', methods=['POST'])
def marcar_feita(revisao_id):
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário não autenticado'})
    
    # 1. RECEBER a qualidade do front-end
    data = request.get_json()
    quality = data.get('quality')
    nivel_confianca = data.get('nivel_confianca')
    tempo_resposta = data.get('tempo_resposta')
    
    # 2. VALIDAR a qualidade (deve ser 0-5)
    if quality is None or not isinstance(quality, int) or quality < 0 or quality > 5:
        return jsonify({'status': 'erro', 'mensagem': 'Quality deve ser um número entre 0 e 5'})
    if nivel_confianca is None:
        nivel_confianca = 3
    if not isinstance(nivel_confianca, int) or nivel_confianca < 1 or nivel_confianca > 5:
        return jsonify({'status': 'erro', 'mensagem': 'Nível de confiança deve ser um número entre 1 e 5'})
    
    # 3. BUSCAR dados atuais da revisão
    cursor.execute('''
        SELECT id_estudo, ef, repetition, interval, COALESCE(modo_revisao, 'simples')
        FROM revisoes 
        WHERE id = ?
    ''', (revisao_id,))
    
    resultado = cursor.fetchone()
    if not resultado:
        return jsonify({'status': 'erro', 'mensagem': 'Revisão não encontrada'})
    
    id_estudo, current_ef, current_repetition, current_interval, modo_revisao = resultado

    # 3.1 EXIGIR interação para flashcard/quiz (tempo_resposta presente)
    if modo_revisao in ('flashcard', 'quiz'):
        if tempo_resposta is None or not isinstance(tempo_resposta, int) or tempo_resposta < 0:
            return jsonify({'status': 'erro', 'mensagem': 'Finalize a interação (mostrar resposta ou responder o quiz) antes de concluir.'})
    
    # 4. APLICAR o algoritmo SM-2
    # Usa valores padrão se forem None (revisões antigas)
    current_ef = current_ef if current_ef is not None else 2.5
    current_repetition = current_repetition if current_repetition is not None else 0
    current_interval = current_interval if current_interval is not None else 1
    
    # 5. CALCULAR próxima revisão
    new_ef, new_interval, new_repetition = sm2(
        quality=quality,
        ef=current_ef,
        interval=current_interval,
        repetition=current_repetition
    )
    
    # 5.1 AJUSTE LEVE PELO NÍVEL DE CONFIANÇA (1-5)
    # Menor confiança => intervalos menores; Maior confiança => intervalos ligeiramente maiores
    # Escala suave para não distorcer o SM-2
    fator_conf = {
        1: 0.5,   # muito inseguro: revisar mais cedo
        2: 0.75,  # inseguro
        3: 1.0,   # neutro
        4: 1.15,  # confiante
        5: 1.3    # muito confiante
    }.get(nivel_confianca, 1.0)
    new_interval = max(1, int(round(new_interval * fator_conf)))

    # 5.2 AJUSTE DO MODO PRÉ-PROVA (se ativo na sessão)
    if session.get('pre_exam_mode', False):
        pre_exam_factor = session.get('pre_exam_factor', 0.6)
        try:
            pre_exam_factor = float(pre_exam_factor)
        except (TypeError, ValueError):
            pre_exam_factor = 0.6
        pre_exam_factor = max(0.4, min(0.8, pre_exam_factor))
        new_interval = max(1, int(round(new_interval * pre_exam_factor)))

    # 5.3 AJUSTE PELO TEMPO DE RESPOSTA (opcional, suave)
    # Rápido (<= 5s) => +10% no intervalo; Lento (>= 30s) => -10%
    if isinstance(tempo_resposta, int):
        if tempo_resposta <= 5:
            new_interval = max(1, int(round(new_interval * 1.10)))
        elif tempo_resposta >= 30:
            new_interval = max(1, int(round(new_interval * 0.90)))
    
    # 6. MARCAR revisão atual como feita E salvar a quality
    cursor.execute('''
        UPDATE revisoes 
        SET feito = 1, quality = ?, nivel_confianca = ?, tempo_resposta = ?
        WHERE id = ?
    ''', (quality, nivel_confianca, tempo_resposta, revisao_id))
    
    # 7. CRIAR próxima revisão com os novos valores
    proxima_data = (datetime.now() + timedelta(days=new_interval)).strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO revisoes (id_estudo, data_revisao, tipo, feito, ef, repetition, interval)
        VALUES (?, ?, ?, 0, ?, ?, ?)
    ''', (id_estudo, proxima_data, 'SM-2', new_ef, new_repetition, new_interval))
    
    conn.commit()
    
    # 8. RETORNAR sucesso com informações úteis
    return jsonify({
        'status': 'ok',
        'proxima_revisao': proxima_data,
        'intervalo_dias': new_interval,
        'ef': new_ef
    })

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario_id = session['usuario_id']
    
    # Estatísticas básicas
    cursor.execute('''
        SELECT COUNT(*) FROM estudos WHERE usuario_id = ?
    ''', (usuario_id,))
    total_estudos = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.feito = 1
    ''', (usuario_id,))
    revisoes_concluidas = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.feito = 0
    ''', (usuario_id,))
    revisoes_pendentes = cursor.fetchone()[0]
    
    # Novos estudos na última semana
    cursor.execute('''
        SELECT COUNT(*) FROM estudos 
        WHERE usuario_id = ? AND data_estudo >= date('now', '-7 days')
    ''', (usuario_id,))
    novos_estudos_7d = cursor.fetchone()[0]
    
    # Revisões urgentes (vencem hoje)
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 0
    ''', (usuario_id, hoje))
    revisoes_urgentes = cursor.fetchone()[0]
    
    # Percentual de conclusão
    total_revisoes = revisoes_concluidas + revisoes_pendentes
    percentual_concluidas = round((revisoes_concluidas / total_revisoes * 100) if total_revisoes > 0 else 0, 1)
    
    # Dias ativos (dias desde o primeiro estudo)
    cursor.execute('''
        SELECT MIN(data_estudo) FROM estudos WHERE usuario_id = ?
    ''', (usuario_id,))
    primeiro_estudo = cursor.fetchone()[0]
    
    if primeiro_estudo:
        primeiro_dia = datetime.strptime(primeiro_estudo, "%Y-%m-%d")
        dias_ativos = (datetime.now() - primeiro_dia).days + 1
        ultima_atividade = "Hoje" if dias_ativos == 1 else f"{dias_ativos} dias"
    else:
        dias_ativos = 0
        ultima_atividade = "Nunca"
    
    # Dados para gráficos
    datas_progresso = []
    valores_progresso = []
    datas_progresso_30 = []
    valores_progresso_30 = []
    datas_total = []
    valores_total = []

    # Últimos 7 dias
    for i in range(6, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        datas_progresso.append(data)
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
        ''', (usuario_id, data))
        valor = cursor.fetchone()[0]
        valores_progresso.append(valor)

    # Últimos 30 dias
    for i in range(29, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        datas_progresso_30.append(data)
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
        ''', (usuario_id, data))
        valor = cursor.fetchone()[0]
        valores_progresso_30.append(valor)

    # Total acumulado desde o primeiro estudo
    cursor.execute('''
        SELECT MIN(data_estudo) FROM estudos WHERE usuario_id = ?
    ''', (usuario_id,))
    primeiro_estudo = cursor.fetchone()[0]

    if primeiro_estudo:
        primeiro_dia = datetime.strptime(primeiro_estudo, "%Y-%m-%d")
        dias_totais = (datetime.now() - primeiro_dia).days + 1
        acumulado = 0
        for i in range(dias_totais):
            data = (primeiro_dia + timedelta(days=i)).strftime("%Y-%m-%d")
            datas_total.append(data)
            cursor.execute('''
                SELECT COUNT(*) FROM revisoes r 
                JOIN estudos e ON r.id_estudo = e.id 
                WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
            ''', (usuario_id, data))
            valor = cursor.fetchone()[0]
            acumulado += valor
            valores_total.append(acumulado)
    else:
        datas_total = []
        valores_total = []
    
    # Desempenho por matéria
    cursor.execute('''
        SELECT e.materia, 
               COUNT(r.id) as total_revisoes,
               SUM(CASE WHEN r.feito = 1 THEN 1 ELSE 0 END) as concluidas
        FROM estudos e
        LEFT JOIN revisoes r ON e.id = r.id_estudo
        WHERE e.usuario_id = ?
        GROUP BY e.materia
    ''', (usuario_id,))
    
    materias_desempenho = []
    for materia, total, concluidas in cursor.fetchall():
        percentual = round((concluidas / total * 100) if total > 0 else 0, 1)
        materias_desempenho.append({
            'nome': materia,
            'total_revisoes': total,
            'percentual': percentual
        })
    
    # Dados para tendências
    labels_tendencias = ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4']
    dados_tendencias = []
    
    for semana in range(4):
        inicio_semana = (datetime.now() - timedelta(weeks=3-semana)).strftime("%Y-%m-%d")
        fim_semana = (datetime.now() - timedelta(weeks=2-semana)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao BETWEEN ? AND ? AND r.feito = 1
        ''', (usuario_id, inicio_semana, fim_semana))
        valor = cursor.fetchone()[0]
        dados_tendencias.append(valor * 10)  # Escalar para melhor visualização
    
    # Recomendações inteligentes
    recomendacoes = []
    
    if revisoes_urgentes > 0:
        recomendacoes.append({
            'tipo': 'warning',
            'icone': 'exclamation-triangle',
            'titulo': 'Revisões Urgentes',
            'descricao': f'Você tem {revisoes_urgentes} revisões vencendo hoje. Priorize essas revisões!'
        })
    
    if percentual_concluidas < 50:
        recomendacoes.append({
            'tipo': 'danger',
            'icone': 'arrow-down-circle',
            'titulo': 'Baixo Progresso',
            'descricao': 'Seu percentual de conclusão está baixo. Tente manter uma rotina mais consistente.'
        })
    elif percentual_concluidas >= 80:
        recomendacoes.append({
            'tipo': 'success',
            'icone': 'star',
            'titulo': 'Excelente Progresso!',
            'descricao': 'Você está mantendo uma excelente consistência nos estudos. Continue assim!'
        })
    
    if novos_estudos_7d == 0:
        recomendacoes.append({
            'tipo': 'info',
            'icone': 'plus-circle',
            'titulo': 'Adicione Novos Estudos',
            'descricao': 'Você não cadastrou novos estudos esta semana. Considere adicionar novos tópicos.'
        })
    
    return render_template('dashboard.html',
                         total_estudos=total_estudos,
                         revisoes_concluidas=revisoes_concluidas,
                         revisoes_pendentes=revisoes_pendentes,
                         novos_estudos_7d=novos_estudos_7d,
                         revisoes_urgentes=revisoes_urgentes,
                         percentual_concluidas=percentual_concluidas,
                         dias_ativos=dias_ativos,
                         ultima_atividade=ultima_atividade,
                         datas_progresso=datas_progresso,
                         valores_progresso=valores_progresso,
                         datas_progresso_30=datas_progresso_30,
                         valores_progresso_30=valores_progresso_30,
                         datas_total=datas_total,
                         valores_total=valores_total,
                         materias_desempenho=materias_desempenho,
                         labels_tendencias=labels_tendencias,
                         dados_tendencias=dados_tendencias,
                         recomendacoes=recomendacoes)

@app.route('/api/dashboard-data')
def api_dashboard_data():
    if 'usuario_id' not in session:
        return jsonify({'error': 'Não autenticado'})
    
    usuario_id = session['usuario_id']
    
    # Dados básicos para atualização em tempo real
    cursor.execute('SELECT COUNT(*) FROM estudos WHERE usuario_id = ?', (usuario_id,))
    total_estudos = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.feito = 1
    ''', (usuario_id,))
    revisoes_concluidas = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.feito = 0
    ''', (usuario_id,))
    revisoes_pendentes = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM estudos 
        WHERE usuario_id = ? AND data_estudo >= date('now', '-7 days')
    ''', (usuario_id,))
    novos_estudos_7d = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM revisoes r 
        JOIN estudos e ON r.id_estudo = e.id 
        WHERE e.usuario_id = ? AND r.data_revisao = date('now') AND r.feito = 0
    ''', (usuario_id,))
    revisoes_urgentes = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT MIN(data_estudo) FROM estudos WHERE usuario_id = ?
    ''', (usuario_id,))
    primeiro_estudo = cursor.fetchone()[0]
    
    if primeiro_estudo:
        primeiro_dia = datetime.strptime(primeiro_estudo, "%Y-%m-%d")
        dias_ativos = (datetime.now() - primeiro_dia).days + 1
    else:
        dias_ativos = 0
    
    total_revisoes = revisoes_concluidas + revisoes_pendentes
    percentual_concluidas = round((revisoes_concluidas / total_revisoes * 100) if total_revisoes > 0 else 0, 1)
    
    # Dados para gráficos
    datas_progresso = []
    valores_progresso = []
    datas_progresso_30 = []
    valores_progresso_30 = []
    datas_total = []
    valores_total = []
    
    # Últimos 7 dias
    for i in range(6, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        datas_progresso.append(data)
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
        ''', (usuario_id, data))
        valor = cursor.fetchone()[0]
        valores_progresso.append(valor)
    
    # Últimos 30 dias
    for i in range(29, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        datas_progresso_30.append(data)
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
        ''', (usuario_id, data))
        valor = cursor.fetchone()[0]
        valores_progresso_30.append(valor)
    
    # Total acumulado desde o primeiro estudo
    if primeiro_estudo:
        primeiro_dia = datetime.strptime(primeiro_estudo, "%Y-%m-%d")
        dias_totais = (datetime.now() - primeiro_dia).days + 1
        acumulado = 0
        for i in range(dias_totais):
            data = (primeiro_dia + timedelta(days=i)).strftime("%Y-%m-%d")
            datas_total.append(data)
            cursor.execute('''
                SELECT COUNT(*) FROM revisoes r 
                JOIN estudos e ON r.id_estudo = e.id 
                WHERE e.usuario_id = ? AND r.data_revisao = ? AND r.feito = 1
            ''', (usuario_id, data))
            valor = cursor.fetchone()[0]
            acumulado += valor
            valores_total.append(acumulado)
    else:
        datas_total = []
        valores_total = []
    
    # Dados para tendências
    labels_tendencias = ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4']
    dados_tendencias = []
    
    for semana in range(4):
        inicio_semana = (datetime.now() - timedelta(weeks=3-semana)).strftime("%Y-%m-%d")
        fim_semana = (datetime.now() - timedelta(weeks=2-semana)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT COUNT(*) FROM revisoes r 
            JOIN estudos e ON r.id_estudo = e.id 
            WHERE e.usuario_id = ? AND r.data_revisao BETWEEN ? AND ? AND r.feito = 1
        ''', (usuario_id, inicio_semana, fim_semana))
        valor = cursor.fetchone()[0]
        dados_tendencias.append(valor * 10)  # Escalar para melhor visualização
    
    return jsonify({
        'total_estudos': total_estudos,
        'revisoes_concluidas': revisoes_concluidas,
        'revisoes_pendentes': revisoes_pendentes,
        'novos_estudos_7d': novos_estudos_7d,
        'revisoes_urgentes': revisoes_urgentes,
        'percentual_concluidas': percentual_concluidas,
        'dias_ativos': dias_ativos,
        'datas_progresso': datas_progresso,
        'valores_progresso': valores_progresso,
        'datas_progresso_30': datas_progresso_30,
        'valores_progresso_30': valores_progresso_30,
        'datas_total': datas_total,
        'valores_total': valores_total,
        'labels_tendencias': labels_tendencias,
        'dados_tendencias': dados_tendencias
    })

# Nova rota para listar todos os usuários cadastrados
@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Lista todos os usuários cadastrados no sistema"""
    cursor.execute('SELECT id, nome, email, data_criacao FROM usuarios ORDER BY data_criacao DESC')
    usuarios = cursor.fetchall()

    # Formatar os dados para retorno
    usuarios_formatados = []
    for usuario in usuarios:
        usuarios_formatados.append({
            'id': usuario[0],
            'nome': usuario[1],
            'email': usuario[2],
            'data_criacao': usuario[3]
        })

    return jsonify(usuarios_formatados)

if __name__ == '__main__':
    app.run(debug=True)
