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
                SELECT 
                    COALESCE(SUM(volume), 0) AS volume_total,
                    COALESCE(SUM(plastico), 0) AS plastico,
                    COALESCE(SUM(vidro), 0) AS vidro,
                    COALESCE(SUM(papel_e_papelao), 0) AS papel_e_papelao,
                    COALESCE(SUM(aluminio), 0) AS aluminio,
                    COALESCE(SUM(outros_metais), 0) AS outros_metais,
                    COALESCE(SUM(embalagem_longa_vida), 0) AS embalagem_longa_vida,
                    COALESCE(SUM(volume), 0) - COALESCE(SUM(plastico), 0) - COALESCE(SUM(vidro), 0) - COALESCE(SUM(papel_e_papelao), 0) - COALESCE(SUM(aluminio), 0) - COALESCE(SUM(outros_metais), 0) - COALESCE(SUM(embalagem_longa_vida), 0) AS nao_reciclado
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
                "Embalagem Longa Vida", "Não Reciclado"
            ]

            valores_validos = [(rotulo, valor) for rotulo, valor in zip(rotulos, dados_empresa[1:]) if valor is not None and valor != 0]

            if valores_validos:
                rotulos_validos, valores = zip(*valores_validos)
                
                # Criar o gráfico de pizza
                plt.figure(figsize=(8, 8))
                plt.pie(valores, labels=rotulos_validos, autopct='%1.1f%%')
                plt.axis('equal')  # Aspecto igual garante que o gráfico seja desenhado como um círculo.

                # Exibir o gráfico
                st.pyplot(plt)

            return dados_empresa  # Retornar todos os valores calculados

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

def calcular_economias( aluminio, papel_papelao, vidro, plastico, embalagem_longa_vida, outros_metais, volume_destinado_corretamente):
    # Calcular peso de cada tipo de resíduo
    peso_aluminio = float(aluminio) if aluminio is not None else 0
    peso_papel_papelao = float(papel_papelao) if papel_papelao is not None else 0
    peso_vidro = float(vidro) if vidro is not None else 0
    peso_plastico = float(plastico) if plastico is not None else 0
    peso_embalagem_longa_vida = float(embalagem_longa_vida) if embalagem_longa_vida is not None else 0
    peso_outros_metais = float(outros_metais) if outros_metais is not None else 0
   
    # Proporções fornecidas pelo Cataki
    proporcoes = {
        "papel_papelao": {"energia": 2.5, "agua": 48, "co2": 3.47, "volume_aterrro": 1.74, "arvores": 0.02, "petroleo": 0.4},
        "vidro": {"energia": 0.64, "agua": 0.5, "co2": 0.28, "volume_aterrro": 1.2, "arvores": 0, "petroleo": 0},
        "plastico": {"energia": 5.3, "agua": 0.45, "co2": 1.21, "volume_aterrro": 3.14, "arvores": 0, "petroleo": 1},
        "embalagem_longa_vida": {"energia": 5.55, "agua": 34.65, "co2": 2.96, "volume_aterrro": 2.34, "arvores": 0.014, "petroleo": 0.53},
        "outros_metais": {"energia": 6.56, "agua": 5.36, "co2": 1.93, "volume_aterrro": 1.98, "arvores": 0, "petroleo": 0},
        "aluminio": {"energia": 48.46, "agua": 18.69, "co2": 4.62, "volume_aterrro": 6.74, "arvores": 0, "petroleo": 0}
    }

    # Inicializar economias como zero
    economia_energia = 0
    economia_agua = 0
    economia_co2 = 0
    economia_volume_aterrro = 0
    economia_arvores = 0
    economia_petroleo = 0

    # Calcular economias com base nas proporções
    economia_energia += peso_papel_papelao * proporcoes["papel_papelao"]["energia"]
    economia_energia += peso_vidro * proporcoes["vidro"]["energia"]
    economia_energia += peso_plastico * proporcoes["plastico"]["energia"]
    economia_energia += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["energia"]
    economia_energia += peso_outros_metais * proporcoes["outros_metais"]["energia"]
    economia_energia += peso_aluminio * proporcoes["aluminio"]["energia"]

    economia_agua += peso_papel_papelao * proporcoes["papel_papelao"]["agua"]
    economia_agua += peso_vidro * proporcoes["vidro"]["agua"]
    economia_agua += peso_plastico * proporcoes["plastico"]["agua"]
    economia_agua += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["agua"]
    economia_agua += peso_outros_metais * proporcoes["outros_metais"]["agua"]
    economia_agua += peso_aluminio * proporcoes["aluminio"]["agua"]

    economia_co2 += peso_papel_papelao * proporcoes["papel_papelao"]["co2"]
    economia_co2 += peso_vidro * proporcoes["vidro"]["co2"]
    economia_co2 += peso_plastico * proporcoes["plastico"]["co2"]
    economia_co2 += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["co2"]
    economia_co2 += peso_outros_metais * proporcoes["outros_metais"]["co2"]
    economia_co2 += peso_aluminio * proporcoes["aluminio"]["co2"]

    economia_volume_aterrro += peso_papel_papelao * proporcoes["papel_papelao"]["volume_aterrro"]
    economia_volume_aterrro += peso_vidro * proporcoes["vidro"]["volume_aterrro"]
    economia_volume_aterrro += peso_plastico * proporcoes["plastico"]["volume_aterrro"]
    economia_volume_aterrro += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["volume_aterrro"]
    economia_volume_aterrro += peso_outros_metais * proporcoes["outros_metais"]["volume_aterrro"]
    economia_volume_aterrro += peso_aluminio * proporcoes["aluminio"]["volume_aterrro"]

    economia_arvores += peso_papel_papelao * proporcoes["papel_papelao"]["arvores"]
    economia_arvores += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["arvores"]

    economia_petroleo += peso_papel_papelao * proporcoes["papel_papelao"]["petroleo"]
    economia_petroleo += peso_plastico * proporcoes["plastico"]["petroleo"]
    economia_petroleo += peso_embalagem_longa_vida * proporcoes["embalagem_longa_vida"]["petroleo"]

    return {
        "Economia de Energia (kWh)": round(economia_energia, 2),
        "Economia de Água (litros)": round(economia_agua, 2),
        "Redução de CO2 (kg)": round(economia_co2, 2),
        "Redução de Volume no Aterro (litros)": round(economia_volume_aterrro, 2),
        "Economia de Árvores (%)": round(economia_arvores, 2),
        "Economia de Petróleo (litros)": round(economia_petroleo, 2)
    }

# Função para gerar o relatório
def generate_report(senha_empresa, data_inicio, data_fim, dados_empresa):
    try:
        if dados_empresa:
            # Realizar cálculos com base nos dados obtidos
            volume_total = dados_empresa[0]
            nao_reciclado = dados_empresa[7]
            volume_destinado_corretamente = volume_total - nao_reciclado
            total_coletas = len(dados_empresa)
            
            # Formatação da data do relatório
            data_relatorio = time.strftime("%d de %B de %Y")
            data_inicio_formatada = data_inicio.strftime("%d/%m/%Y")
            data_fim_formatada = data_fim.strftime("%d/%m/%Y")
            
            # Escrita do relatório
            st.markdown("<h1 style='color: #38b6ff;'>Relatório de Coleta</h1>", unsafe_allow_html=True)
            st.write("Plano de Gerenciamento de Resíduos Sólidos (PGRS)")
            st.write(f"Uberlândia, {data_relatorio}")
            st.write(f"No período entre {data_inicio_formatada} a {data_fim_formatada} foram feitas {total_coletas} coletas, totalizando cerca de {round(volume_total, 2)} kg coletados.")
            st.write(f"Foi considerada uma perda de {round(nao_reciclado, 2)} kg de rejeito ou materiais não recicláveis nos recipientes de coleta.")
            st.write(f"Ao final do período conseguimos destinar corretamente {round(volume_destinado_corretamente, 2)} kg, reinserindo-os na economia circular, através da reciclagem e da compostagem.")
    
            # Calcular economias com base nas proporções
            proporcoes = buscar_valores_proporcoes(senha_empresa, data_inicio, data_fim)
            if proporcoes:
                resultado = calcular_economias(*proporcoes, volume_destinado_corretamente)
    
                # Exibir resultados das economias (exemplo de código, ajuste conforme necessário)
                st.markdown("<h2 style='color: #38b6ff;'>Ganhos Ambientais</h2>", unsafe_allow_html=True)
                for chave, valor in resultado.items():
                    st.write(f"{chave}: {valor}")
                    
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
    
    except TypeError:
        st.error("Dados sobre as proporções de resíduos ausentes. Peça para o moderador fazer uma avaliação ou inserir os dados após a análise.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")

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
            # Buscar os dados uma vez antes de chamar generate_report
            dados_empresa = buscar_valores_e_criar_grafico(senha_empresa, data_inicio, data_fim)
            generate_report(senha_relatorio, data_inicio, data_fim, dados_empresa)

# Chamada para iniciar o formulário de coleta
collection_form()

# Criar a tabela de usuários se ainda não existir
create_user_table()

# Executar o site
home()
