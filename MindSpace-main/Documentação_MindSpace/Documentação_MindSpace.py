#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pyodbc
import openai
import os
#As bibliotecas 'pyodbc', 'openai' e 'os' são importadas para permitir o uso de recursos como a conexão com banco de dados SQL Server,
#a integração com a API da OpenAI e operações do sistema operacional, respectivamente.
class Usuario:
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email
#A classe Usuario é definida para representar um usuário do chatbot.
#Ela possui três atributos: id, nome e email, que são atribuídos ao objeto durante a inicialização.
class MentalHealthChatbot:
    def __init__(self):
        self.connection_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:SEU DATABASE,1433;Database=QUAL DATABASE;Uid=USUARIO;Pwd={SUA SENHA};"
        self.openai_api_key = 'SUA_CHAVE_API'
        self.openai_engine = 'text-davinci-003'
        self.logged_in_user = None
#A classe MentalHealthChatbot é a classe principal que implementa o chatbot. Ela possui os seguintes atributos:

#connection_string: uma string de conexão para estabelecer uma conexão com o banco de dados SQL Server.
#openai_api_key: uma chave de API para autenticar a comunicação com a plataforma OpenAI.
#openai_engine: o motor OpenAI a ser utilizado para gerar respostas do chatbot.
#logged_in_user: um objeto Usuario que representa o usuário atualmente logado.
    def establish_connection(self):
        conn = pyodbc.connect(self.connection_string)
        return conn
#O método establish_connection é usado para estabelecer uma conexão com o banco de dados usando a string de conexão definida anteriormente.
#Ele retorna o objeto de conexão.
    def create_tables(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='usuarios')
            CREATE TABLE usuarios (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nome NVARCHAR(100),
                email NVARCHAR(100),
                senha NVARCHAR(50)
            )
        ''')

        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='conversas')
            CREATE TABLE conversas (
                id INT IDENTITY(1,1) PRIMARY KEY,
                usuario_id INT,
                usuario_input NVARCHAR(MAX),
                resposta_chatbot NVARCHAR(MAX),
                Data DATETIME,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        ''')
        cursor.close()
#O método create_tables é responsável por criar as tabelas necessárias no banco de dados, caso elas não existam.
#Ele executa duas instruções SQL para criar as tabelas "usuarios" e "conversas" com suas respectivas colunas.
    def login(self):
        email = input("Digite seu email: ")
        senha = input("Digite sua senha: ")

        conn = self.establish_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM usuarios WHERE email=? AND senha=?', (email, senha))
        user_row = cursor.fetchone()
        cursor.close()

        if user_row:
            user = Usuario(user_row.id, user_row.nome, user_row.email)
            self.logged_in_user = user
            print(f"Bem-vindo(a), {user.nome}!")
        else:
            print("Credenciais inválidas.")
#O método login permite que um usuário faça login no chatbot.
#Ele solicita ao usuário que digite seu email e senha,
#verifica se as credenciais correspondem a um usuário existente no banco de dados e,
#se for o caso, atribui o usuário logado ao atributo logged_in_user.
    def register(self):
        nome = input("Digite seu nome: ")
        email = input("Digite seu email: ")
        senha = input("Digite uma senha: ")

        conn = self.establish_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
        conn.commit()
        cursor.close()

        print("Cadastro realizado com sucesso!")
#O método register permite que um novo usuário se cadastre no chatbot. Ele solicita ao usuário que digite seu nome, email e senha,
#insere essas informações na tabela "usuarios" do banco de dados e imprime uma mensagem informando que o cadastro foi realizado com sucesso.
    def generate_response(self, user_input):
        openai.api_key = self.openai_api_key

        response = openai.Completion.create(
            engine=self.openai_engine,
            prompt=user_input,
            max_tokens=3000,
            temperature=0.7,
            n=1,
            stop=None,
            timeout=15
        )

        response_text = response.choices[0].text.strip()
        return response_text
#O método generate_response gera uma resposta para uma entrada do usuário usando a API da OpenAI.
#Ele envia a entrada do usuário como um prompt para a API e obtém uma resposta. O texto da resposta é retornado como resultado.
    def store_conversation(self, conn, user_input, bot_response):
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversas (id_usuario, usuario_input, resposta_chatbot, Data)
            VALUES (?, ?, ?, GETUTCDATE())
        ''', (self.logged_in_user.id, user_input, bot_response))
        conn.commit()
        cursor.close()
#O método store_conversation é usado para armazenar uma conversa no banco de dados.
#Ele insere uma nova linha na tabela "conversas" com o ID do usuário, a entrada do usuário, a resposta do chatbot e a data atual.
    def run(self):
        conn = self.establish_connection()
        self.create_tables(conn)

        print("\nSeja bem-vindo(a)! Estou aqui para te ajudar!")
        print("\nDigite 'sair' a qualquer momento para encerrar o chat.")
        print("\nDica: Fale sobre o que está sentindo hoje, mas se preferir pode perguntar sobre algum outro assunto!")

        while True:
            if not self.logged_in_user:
                choice = input("\nVocê deseja fazer login (L) ou cadastrar-se (C)? ").lower()

                if choice == 'l':
                    self.login()
                elif choice == 'c':
                    self.register()

            if self.logged_in_user:
                user_input = input("\nUsuário: ")

                if user_input.lower() == 'sair':
                    print("Chat encerrado.")
                    break

                bot_response = self.generate_response(user_input)
                self.store_conversation(conn, user_input, bot_response)

                print("\nMindSpace: " + bot_response)

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conversas')
        conversations = cursor.fetchall()
        print("Conversas armazenadas:")
        for conversation in conversations:
            print(f"Usuário: {conversation.usuario_input}")
            print(f"Chatbot: {conversation.resposta_chatbot}")
            print()

        cursor.close()
        conn.close()
#O método run é o ponto de entrada do chatbot. Ele inicia a conexão com o banco de dados, cria as tabelas se necessário e exibe uma mensagem de boas-vindas ao usuário.
#Em seguida, inicia um loop no qual o usuário pode fazer login, se cadastrar, enviar mensagens ao chatbot e receber respostas.

#Se um usuário estiver logado, a entrada do usuário é processada, uma resposta é gerada usando o método generate_response
#e a conversa é armazenada no banco de dados usando o método store_conversation. A resposta do chatbot é exibida na saída.

#Depois que o loop é encerrado, todas as conversas armazenadas no banco de dados são exibidas na saída.
if __name__ == '__main__':
    chatbot = MentalHealthChatbot()
    chatbot.run()
#O trecho final do código cria uma instância do chatbot e chama o método run para iniciar a execução do programa quando o arquivo Python é executado diretamente.
#Isso permite que o chatbot seja executado como um aplicativo independente.

#Essa é uma visão geral da estrutura e funcionalidades do código Python fornecido. Espero que isso ajude você a entender melhor o que o código faz e como ele está organizado.

