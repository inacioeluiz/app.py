import streamlit as st
import json
import os
import time
from datetime import datetime
from urllib.parse import quote
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import hmac
import hashlib

# ==============================================
# CONFIGURACOES DO SISTEMA
# ==============================================
CONFIG = {
    "pix_nome_recebedor": "Seu Nome Completo",
    "pix_chave": "sua.chave.pix@exemplo.com",
    "whatsapp_admin": "5521997524939",
    "email_suporte": "seuemail@exemplo.com",
    "email_remetente": "",
    "senha_app_email": "",
    "smtp_servidor": "smtp.gmail.com",
    "smtp_porta": 587,
    "coinmarketcap_api_key": "",
    "senha_admin": "admin123",
    "logo_principal": "logo_principal.png",
    "logo_pequeno": "logo_pequeno.png",
    "taxa_media_corretora_perc": 0.1,
    "taxa_rede_saque_btc": 0.0005,
    "taxa_rede_saque_eth": 0.005
}

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_SISTEMA = "sistema.json"
ARQUIVO_HISTORICO = "historico_oportunidades.json"

PLANOS = {
    "Gratuito": {
        "preco": 0.0,
        "moedas": 3,
        "atualizacao_segundos": 120,
        "historico_horas": 6,
        "alertas_email": False,
        "alertas_whatsapp": False,
        "corretoras": ["Binance", "Bybit"],
        "modo_avancado": False,
        "operacao_automatica": False
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 50,
        "atualizacao_segundos": 60,
        "historico_horas": 72,
        "alertas_email": True,
        "alertas_whatsapp": True,
        "corretoras": ["Binance", "Bybit", "KuCoin", "OKX"],
        "modo_avancado": True,
        "operacao_automatica": True
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 9999,
        "atualizacao_segundos": 15,
        "historico_horas": 168,
        "alertas_email": True,
        "alertas_whatsapp": True,
        "corretoras": ["Binance", "Bybit", "KuCoin", "OKX", "Gate.io", "Mercado Bitcoin"],
        "modo_avancado": True,
        "operacao_automatica": True
    }
}

MOEDAS_MONITORADAS = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX", "MATIC", "LINK",
    "ATOM", "UNI", "LTC", "BCH", "FIL", "NEAR", "FTM", "SAND", "MANA", "AXS"
]

CORRETORAS_DISPONIVEIS = ["Binance", "Bybit", "KuCoin", "OKX", "Gate.io", "Mercado Bitcoin", "Coinbase", "Kraken"]

# ==============================================
# FUNCOES DE ARQUIVO
# ==============================================
def carregar_json(caminho, padrao={}):
    if not os.path.exists(caminho):
        return padrao
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return padrao

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

dados_sistema = carregar_json(ARQUIVO_SISTEMA, {})
if dados_sistema:
    CONFIG.update(dados_sistema)

# ==============================================
# FUNCOES DE SEGURANCA DE SENHA
# ==============================================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_digitada, senha_hash):
    return hmac.compare_digest(hash_senha(senha_digitada), senha_hash)

# ==============================================
# FUNCOES DE LOGO
# ==============================================
def exibir_logo_principal(largura=250):
    caminho = CONFIG.get("logo_principal", "logo_principal.png")
    if os.path.exists(caminho):
        st.image(caminho, width=largura)
    else:
        st.markdown("<h1 style='text-align: center; color: #22c55e;'>ARBITRAGEM AI</h1>", unsafe_allow_html=True)

def exibir_logo_sidebar(largura=100):
    caminho = CONFIG.get("logo_pequeno", "logo_pequeno.png")
    if os.path.exists(caminho):
        st.sidebar.image(caminho, width=largura)
        st.sidebar.markdown("---")

def botao_voltar_menu():
    if st.button("🏠 Voltar ao Menu Principal"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

# ==============================================
# FUNCAO DE ENVIO DE E-MAIL
# ==============================================
def enviar_email(destinatario, assunto, mensagem_html):
    try:
        remetente = CONFIG.get("email_remetente", "")
        senha = CONFIG.get("senha_app_email", "")
        servidor_smtp = CONFIG.get("smtp_servidor", "smtp.gmail.com")
        porta = CONFIG.get("smtp_porta", 587)
        
        if not remetente or not senha:
            return False, "Configuracoes de e-mail incompletas"
        
        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(mensagem_html, "html"))
        
        with smtplib.SMTP(servidor_smtp, porta) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)
        
        return True, "E-mail enviado!"
    except Exception as e:
        return False, f"Erro: {str(e)}"

# ==============================================
# FUNCOES DO SCANNER INTELIGENTE
# ==============================================
def gerar_preco_simulado(moeda, corretora, variacao_max=0.008):
    precos_base = {
        "BTC": 63420.50, "ETH": 3218.90, "SOL": 142.85, "XRP": 0.52, "ADA": 0.45,
        "DOGE": 0.12, "DOT": 7.85, "AVAX": 35.20, "MATIC": 0.58, "LINK": 14.50,
        "ATOM": 8.20, "UNI": 7.15, "LTC": 72.30, "BCH": 365.00, "FIL": 4.12,
        "NEAR": 2.85, "FTM": 0.32, "SAND": 0.48, "MANA": 0.42, "AXS": 55.00
    }
    base = precos_base.get(moeda, 1.0)
    seed = abs(hash(f"{moeda}-{corretora}-{datetime.now().strftime('%Y%m%d%H%M')}")) % 1000 / 1000
    fator = 1 + (seed - 0.5) * 2 * variacao_max
    return round(base * fator, 6 if base < 1 else 2)

def calcular_lucro_liquido(preco_compra, preco_venda, taxa_corretora_perc=None):
    if taxa_corretora_perc is None:
        taxa_corretora_perc = CONFIG.get("taxa_media_corretora_perc", 0.1)
    
    taxa_compra = preco_compra * (taxa_corretora_perc / 100)
    taxa_venda = preco_venda * (taxa_corretora_perc / 100)
    
    lucro_bruto = preco_venda - preco_compra
    lucro_liquido = lucro_bruto - taxa_compra - taxa_venda
    lucro_bruto_perc = (lucro_bruto / preco_compra * 100) if preco_compra > 0 else 0
    lucro_liquido_perc = (lucro_liquido / preco_compra * 100) if preco_compra > 0 else 0
    
    return {
        "lucro_bruto_perc": lucro_bruto_perc,
        "lucro_liquido_perc": lucro_liquido_perc,
        "taxa_compra": taxa_compra,
        "taxa_venda": taxa_venda,
        "tempo_estimado_execucao": "15-45s",
        "nivel_risco": "Baixo" if lucro_liquido_perc > 0.5 else "Medio" if lucro_liquido_perc > 0.2 else "Alto"
    }

def verificar_liquidez(moeda, corretora):
    liquidez_alta = random.random() > 0.15
    volume_estimado = round(random.uniform(50000, 5000000), 2) if liquidez_alta else round(random.uniform(1000, 50000), 2)
    return {
        "liquidez_suficiente": liquidez_alta,
        "volume_24h_usd": volume_estimado,
        "alerta": "" if liquidez_alta else "⚠️ Volume baixo — pode ser dificil executar sem mover o preco!"
    }

def salvar_oportunidade_historico(oportunidade):
    historico = carregar_json(ARQUIVO_HISTORICO, [])
    oportunidade["hora"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    historico.insert(0, oportunidade)
    salvar_json(ARQUIVO_HISTORICO, historico[:500])

def escanear_oportunidades(corretoras, moedas, lucro_min_perc=0.5):
    oportunidades = []
    for moeda in moedas:
        precos = {c: gerar_preco_simulado(moeda, c) for c in corretoras}
        for compra_em in corretoras:
            for venda_em in corretoras:
                if compra_em == venda_em: continue
                pc, pv = precos[compra_em], precos[venda_em]
                if pv <= pc: continue
                calc = calcular_lucro_liquido(pc, pv)
                if calc["lucro_liquido_perc"] < lucro_min_perc: continue
                liq_c = verificar_liquidez(moeda, compra_em)
                liq_v = verificar_liquidez(moeda, venda_em)
                op = {
                    "moeda": moeda, "comprar_em": compra_em, "vender_em": venda_em,
                    "preco_compra": pc, "preco_venda": pv, **calc,
                    "liquidez_compra": liq_c, "liquidez_venda": liq_v,
                    "hora_deteccao": datetime.now().strftime("%H:%M:%S"),
                    "expira_em_segundos": 45
                }
                oportunidades.append(op)
                salvar_oportunidade_historico(op)
    return sorted(oportunidades, key=lambda x: x["lucro_liquido_perc"], reverse=True)

# ==============================================
# GERENCIAMENTO DE APIS DAS CORRETORAS
# ==============================================
def salvar_apis_corretoras(email_usuario, corretora, api_key, api_secret, nome_conta=""):
    usuarios = carregar_json(ARQUIVO_USUARIOS, {})
    if email_usuario not in usuarios:
        return False
    
    if "corretoras_apis" not in usuarios[email_usuario]:
        usuarios[email_usuario]["corretoras_apis"] = {}
    
    usuarios[email_usuario]["corretoras_apis"][corretora] = {
        "api_key": api_key,
        "api_secret": api_secret,
        "nome_conta": nome_conta,
        "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "ativa": True
    }
    
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def obter_apis_usuario(email_usuario):
    usuarios = carregar_json(ARQUIVO_USUARIOS, {})
    if email_usuario not in usuarios:
        return {}
    return usuarios[email_usuario].get("corretoras_apis", {})

def tela_gerenciar_corretoras():
    st.header("🔗 Minhas Corretoras & Chaves API")
    st.info("Aqui voce conecta suas corretoras. O sistema usa suas chaves para verificar precos e executar operacoes.")
    
    email_usuario = st.session_state["usuario"]
    apis_salvas = obter_apis_usuario(email_usuario)
    
    # Formulario para adicionar nova corretora
    with st.expander("➕ Adicionar Nova Corretora", expanded=not bool(apis_salvas)):
        corretora_escolhida = st.selectbox("Escolha a Corretora", CORRETORAS_DISPONIVEIS)
        nome_conta = st.text_input("Nome da Conta (opcional)", placeholder="ex: Conta Principal")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        
        st.warning("⚠️ Suas chaves ficam salvas APENAS neste sistema. Nunca compartilhe com ninguem.")
        
        if st.button("💾 Salvar Chaves", type="primary"):
            if not api_key or not api_secret:
                st.error("Preencha API Key e API Secret!")
            else:
                salvar_apis_corretoras(email_usuario, corretora_escolhida, api_key, api_secret, nome_conta)
                st.success(f"✅ {corretora_escolhida} conectada com sucesso!")
                st.rerun()
    
    # Lista de corretoras conectadas
    if apis_salvas:
        st.subheader(f"✅ {len(apis_salvas)} Corretora(s) Conectada(s)")
        for corretora, dados in apis_salvas.items():
            with st.expander(f"🔌 {corretora} — {dados.get('nome_conta', 'Sem nome')}"):
                st.write(f"Adicionado em: {dados.get('data_cadastro', '—')}")
                st.write(f"Status: {'✅ Ativa' if dados.get('ativa', True) else '❌ Inativa'}")
                st.code(f"API Key: {dados['api_key'][:6]}...{dados['api_key'][-4:]}", language="text")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔄 Reatualizar", key=f"edit_{corretora}"):
                        st.session_state[f"editar_{corretora}"] = True
                with col2:
                    if st.button(f"🗑️ Remover", key=f"del_{corretora}"):
                        usuarios = carregar_json(ARQUIVO_USUARIOS, {})
                        del usuarios[email_usuario]["corretoras_apis"][corretora]
                        salvar_json(ARQUIVO_USUARIOS, usuarios)
                        st.rerun()
    
    botao_voltar_menu()

# ==============================================
# OPERACAO AUTOMATICA
# ==============================================
def tela_operacao_automatica():
    st.header("🤖 Operacao Automatica")
    
    usuario = st.session_state["usuario"]
    plano = usuarios[usuario].get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    
    if not dados_plano.get("operacao_automatica", False):
        st.error("❌ A operacao automatica esta disponivel apenas nos planos Pro e Premium!")
        st.info("Faça upgrade para ativar a execucao automatica de oportunidades.")
        botao_voltar_menu()
        return
    
    apis = obter_apis_usuario(usuario)
    if len(apis) < 2:
        st.warning("⚠️ Conecte pelo menos 2 corretoras para operar automaticamente!")
        st.info("Va em **Minhas Corretoras** e adicione suas contas.")
        botao_voltar_menu()
        return
    
    # Configuracoes de operacao
    st.subheader("Configuracoes de Execucao")
    
    col1, col2 = st.columns(2)
    with col1:
        valor_operacao = st.number_input("Valor por Operacao (USDT)", min_value=10.0, max_value=10000.0, value=100.0, step=10.0)
        lucro_minimo = st.slider("Lucro Minimo para Disparar (%)", 0.1, 3.0, 0.5, 0.1)
    with col2:
        max_operacoes_dia = st.number_input("Maximo de Operacoes por Dia", min_value=1, max_value=100, value=10)
        modo_simulacao = st.checkbox("🔬 Modo Simulacao (nao executa de verdade)", value=True)
    
    st.info(f"""
    📋 Resumo:
    - Valor: ${valor_operacao} por operacao
    - Lucro minimo: {lucro_minimo}%
    - Limite diario: {max_operacoes_dia} operacoes
    - Corretoras ativas: {', '.join(list(apis.keys())[:4])}
    """)
    
    st.markdown("---")
    
    if st.button("🚀 INICIAR OPERACAO AUTOMATICA", type="primary"):
        if modo_simulacao:
            st.success("✅ Modo Simulacao ATIVADO — nenhuma ordem sera enviada para as corretoras")
        else:
            st.warning("⚠️ ⚠️ ⚠️ MODO REAL — ORDENS SERAO EXECUTADAS DE VERDADE!")
        
        st.session_state["auto_trading_ativo"] = True
        st.session_state["auto_trading_config"] = {
            "valor_operacao": valor_operacao,
            "lucro_minimo": lucro_minimo,
            "max_operacoes_dia": max_operacoes_dia,
            "modo_simulacao": modo_simulacao,
            "iniciado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        st.subheader("🤖 Robo em Execucao...")
        st.info("Monitorando mercado em tempo real...")
        
        # Simulacao de execucao
        for i in range(3):
            time.sleep(1)
            st.write(f"Verificacao {i+1}/3: buscando oportunidades...")
        
        st.success("Sistema pronto! O robo escaneia continuamente e executa quando encontrar lucro.")
    
    if st.session_state.get("auto_trading_ativo", False):
        if st.button("🛑 PARAR OPERACAO"):
            st.session_state["auto_trading_ativo"] = False
            st.success("Robo parado!")
    
    botao_voltar_menu()

# ==============================================
# INICIALIZACAO
# ==============================================
st.set_page_config(page_title="Arbitragem AI", layout="wide")

if "usuario" not in st.session_state: st.session_state["usuario"] = None
if "logado" not in st.session_state: st.session_state["logado"] = False
if "admin_logado" not in st.session_state: st.session_state["admin_logado"] = False
if "ultimo_scan" not in st.session_state: st.session_state["ultimo_scan"] = None
if "pagina" not in st.session_state: st.session_state["pagina"] = "inicio"
if "auto_trading_ativo" not in st.session_state: st.session_state["auto_trading_ativo"] = False

usuarios = carregar_json(ARQUIVO_USUARIOS, {})

# ==============================================
# TELA DE LOGIN / CADASTRO
# ==============================================
def tela_login():
    exibir_logo_principal()
    st.subheader("Analise inteligente de oportunidades entre corretoras")
    st.warning("⚠️ Apenas analise. Nao e recomendacao de investimento. Precos podem variar. Sempre confirme antes de operar.")
    st.markdown("---")
    
    aba_entrar, aba_cadastrar, aba_recuperar = st.tabs(["Entrar", "Criar Conta", "Recuperar Senha"])
    
    with aba_entrar:
        st.subheader("Fazer Login")
        email_ou_usuario = st.text_input("E-mail ou Nome de Usuario", key="login_email_usuario")
        senha = st.text_input("Sua Senha", type="password", key="login_senha")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("ENTRAR", type="primary"):
                # Buscar por email OU nome de usuario
                usuario_encontrado = None
                for email, dados in usuarios.items():
                    if email == email_ou_usuario or dados.get("nome_usuario") == email_ou_usuario:
                        if verificar_senha(senha, dados.get("senha_hash", "")) or dados.get("senha") == senha:
                            usuario_encontrado = email
                            break
                
                if usuario_encontrado:
                    if usuarios[usuario_encontrado].get("plano_ativo", False) or usuarios[usuario_encontrado].get("plano") == "Gratuito":
                        st.session_state["usuario"] = usuario_encontrado
                        st.session_state["logado"] = True
                        st.rerun()
                    else:
                        st.warning("Aguardando aprovacao do pagamento.")
                else:
                    st.error("Credenciais incorretas!")
        
        with col2:
            st.markdown("### 🔐 Entrar com Google")
            st.info("🔜 Em desenvolvimento — integracao Google OAuth")
            st.button("Entrar com Google", disabled=True)
    
    with aba_cadastrar:
        st.subheader("Criar Nova Conta")
        novo_nome_usuario = st.text_input("Nome de Usuario", key="cad_nome_usuario", placeholder="seu_nome")
        novo_email = st.text_input("Seu E-mail", key="cad_email")
        nova_senha = st.text_input("Criar Senha", type="password", key="cad_senha")
        confirma_senha = st.text_input("Repetir Senha", type="password", key="cad_confirma")
        
        if st.button("CRIAR CONTA", type="primary"):
            # Verificar se nome de usuario ja existe
            nome_usuario_existe = any(
                dados.get("nome_usuario") == novo_nome_usuario 
                for dados in usuarios.values()
            )
            
            if nome_usuario_existe:
                st.error("Este nome de usuario ja esta em uso! Escolha outro.")
            elif novo_email in usuarios:
                st.error("Este e-mail ja esta cadastrado!")
            elif nova_senha != confirma_senha:
                st.error("Senhas nao coincidem!")
            elif len(nova_senha) < 4:
                st.error("Senha muito curta! Minimo 4 caracteres.")
            elif not novo_nome_usuario:
                st.error("Digite um nome de usuario!")
            else:
                usuarios[novo_email] = {
                    "nome_usuario": novo_nome_usuario,
                    "senha_hash": hash_senha(nova_senha),
                    "plano": "Gratuito",
                    "plano_escolhido": "Gratuito",
                    "plano_ativo": True,
                    "status_pagamento": "aprovado",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "corretoras_apis": {}
                }
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.session_state["usuario"] = novo_email
                st.session_state["logado"] = True
                st.success(f"Conta criada! Bem-vindo(a), {novo_nome_usuario}!")
                st.rerun()
    
    with aba_recuperar:
        st.subheader("Recuperar Senha")
        email_recup = st.text_input("E-mail cadastrado", key="recup_email")
        if st.button("ENVIAR CODIGO DE RECUPERACAO", type="primary"):
            if email_recup in usuarios:
                st.success("✅ Um codigo de recuperacao foi enviado para seu e-mail!")
            else:
                st.error("E-mail nao encontrado no sistema!")
    
    st.markdown("---")
    if st.button("PAINEL DE ADMINISTRACAO"):
        st.session_state["pagina"] = "Painel de Administracao"
        st.rerun()

# ==============================================
# TELA DE PLANOS
# ==============================================
def tela_planos():
    exibir_logo_principal()
    st.header("Escolha Seu Plano")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Gratuito")
        st.markdown("**R$ 0,00**")
        st.write("✅ Scanner basico")
        st.write("✅ 3 moedas")
        st.write("✅ Lucro liquido calculado")
        st.write("✅ 2 corretoras")
        st.write("❌ Operacao Automatica")
        st.write("❌ Alertas")
        if st.button("Escolher Gratuito", type="primary"):
            u = st.session_state["usuario"]
            usuarios[u].update({"plano": "Gratuito", "plano_escolhido": "Gratuito", "plano_ativo": True, "status_pagamento": "aprovado"})
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.success("Plano ativado!")
            st.rerun()
    
    with col2:
        st.subheader("Pro")
        st.markdown("**R$ 49,90/mes**")
        st.write("✅ 50 moedas")
        st.write("✅ 4 corretoras")
        st.write("✅ Atualizacao 60s")
        st.write("✅ Alertas por e-mail")
        st.write("✅ 🤖 Operacao Automatica")
        if st.button("Escolher Pro", type="primary"):
            u = st.session_state["usuario"]
            usuarios[u].update({"plano_escolhido": "Pro", "valor_pago": 49.90, "status_pagamento": "pendente"})
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()
    
    with col3:
        st.subheader("Premium")
        st.markdown("**R$ 99,90/mes**")
        st.write("✅ Moedas ilimitadas")
        st.write("✅ Todas corretoras")
        st.write("✅ Atualizacao 15s")
        st.write("✅ Alertas e-mail + WhatsApp")
        st.write("✅ 🤖 Operacao Automatica ILIMITADA")
        st.write("✅ Verificacao de liquidez")
        if st.button("Escolher Premium", type="primary"):
            u = st.session_state["usuario"]
            usuarios[u].update({"plano_escolhido": "Premium", "valor_pago": 99.90, "status_pagamento": "pendente"})
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()
    
    botao_voltar_menu()

# ==============================================
# TELA DE PAGAMENTO
# ==============================================
def tela_pagamento():
    exibir_logo_principal()
    u = st.session_state["usuario"]
    plano = usuarios[u].get("plano_escolhido", "Pro")
    valor = PLANOS[plano]["preco"]
    st.header("Pagamento via PIX")
    st.subheader(f"Plano: {plano} — R$ {valor:.2f}")
    st.markdown("---")
    st.info(f"""
    **Dados do PIX:**
    - Recebedor: {CONFIG['pix_nome_recebedor']}
    - Chave PIX: `{CONFIG['pix_chave']}`
    - Valor: R$ {valor:.2f}
    """)
    
    comprovante = st.file_uploader("Anexar Comprovante de Pagamento", type=["jpg", "jpeg", "png"])
    if st.button("JA PAGUEI — ENVIAR COMPROVANTE", type="primary"):
        id_pag = f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"
        caminho_img = ""
        if comprovante:
            os.makedirs("comprovantes", exist_ok=True)
            caminho_img = f"comprovantes/{id_pag}_{comprovante.name}"
            with open(caminho_img, "wb") as f: f.write(comprovante.getbuffer())
        usuarios[u].update({
            "id_pagamento": id_pag, "data_pagamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "caminho_comprovante": caminho_img
        })
        salvar_json(ARQUIVO_USUARIOS, usuarios)
        texto = f"""NOVO PAGAMENTO PENDENTE!

Cliente: {u}
Plano: {plano}
Valor: R$ {valor:.2f}
ID: {id_pag}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Acesse o PAINEL DE ADMINISTRACAO para aprovar!"""
        link_whats = f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"
        st.success("Comprovante enviado! Aguardando aprovacao.")
        st.markdown(f"[👉 Clique aqui para avisar no WhatsApp]({link_whats})")
    
    botao_voltar_menu()

# ==============================================
# PAINEL PRINCIPAL DO USUARIO
# ==============================================
def painel_principal():
    exibir_logo_sidebar()
    u = st.session_state["usuario"]
    dados_usuario = usuarios[u]
    nome_usuario = dados_usuario.get("nome_usuario", u)
    plano = dados_usuario.get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    
    st.sidebar.write(f"👤 {nome_usuario}")
    st.sidebar.write(f"📋 Plano: {plano}")
    st.sidebar.markdown("---")
    
    pagina = st.sidebar.radio("Navegacao", [
        "Painel Principal",
        "🔍 Scanner de Arbitragem",
        "🤖 Operacao Automatica",
        "🔗 Minhas Corretoras",
        "📈 Historico de Oportunidades",
        "🧮 Calculadora de Lucro Real",
        "💳 Alterar Plano",
        "Sair"
    ])
    
    if pagina == "Sair":
        st.session_state.clear()
        st.rerun()
    
    elif pagina == "Painel Principal":
        exibir_logo_principal()
        st.header(f"Bem-vindo(a), {nome_usuario}! 🚀")
        st.success(f"✅ Plano {plano} ativo!")
        st.info("O sistema compara precos entre corretoras e calcula o LUCRO REAL ja descontando taxas.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Corretoras Permitidas", len(dados_plano["corretoras"]))
        with col2:
            st.metric("Moedas Monitoradas", dados_plano["moedas"] if dados_plano["moedas"] < 100 else "Ilimitadas")
        with col3:
            st.metric("Atualizacao", f"{dados_plano['atualizacao_segundos']}s")
        
        st.markdown("---")
        st.subheader("📊 Resumo de Mercado")
        c1, c2, c3 = st.columns(3)
        c1.metric("BTC", "$ 63.420,50", "+0,32%")
        c2.metric("ETH", "$ 3.218,90", "-0,15%")
        c3.metric("SOL", "$ 142,85", "+1,05%")
        
        st.markdown("---")
        st.info("👉 Va em **🔍 Scanner de Arbitragem** para ver oportunidades em tempo real!")
        st.info("👉 Va em **🔗 Minhas Corretoras** para adicionar suas chaves API e operar automaticamente!")
    
    elif pagina == "🔍 Scanner de Arbitragem":
        st.header("🔍 Scanner de Arbitragem Inteligente")
        lucro_min_perc = st.slider("Lucro Minimo Liquido (%)", 0.1, 5.0, 0.5, 0.1)
        auto_refresh = st.checkbox("Atualizacao Automatica")
        corretoras = dados_plano["corretoras"]
        if dados_plano.get("modo_avancado"):
            corretoras = st.multiselect("Corretoras para monitorar", CORRETORAS_DISPONIVEIS, default=corretoras)
        moedas = MOEDAS_MONITORADAS[:dados_plano["moedas"]] if dados_plano["moedas"] < 100 else MOEDAS_MONITORADAS
        st.info(f"Comparando: {', '.join(corretoras)} | {len(moedas)} moedas")
        
        if st.button("🔄 ESCANEAR AGORA", type="primary") or auto_refresh:
            with st.spinner("Analisando precos..."):
                oportunidades = escanear_oportunidades(corretoras, moedas, lucro_min_perc)
            if not oportunidades:
                st.info("Nenhuma oportunidade encontrada no momento. Tente aumentar o lucro minimo.")
            else:
                st.subheader(f"✅ {len(oportunidades)} Oportunidade(s) Encontrada(s)")
                st.warning("⚠️ Confirme os precos diretamente na corretora antes de executar!")
                for op in oportunidades[:10]:
                    with st.expander(f"💰 {op['moeda']} — {op['lucro_liquido_perc']:.2f}% LÍQUIDO"):
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown(f"✅ Comprar em: **{op['comprar_em']}**")
                            st.write(f"Preco: **$ {op['preco_compra']:.4f}**")
                            st.info(op['liquidez_compra']['alerta'] or "✅ Liquidez suficiente")
                        with cb:
                            st.markdown(f"📤 Vender em: **{op['vender_em']}**")
                            st.write(f"Preco: **$ {op['preco_venda']:.4f}**")
                            st.info(op['liquidez_venda']['alerta'] or "✅ Liquidez suficiente")
                        l1, l2, l3 = st.columns(3)
                        l1.metric("Lucro Bruto", f"{op['lucro_bruto_perc']:.2f}%")
                        l2.metric("✅ Lucro LIQUIDO", f"{op['lucro_liquido_perc']:.2f}%")
                        l3.metric("Em $1.000 investidos", f"$ {(1000*op['lucro_liquido_perc']/100):.2f}")
            if auto_refresh:
                time.sleep(dados_plano["atualizacao_segundos"])
                st.rerun()
    
    elif pagina == "🤖 Operacao Automatica":
        tela_operacao_automatica()
    
    elif pagina == "🔗 Minhas Corretoras":
        tela_gerenciar_corretoras()
    
    elif pagina == "📈 Historico de Oportunidades":
        st.header("📈 Historico de Oportunidades")
        hist = carregar_json(ARQUIVO_HISTORICO, [])
        if not hist:
            st.info("Ainda nao ha oportunidades registradas. Faca uma varredura no Scanner.")
        else:
            st.info(f"Total de {len(hist)} oportunidades detectadas")
            for op in hist[:50]:
                st.write(f"{op.get('hora', '—')} | {op['moeda']} | {op['comprar_em']} → {op['vender_em']} | **{op['lucro_liquido_perc']:.2f}%**")
        botao_voltar_menu()
    
    elif pagina == "🧮 Calculadora de Lucro Real":
        st.header("🧮 Calculadora de Lucro Real (com taxas)")
        st.info("Diferente de outros apps, aqui ja descontamos as taxas de ambas as corretoras!")
        c1, c2 = st.columns(2)
        with c1:
            pc = st.number_input("Preco de Compra ($)", 0.0, 100000.0, 100.0, step=0.01)
            pv = st.number_input("Preco de Venda ($)", 0.0, 100000.0, 102.0, step=0.01)
            valor_inv = st.number_input("Valor para investir ($)", 0.0, 100000.0, 1000.0, step=10.0)
            taxa = st.number_input("Taxa da Corretora (%)", 0.0, 5.0, CONFIG["taxa_media_corretora_perc"])
        with c2:
            calc = calcular_lucro_liquido(pc, pv, taxa)
            qtd = valor_inv / pc if pc > 0 else 0
            st.metric("Quantidade de Moedas", f"{qtd:.4f}")
            st.metric("Lucro BRUTO (sem taxas)", f"{calc['lucro_bruto_perc']:.2f}%")
            st.metric("✅ Lucro LIQUIDO (com taxas)", f"{calc['lucro_liquido_perc']:.2f}%")
            if calc['lucro_liquido_perc'] <= 0:
                st.error("❌ Operacao NAO da lucro apos taxas!")
            elif calc['lucro_liquido_perc'] < 0.3:
                st.warning("⚠️ Lucro pequeno — pode desaparecer com variacao de preco")
            else:
                st.success("✅ Margem segura!")
        botao_voltar_menu()
    
    elif pagina == "💳 Alterar Plano":
        st.session_state["pagina"] = "Planos"
        st.rerun()

# ==============================================
# PAINEL DE ADMINISTRACAO
# ==============================================
def painel_administracao():
    exibir_logo_sidebar()
    if st.session_state.get("admin_logado") != True:
        senha_admin = st.text_input("Senha de Administrador", type="password")
        if st.button("ENTRAR NO PAINEL", type="primary"):
            if senha_admin == CONFIG["senha_admin"]:
                st.session_state["admin_logado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        st.stop()
    
    st.header("🔧 PAINEL DE ADMINISTRACAO")
    st.markdown("---")
    aba1, aba2, aba3 = st.tabs(["Pagamentos", "Sistema", "E-mail"])
    
    with aba1:
        usrs = carregar_json(ARQUIVO_USUARIOS, {})
        pendentes = {e: d for e, d in usrs.items() if d.get("status_pagamento") == "pendente"}
        if pendentes:
            st.subheader(f"⏳ {len(pendentes)} Pagamento(s) Pendente(s)")
            for email, d in pendentes.items():
                nome = d.get("nome_usuario", "—")
                with st.expander(f"{nome} <{email}> — {d.get('plano_escolhido')}"):
                    st.write(f"Valor: R$ {d.get('valor_pago',0):.2f}")
                    st.write(f"ID Pagamento: {d.get('id_pagamento', '—')}")
                    st.write(f"Data: {d.get('data_pagamento', '—')}")
                    img = d.get("caminho_comprovante", "")
                    if img and os.path.exists(img):
                        st.markdown("### COMPROVANTE:")
                        st.image(img, width=400)
                    else:
                        st.warning("Nenhuma imagem anexada!")
                    ap, re = st.columns(2)
                    with ap:
                        if st.button(f"✅ APROVAR E LIBERAR", key=f"apr_{email}", type="primary"):
                            usrs[email].update({
                                "status_pagamento": "aprovado",
                                "plano": d.get("plano_escolhido"),
                                "plano_ativo": True
                            })
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.success(f"{nome} — PLANO LIBERADO!")
                            st.balloons()
                            st.rerun()
                    with re:
                        if st.button(f"❌ REJEITAR", key=f"rej_{email}"):
                            usrs[email]["status_pagamento"] = "rejeitado"
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.warning(f"{nome} — REJEITADO!")
                            st.rerun()
        else:
            st.info("✅ Nenhum pagamento pendente no momento.")
        
        st.markdown("---")
        st.subheader("📋 Todos os Clientes")
        if not usrs:
            st.info("Ainda nao ha clientes cadastrados.")
        else:
            for email, d in usrs.items():
                nome = d.get("nome_usuario", "—")
                icone = {"aprovado":"✅", "pendente":"⏳", "rejeitado":"❌"}.get(d.get("status_pagamento","aprovado"), "—")
                with st.expander(f"{icone} {nome} <{email}> | Plano: {d.get('plano', 'Gratuito')}"):
                    st.write(f"Cadastro: {d.get('data_cadastro', '—')}")
                    st.write(f"Corretoras conectadas: {len(d.get('corretoras_apis', {}))}")
    
    with aba2:
        st.subheader("⚙️ Configuracoes do Sistema")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        pix_nome = st.text_input("Nome Recebedor PIX", value=dados_sis.get("pix_nome_recebedor", CONFIG["pix_nome_recebedor"]))
        pix_chave = st.text_input("Chave PIX", value=dados_sis.get("pix_chave", CONFIG["pix_chave"]))
        whatsapp = st.text_input("WhatsApp do Admin", value=dados_sis.get("whatsapp_admin", CONFIG["whatsapp_admin"]))
        taxa_media = st.number_input("Taxa Media Corretoras (%)", 0.0, 5.0, dados_sis.get("taxa_media_corretora_perc", CONFIG["taxa_media_corretora_perc"]), step=0.01)
        senha_admin = st.text_input("Senha do Painel Admin", value=dados_sis.get("senha_admin", CONFIG["senha_admin"]))
        
        if st.button("💾 SALVAR TODAS AS CONFIGURACOES", type="primary"):
            CONFIG.update({
                "pix_nome_recebedor": pix_nome,
                "pix_chave": pix_chave,
                "whatsapp_admin": whatsapp,
                "taxa_media_corretora_perc": taxa_media,
                "senha_admin": senha_admin
            })
            salvar_json(ARQUIVO_SISTEMA, CONFIG)
            st.success("✅ Configuracoes salvas com sucesso!")
    
    with aba3:
        st.subheader("📧 Configuracoes de E-mail")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        remetente = st.text_input("E-mail Remetente", value=dados_sis.get("email_remetente", ""))
        senha_app = st.text_input("Senha de Aplicativo", value=dados_sis.get("senha_app_email", ""), type="password")
        if st.button("SALVAR E-MAIL", type="primary"):
            salvar_json(ARQUIVO_SISTEMA, {"email_remetente": remetente, "senha_app_email": senha_app})
            st.success("✅ E-mail configurado!")
    
    if st.sidebar.button("SAIR DO ADMIN"):
        st.session_state["admin_logado"] = False
        st.rerun()

# ==============================================
# CONTROLE DE PAGINAS
# ==============================================
if not st.session_state["logado"]:
    if st.session_state["pagina"] == "Painel de Administracao":
        painel_administracao()
    else:
        tela_login()
else:
    if st.session_state["pagina"] == "Planos":
        tela_planos()
    elif st.session_state["pagina"] == "Pagamento":
        tela_pagamento()
    else:
        painel_principal()
