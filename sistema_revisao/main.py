import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def gerar_grafico_desempenho():
    cursor.execute('''
    SELECT resultado, COUNT(*) FROM desempenho
    GROUP BY resultado
    ''')
    dados = cursor.fetchall()

    if not dados:
        print("\n📉 Ainda não há dados de desempenho registrados.")
        return

    categorias = [row[0] for row in dados]
    quantidades = [row[1] for row in dados]

    cores = []
    for cat in categorias:
        if cat == "Lembrei bem":
            cores.append("green")
        elif cat == "Dificuldade":
            cores.append("orange")
        elif cat == "Errei":
            cores.append("red")
        else:
            cores.append("gray")

    plt.figure(figsize=(8,5))
    plt.bar(categorias, quantidades, color=cores)
    plt.title("📊 Desempenho nas Revisões")
    plt.xlabel("Resultado")
    plt.ylabel("Quantidade")
    plt.tight_layout()
    plt.savefig("grafico_desempenho.png")
    plt.show()

# Conectar ou criar o banco de dados
conn = sqlite3.connect("revisao_estudos.db")
cursor = conn.cursor()

# Criar as tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS estudos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia TEXT NOT NULL,
    topico TEXT NOT NULL,
    data_estudo TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS revisoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudo INTEGER,
    data_revisao TEXT NOT NULL,
    tipo TEXT NOT NULL,
    feito INTEGER DEFAULT 0,
    FOREIGN KEY (id_estudo) REFERENCES estudos(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS desempenho (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_revisao INTEGER,
    resultado TEXT,
    data_registro TEXT,
    FOREIGN KEY (id_revisao) REFERENCES revisoes(id)
)
''')
conn.commit()

# Função para cadastrar novo estudo
def cadastrar_estudo():
    materia = input("Matéria: ")
    topico = input("Tópico: ")
    data_input = input("Data do estudo (dd/mm/aaaa): ")
    data_estudo = datetime.strptime(data_input, "%d/%m/%Y")

    # Inserir o estudo na tabela
    cursor.execute('INSERT INTO estudos (materia, topico, data_estudo) VALUES (?, ?, ?)',
                   (materia, topico, data_estudo.strftime("%Y-%m-%d")))
    id_estudo = cursor.lastrowid

    # Datas das revisões
    dias = [1, 3, 7, 14, 30]
    for i, d in enumerate(dias):
        data_rev = (data_estudo + timedelta(days=d)).strftime("%Y-%m-%d")
        tipo = f"Rev{i+1}"
        cursor.execute('INSERT INTO revisoes (id_estudo, data_revisao, tipo) VALUES (?, ?, ?)',
                       (id_estudo, data_rev, tipo))

    conn.commit()
    print("✅ Estudo e revisões cadastrados com sucesso!\n")

# Função para mostrar revisões do dia
def mostrar_revisoes_hoje():
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
    SELECT estudos.materia, estudos.topico, revisoes.tipo
    FROM revisoes
    JOIN estudos ON revisoes.id_estudo = estudos.id
    WHERE revisoes.data_revisao = ? AND revisoes.feito = 0
    ''', (hoje,))
    resultados = cursor.fetchall()

    print(f"\n📅 Revisões para hoje ({datetime.now().strftime('%d/%m/%Y')}):")
    if resultados:
        for r in resultados:
            print(f"- {r[0]} | {r[1]} ({r[2]})")
    else:
        print("Nenhuma revisão pendente para hoje.")

def marcar_revisao_como_feita():
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
    SELECT revisoes.id, estudos.materia, estudos.topico, revisoes.tipo
    FROM revisoes
    JOIN estudos ON revisoes.id_estudo = estudos.id
    WHERE revisoes.data_revisao = ? AND revisoes.feito = 0
    ''', (hoje,))
    resultados = cursor.fetchall()

    if not resultados:
        print("\n✅ Nenhuma revisão pendente para hoje.")
        return

    print(f"\n📌 Revisões pendentes para hoje ({datetime.now().strftime('%d/%m/%Y')}):")
    for i, (rev_id, materia, topico, tipo) in enumerate(resultados, start=1):
        print(f"{i}. {materia} | {topico} ({tipo})")

    try:
        escolha = int(input("\nDigite o número da revisão que você concluiu (ou 0 para cancelar): "))
        if escolha == 0:
            print("❌ Cancelado.")
            return

        revisao_id = resultados[escolha - 1][0]

        # Marcar como feita
        cursor.execute('UPDATE revisoes SET feito = 1 WHERE id = ?', (revisao_id,))
        conn.commit()
        print("✅ Revisão marcada como feita!")

        # Registrar desempenho
        print("\n🧠 Como foi seu desempenho?")
        print("1 - Lembrei bem")
        print("2 - Tive dificuldade")
        print("3 - Errei")
        op = input("Escolha uma opção: ")

        resultados_map = {"1": "Lembrei bem", "2": "Dificuldade", "3": "Errei"}
        resultado = resultados_map.get(op, "Não informado")

        cursor.execute('''
        INSERT INTO desempenho (id_revisao, resultado, data_registro)
        VALUES (?, ?, ?)
        ''', (revisao_id, resultado, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        print("📊 Desempenho registrado com sucesso!\n")

    except (ValueError, IndexError):
        print("❌ Entrada inválida.")

# Menu
def main():
    while True:
        print("\n=== Sistema de Revisão com Banco de Dados ===")
        print("1. Cadastrar novo estudo")
        print("2. Ver revisões do dia")
        print("3. Marcar revisão como feita")
        print("4. Ver gráfico de desempenho")
        print("5. Sair")
        op = input("Escolha uma opção: ")
        if op == "1":
            cadastrar_estudo()
        elif op == "2":
            mostrar_revisoes_hoje()
        elif op == "3":
            marcar_revisao_como_feita()
        elif op == "4":
            gerar_grafico_desempenho()
        elif op == "5":
            print("Saindo... 👋")
            break
        else:
            print("Opção inválida.")

main()
conn.close()