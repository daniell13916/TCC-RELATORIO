from streamlit.components.v1 import html
import streamlit as st
import psycopg2
import time
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import locale
# Adiciona a imagem de plano de fundo e o estilo para ocupar toda a tela
st.markdown(
    f"""
    <style>
    .stApp {{
        background: url("https://lh3.googleusercontent.com/pw/AP1GczMmpHRnbB_1-qEmLsLsuMQgL7-D3V91nrCKM_WlU4cA4yrPKO2vP8Pj3I_MssP3dlsv7HSLLwDh73kltLTLRm7aX3B5DALLaFlMNMXoCjPa8jhLFWw1vUfJcxqKCo5DK7gawaB45eueEkyEVUmizvVn=w1366-h768-s-no-gm?authuser=0");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(
    host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
    database="postgres",
    user="postgres",
    password="#SEUlixo321"
)

def create_user_table():
    try:
        with conn:
            with conn.cursor() as cur:
                # Criar a tabela de usuários dentro do esquema "public"
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        função VARCHAR(20) NOT NULL,
                        empresa VARCHAR(100) DEFAULT NULL,
                        acesso BOOLEAN DEFAULT FALSE
                    );
                """)
        # Commit a transação após a criação da tabela
        conn.commit()
    except psycopg2.Error as e:
        st.error(f"Erro ao criar tabela de usuários: {e}")
    finally:
        if conn:
            conn.close()

#cria a tabela caso tenha novo cadastro e ela não exista
def create_empresa(nome_empresa):
    try:
        with conn.cursor() as cur:
            # Verificar se a tabela da empresa já existe
            cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (nome_empresa,))
            exists = cur.fetchone()[0]
            if not exists:
                # Criar a tabela da empresa com colunas para cada tipo de resíduo
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS "Dados de coleta".{nome_empresa} (
                        id SERIAL PRIMARY KEY,
                        data DATE NOT NULL,
                        mes INTEGER NOT NULL,
                        ano INTEGER NOT NULL,
                        volume DECIMAL(10, 2) NOT NULL,
                        nome_coletor VARCHAR(100) NOT NULL,
                        plastico INTEGER DEFAULT 0,
                        vidro INTEGER DEFAULT 0,
                        papel INTEGER DEFAULT 0,
                        papelao INTEGER DEFAULT 0,
                        aluminio INTEGER DEFAULT 0,
                        aco INTEGER DEFAULT 0,
                        residuos_eletronicos INTEGER DEFAULT 0,
                        pilhas_baterias INTEGER DEFAULT 0,
                        folhas_galhos INTEGER DEFAULT 0,
                        tetrapak INTEGER DEFAULT 0,
                        pneus INTEGER DEFAULT 0,
                        oleo_cozinha INTEGER DEFAULT 0,
                        cds_dvds INTEGER DEFAULT 0,
                        cartuchos_tinta INTEGER DEFAULT 0,
                        entulho_construcao INTEGER DEFAULT 0,
                        madeira INTEGER DEFAULT 0,
                        paletes INTEGER DEFAULT 0,
                        serragem INTEGER DEFAULT 0,
                        produtos_quimicos INTEGER DEFAULT 0,
                        medicamentos INTEGER DEFAULT 0,
                        lampadas_fluorescentes INTEGER DEFAULT 0,
                        materia_organica INTEGER DEFAULT 0,
                        cobre INTEGER DEFAULT 0
                    );
                """)
                conn.commit()
            else:
                st.warning(f"A tabela para a empresa '{nome_empresa}' já existe.")
    except psycopg2.Error as e:
        st.error(f"Não foi possível criar a tabela para a empresa '{nome_empresa}': {e}")

#adiciona novo usuário na tabela users, podendo sem empresa ou coletor
def add_user(username, email, password, função, empresa=None):
    try:
        if not email:
            raise ValueError("Por favor, insira um endereço de e-mail.")
        if len(username) < 5:
            raise ValueError("O nome de usuário deve ter no mínimo 5 caracteres.")
        if len(password) < 5:
            raise ValueError("A senha deve ter no mínimo 5 caracteres.")
        if função not in ["Coletor", "Empresa", "Administrador"]:
            raise ValueError("Função inválida. Escolha entre 'Coletor', 'Empresa' ou 'Administrador'.")

        with conn.cursor() as cur:
            # Verifica se o nome de usuário ou e-mail já existem na base de dados
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username, email))
            existing_user = cur.fetchone()
            if existing_user:
                raise ValueError("Usuário ou e-mail já cadastrados. Por favor, altere ou utilize os já existentes.")
            
            # Convertendo a empresa para minúsculo se não for None
            empresa_lower = empresa.lower() if empresa else None
            
            cur.execute("INSERT INTO users (username, email, password, função, empresa) VALUES (%s, %s, %s, %s, %s);",
                        (username, email, password, função.capitalize(), empresa_lower))
            
            # Verifica se já existe uma tabela com o nome da empresa em "Dados de coleta"
            if função.lower() == "empresa":
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa_lower,))
                table_exists = cur.fetchone()[0]
                if not table_exists:
                    # Se a tabela não existe, cria ela
                    create_empresa(empresa_lower)
        conn.commit()
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error("Erro ao cadastrar usuário. Por favor, tente novamente mais tarde.")

#para saber se o usuário ta online ou não
def on_session_state_changed():
    if st.session_state.is_session_state_changed:
        if st.session_state.is_session_state_changed:
            # Atualiza o status de login do usuário para False quando a sessão é encerrada
            update_user_login_status(st.session_state.username, False)

# Define a função on_session_state_changed como callback
st.session_state.on_session_state_changed = on_session_state_changed

# Função para atualizar o status de login do usuário
def update_user_login_status(username, is_logged_in):
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET acesso = %s WHERE username = %s;", (is_logged_in, username))
        conn.commit()
    except Exception as e:
        st.error("Erro ao atualizar o status de login do usuário.")

# Função para verificar se o usuário existe no banco de dados usando nome de usuário ou e-mail
def check_user(username_or_email, password):
    with conn.cursor() as cur:
        # Verificar se o nome de usuário ou o e-mail corresponde a um registro no banco de dados
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username_or_email, username_or_email))
        return cur.fetchone() is not None

#<a href="https://im.ge/i/conhinhoes1-1.Ko25Ep"><img src="https://i.im.ge/2024/05/17/Ko25Ep.conhinhoes1-1.md.png" alt="conhinhoes1 1" border="0"></a>

def home():
    st.write(" ")

# Executar o site
home()

def register():
      st.write(" ")
register()

#ve se a tabela já existe e se tiver vai add os dados e se não tiver vai criar tabela com base na função create_empresa
def check_table_existence(senha_empresa, username, dia, mes, ano, volume):
    try:
        # Abrir um cursor para executar consultas SQL
        with conn.cursor() as cur:
            # Consulta SQL para verificar se a senha existe na tabela users e obter o ID e a empresa
            cur.execute("SELECT id, empresa FROM public.users WHERE password = %s;", (senha_empresa,))
            empresa_info = cur.fetchone()
            if empresa_info:
                user_id, empresa = empresa_info
                
                # Verificar a existência da tabela
                cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'Dados de coleta' AND table_name = %s);", (empresa,))
                table_exists = cur.fetchone()[0]
                if table_exists:
                    # Insere os dados na tabela existente
                    cur.execute(f"""
                        INSERT INTO "Dados de coleta".{empresa} (data, mes, ano, volume, nome_coletor)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (f'{ano}-{mes}-{dia}', mes, ano, volume, username))
                    conn.commit()
                    return f"Dados inseridos na tabela '{empresa}'."
                else:
                    return f"A tabela '{empresa}' não existe."
            else:
                # Senha da empresa não encontrada, adicionar link "Criar conta"
                return "Senha da empresa não encontrada. [Criar conta](https://seulixo.streamlit.app/)"
    except psycopg2.Error as e:
        return f"Erro ao conectar ao banco de dados: {e}"

# Função para conectar ao banco de dados PostgreSQL, buscar os valores das colunas para uma linha específica
# e criar um gráfico de pizza com base nesses valores

def buscar_valores_e_criar_grafico(senha, data_inicio, data_fim):
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="#SEUlixo321"
        )

        # Criar um cursor para executar consultas
        cur = conn.cursor()

        # Consulta para obter o nome da empresa da tabela "users" com base na senha fornecida
        cur.execute("""
            SELECT empresa
            FROM users
            WHERE password = %s;
        """, (senha,))
        
        # Obter o nome da empresa
        empresa = cur.fetchone()[0]

        # Verificar se a tabela da empresa existe no esquema "Dados de coleta"
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'Dados de coleta'
                AND table_name = %s
            );
        """, (empresa,))
        
        tabela_existe = cur.fetchone()[0]

        if tabela_existe:
            # Montar a consulta para obter os dados da tabela da empresa no intervalo de tempo especificado
            consulta_dados_empresa = f"""
                SELECT AVG(plastico), AVG(vidro), AVG(papel_e_papelao), AVG(aluminio), AVG(outros_metais), AVG(embalagem_longa_vida)
                FROM "Dados de coleta".{empresa}
                WHERE data >= %s AND data <= %s;
            """
            
            # Executar a consulta para obter os dados da tabela da empresa
            cur.execute(consulta_dados_empresa, (data_inicio, data_fim))
            dados_empresa = cur.fetchone()

            # Fechar o cursor e a conexão com o banco de dados
            cur.close()
            conn.close()

            # Filtrar os valores válidos (diferentes de zero e não None)
            rotulos = [
                "Plástico", "Vidro", "Papel e Papelão", "Alumínio", "Outros Metais",
                "Embalagem Longa Vida"
            ]

            valores_validos = [(rotulo, valor) for rotulo, valor in zip(rotulos, dados_empresa) if valor is not None and valor != 0]

            if valores_validos:
                rotulos_validos, valores = zip(*valores_validos)
                
                # Criar o gráfico de pizza
                plt.figure(figsize=(8, 8))
                plt.pie(valores, labels=rotulos_validos, autopct='%1.1f%%')
                plt.axis('equal')  # Aspecto igual garante que o gráfico seja desenhado como um círculo.

                # Exibir o gráfico
                st.pyplot(plt)
            else:
                st.warning("Não há dados válidos para exibir no gráfico.")

        else:
            st.error(f"A tabela '{empresa}' não existe no esquema 'Dados de coleta'.")

    except psycopg2.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")

def buscar_valores_proporcoes(senha, data_inicio, data_fim):
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="#SEUlixo321"
        )

        # Criar um cursor para executar consultas
        cur = conn.cursor()

        # Consulta para obter o nome da empresa da tabela "users" com base na senha fornecida
        cur.execute("""
            SELECT empresa
            FROM users
            WHERE password = %s;
        """, (senha,))
        
        # Obter o nome da empresa
        empresa = cur.fetchone()[0]

        # Verificar se a tabela da empresa existe no esquema "Dados de coleta"
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'Dados de coleta'
                AND table_name = %s
            );
        """, (empresa,))
        
        tabela_existe = cur.fetchone()[0]

        if tabela_existe:
            # Montar a consulta para obter a soma dos dados da tabela da empresa no intervalo de tempo especificado
            consulta_proporcoes_empresa = f"""
                SELECT 
                    SUM(aluminio), 
                    SUM(papel_e_papelao), 
                    SUM(vidro), 
                    SUM(plastico), 
                    SUM(embalagem_longa_vida), 
                    SUM(outros_metais)
                FROM "Dados de coleta".{empresa}
                WHERE data >= %s AND data <= %s;
            """
            
            # Executar a consulta para obter os dados da tabela da empresa
            cur.execute(consulta_proporcoes_empresa, (data_inicio, data_fim))
            proporcoes = cur.fetchone()

            # Fechar o cursor e a conexão com o banco de dados
            cur.close()
            conn.close()

            return proporcoes

        else:
            st.error(f"A tabela '{empresa}' não existe no esquema 'Dados de coleta'.")
            return None

    except psycopg2.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def buscar_valores_e_criar_grafico(senha, data_inicio, data_fim):
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="#SEUlixo321"
        )

        # Criar um cursor para executar consultas
        cur = conn.cursor()

        # Consulta para obter o nome da empresa da tabela "users" com base na senha fornecida
        cur.execute("""
            SELECT empresa
            FROM users
            WHERE password = %s;
        """, (senha,))
        
        # Obter o nome da empresa
        empresa = cur.fetchone()[0]

        # Verificar se a tabela da empresa existe no esquema "Dados de coleta"
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'Dados de coleta'
                AND table_name = %s
            );
        """, (empresa,))
        
        tabela_existe = cur.fetchone()[0]

        if tabela_existe:
            # Montar a consulta para obter os dados da tabela da empresa no intervalo de tempo especificado
            consulta_dados_empresa = f"""
                SELECT SUM(plastico), SUM(vidro), SUM(papel_e_papelao), SUM(aluminio), SUM(outros_metais), SUM(embalagem_longa_vida), SUM(volume)
                FROM "Dados de coleta".{empresa}
                WHERE data >= %s AND data <= %s;
            """
            
            # Executar a consulta para obter os dados da tabela da empresa
            cur.execute(consulta_dados_empresa, (data_inicio, data_fim))
            dados_empresa = cur.fetchone()

            # Fechar o cursor e a conexão com o banco de dados
            cur.close()
            conn.close()

            if dados_empresa:
                (total_plastico, total_vidro, total_papel_papelao, total_aluminio, total_outros_metais, total_embalagem_longa_vida, total_volume_coletado) = dados_empresa

                if total_volume_coletado is None or total_volume_coletado == 0:
                    st.warning("O total de volume coletado é zero ou não disponível.")
                    return

                # Calcular as proporções de cada tipo de resíduo
                proporcao_plastico = (total_plastico / total_volume_coletado) * 100 if total_plastico is not None else 0
                proporcao_vidro = (total_vidro / total_volume_coletado) * 100 if total_vidro is not None else 0
                proporcao_papel_papelao = (total_papel_papelao / total_volume_coletado) * 100 if total_papel_papelao is not None else 0
                proporcao_aluminio = (total_aluminio / total_volume_coletado) * 100 if total_aluminio is not None else 0
                proporcao_outros_metais = (total_outros_metais / total_volume_coletado) * 100 if total_outros_metais is not None else 0
                proporcao_embalagem_longa_vida = (total_embalagem_longa_vida / total_volume_coletado) * 100 if total_embalagem_longa_vida is not None else 0

                # Filtrar os valores válidos (diferentes de zero e não None)
                rotulos = [
                    "Plástico", "Vidro", "Papel e Papelão", "Alumínio", "Outros Metais", "Embalagem Longa Vida"
                ]

                proporcoes = [
                    proporcao_plastico, proporcao_vidro, proporcao_papel_papelao, proporcao_aluminio, proporcao_outros_metais, proporcao_embalagem_longa_vida
                ]

                valores_validos = [(rotulo, proporcao) for rotulo, proporcao in zip(rotulos, proporcoes) if proporcao > 0]

                if valores_validos:
                    rotulos_validos, valores = zip(*valores_validos)
                    
                    # Criar o gráfico de pizza
                    plt.figure(figsize=(8, 8))
                    plt.pie(valores, labels=rotulos_validos, autopct='%1.1f%%')
                    plt.axis('equal')  # Aspecto igual garante que o gráfico seja desenhado como um círculo.

                    # Exibir o gráfico
                    st.pyplot(plt)
                else:
                    st.warning("Não há dados válidos para exibir no gráfico.")
            else:
                st.warning("Nenhum dado foi encontrado para o intervalo de tempo especificado.")
        else:
            st.error(f"A tabela '{empresa}' não existe no esquema 'Dados de coleta'.")

    except psycopg2.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        
def generate_report(senha_empresa, data_inicio, data_fim):
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            host="seulixo-aws.c7my4s6c6mqm.us-east-1.rds.amazonaws.com",
            database="postgres",
            user="postgres",
            password="#SEUlixo321"
        )
        
        # Abrir um cursor para executar consultas SQL
        with conn.cursor() as cur:
            # Consulta SQL para obter informações da empresa com base na senha fornecida
            cur.execute("SELECT id, empresa FROM public.users WHERE password = %s;", (senha_empresa,))
            empresa_info = cur.fetchone()
            
            if empresa_info:
                user_id, empresa = empresa_info  # Definindo a variável empresa aqui
                
                # Consulta SQL para obter a porcentagem de rejeitos com base na senha fornecida
                cur.execute("""
                    SELECT porcentagem_rejeitos
                    FROM users
                    WHERE password = %s;
                """, (senha_empresa,))
                porcentagem_rejeitos = cur.fetchone()
    
                if porcentagem_rejeitos is not None:
                    porcentagem_rejeitos = float(porcentagem_rejeitos[0])  # Converter para float
    
                    # Consulta SQL para obter os dados de coleta da empresa no período especificado
                    cur.execute(f"""
                        SELECT data, volume
                        FROM "Dados de coleta".{empresa}
                        WHERE data >= %s AND data <= %s;
                    """, (data_inicio, data_fim))
                    coleta_data = cur.fetchall()
    
                    if coleta_data:
                        # Cálculo do total de coletas e volume coletado
                        total_coletas = len(coleta_data)
                        total_volume_coletado = sum(float(row[1]) for row in coleta_data)  # Convertendo para float
                        perda_rejeito = total_volume_coletado * (porcentagem_rejeitos / 100)
                        volume_destinado_corretamente = total_volume_coletado - perda_rejeito
    
                        # Formatação da data do relatório
                        data_relatorio = time.strftime("%d de %B de %Y")
                        
                        # Formatação das datas de início e fim
                        data_inicio_formatada = data_inicio.strftime("%d/%m/%Y")
                        data_fim_formatada = data_fim.strftime("%d/%m/%Y")
                        
                        # Escrita do relatório
                        st.markdown("<h1 style='color: #38b6ff;'>Relatório de Coleta</h1>", unsafe_allow_html=True)
                        st.write("Plano de Gerenciamento de Resíduos Sólidos (PGRS)")
                        st.write(f"Uberlândia, {data_relatorio}")
                        st.write(f"No período entre {data_inicio_formatada} a {data_fim_formatada} foram feitas {total_coletas} coletas, totalizando cerca de {round(total_volume_coletado, 2)} kg coletados.")
                        st.write(f"Foi considerada uma perda de {porcentagem_rejeitos}% de rejeito ou materiais não recicláveis nos recipientes de coleta.")
                        st.write(f"Ao final do período conseguimos destinar corretamente {round(volume_destinado_corretamente, 2)} kg, reinserindo-os na economia circular, através da reciclagem e da compostagem.")
                        st.markdown("<h2 style='color: #38b6ff;'>Análise Gravimétrica</h2>", unsafe_allow_html=True)
                        st.write("Porcentagem de cada tipo de material em relação ao peso total")
    
                        # Chamar a função para buscar os valores das colunas e criar o gráfico
                        buscar_valores_e_criar_grafico(senha_empresa, data_inicio, data_fim)
    
                        # Calcular economias com base nas proporções
                        proporcoes = buscar_valores_proporcoes(senha_empresa, data_inicio, data_fim)
                        if proporcoes:
                            resultado = calcular_economias(*proporcoes, volume_destinado_corretamente)
    
                            # Exibir resultados das economias
                            st.markdown("<h2 style='color: #38b6ff;'>Ganhos Ambientais</h2>", unsafe_allow_html=True)
                            st.write("Dados dos ganhos ambientais na preservação do meio ambiente alcançados com a destinação correta dos resíduos recicláveis e orgânicos.")
    
                            # Dividindo os resultados em uma matriz 3x2
                            num_rows = 3
                            num_cols = 2
                            resultados = list(resultado.items())
    
                            # Dicionário de emojis correspondentes aos diferentes tipos de economias
                            emojis = {
                                "Economia de Energia (kWh)": "💡",
                                "Economia de Água (litros)": "💧",
                                "Redução de CO2 (kg)": "🌍",
                                "Redução de Volume no Aterro (litros)": "♻️",
                                "Economia de Árvores (%)": "🌳",
                                "Economia de Petróleo (litros)": "⛽"
                            }
    
                            for i in range(num_rows):
                                for j in range(num_cols):
                                    index = i * num_cols + j
                                    if index < len(resultados):
                                        chave, valor = resultados[index]
                                        # Adicionar emoji correspondente à economia
                                        emoji = emojis.get(chave, "")
                                        # Criar a moldura com o emoji e o valor
                                        st.markdown(f"<div style='border: 1px solid black; padding: 20px; text-align: center; color: #38b6ff;'>{emoji} {chave}: {valor}</div>", unsafe_allow_html=True)
                                    else:
                                        # Criar uma moldura vazia
                                        st.markdown("<div style='border: 1px solid black; padding: 20px;'></div>", unsafe_allow_html=True)
    
                            # Colorindo os títulos em azul
                            st.markdown(
                                """
                                <style>
                                .title-text {
                                    color: #38b6ff;
                                }
                                </style>
                                """, 
                                unsafe_allow_html=True
                            )
    
                            st.write("Fonte: Cálculos desenvolvidos pelo Cataki em parceria com o Instituto GEA.")
                            st.markdown("<h2 style='color: #38b6ff;'>Gabriela Brant</h2>", unsafe_allow_html=True)
                            st.write("Responsável Técnica Seu Lixo LTDA")
                            st.markdown("<h2 style='color: #38b6ff;'>Alexandre Corrêa</h2>", unsafe_allow_html=True)
                            st.write("Diretor Seu Lixo LTDA")
    
                    else:
                        st.error("Não há dados de coleta para o período especificado.")
            else:
                st.error("Senha da empresa não encontrada.")
            
    except TypeError:
        st.error("Dados sobre as proporções de resíduos ausentes. Peça para o moderador fazer uma avaliação ou inserir os dados após a análise.")
    except psycopg2.Error as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")


# Função para exibir o formulário de coleta
def collection_form():
    st.markdown("<h1 style='color: #38b6ff;'>Relatório de Coleta</h1>", unsafe_allow_html=True)
    with st.form("registro_coleta_form"):
        st.write("Plano de Gerenciamento de Resíduos Sólidos (PGRS)")
        username = st.text_input("Nome do Coletor")
        dia = st.number_input("Dia", min_value=1, max_value=31)
        mes = st.number_input("Mês", min_value=1, max_value=12)
        ano = st.number_input("Ano", min_value=2024)
        volume = st.number_input("Volume Coletado (Kg)", min_value=0.01)
        senha_empresa = st.text_input("Senha da Empresa", type="password")

        submit_button_cadastro = st.form_submit_button("Registrar Coleta")
        if submit_button_cadastro:
            result_message = check_table_existence(senha_empresa, username, dia, mes, ano, volume)
            st.write(result_message)

    with st.form("gerar_relatorio_form"):
        st.markdown("<h1 style='color: #38b6ff;'>Gerar Relatório</h1>", unsafe_allow_html=True)
        data_inicio = st.date_input("Data de Início")
        data_fim = st.date_input("Data Final")
        senha_relatorio = st.text_input("Senha da Empresa para Relatório", type="password")
        submit_button_relatorio = st.form_submit_button("Gerar Relatório")
        
        if submit_button_relatorio:
            generate_report(senha_relatorio, data_inicio, data_fim)

collection_form()

# Criar a tabela de usuários se ainda não existir
create_user_table()

# Executar o site
home()
