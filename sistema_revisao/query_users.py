import sqlite3

conn = sqlite3.connect('revisao_estudos.db')
cursor = conn.cursor()

cursor.execute('SELECT id, nome, email, senha, data_criacao FROM usuarios')
usuarios = cursor.fetchall()

print("Usuários cadastrados:")
for usuario in usuarios:
    print(f"ID: {usuario[0]}, Nome: {usuario[1]}, Email: {usuario[2]}, Senha (hash): {usuario[3]}, Data: {usuario[4]}")

conn.close()
