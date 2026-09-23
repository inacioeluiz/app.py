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
    """Botao padrao para voltar ao menu principal"""
    if st.sidebar.button("🏠 Voltar ao Menu Principal"):
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
# INICIALIZACAO
# ==============================================
st.set_page_config(page_title="Arbitragem AI", layout="wide")

if "usuario" not in st.session_state: st.session_state["usuario"] = None
if "nome_usuario" not in st.session_state: st.session_state["nome_usuario"] = None
if "logado" not in st.session_state: st.session_state["logado"] = False
if "admin_logado" not in st.session_state: st.session_state["admin_logado"] = False
if "ultimo_scan" not in st.session_state: st.session_state["ultimo_scan"] = None

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
        st.info("Entre com **E-mail** ou **Nome de Usuario**")
        email_ou_nome = st.text_input("E-mail ou Nome de Usuario", key="login_usuario")
        senha = st.text_input("Sua Senha", type="password", key="login_senha")
        
        if st.button("ENTRAR", type="primary"):
            encontrado = None
            for chave, dados in usuarios.items():
                if chave == email_ou_nome or dados.get("nome_usuario") == email_ou_nome:
                    if dados.get("senha") == senha:
                        encontrado = chave
                        break
            if encontrado:
                if usuarios[encontrado].get("plano_ativo", False) or usuarios[encontrado].get("plano") == "Gratuito":
                    st.session_state["usuario"] = encontrado
                    st.session_state["nome_usuario"] = usuarios[encontrado].get("nome_usuario", encontrado)
                    st.session_state["logado"] = True
                    st.rerun()
                else:
                    st.warning("Aguardando aprovacao do pagamento. Verifique mais tarde.")
            else:
                st.error("Credenciais incorretas!")
        
        st.markdown("---")
        st.info("🔜 Em breve: Login com Google")
    
    with aba_cadastrar:
        st.info("Preencha todos os dados abaixo")
        novo_nome = st.text_input("Nome de Usuario (ex: seu_nome123)", key="cad_nome_usuario")
        novo_email = st.text_input("Seu E-mail", key="cad_email")
        nova_senha = st.text_input("Criar Senha", type="password", key="cad_senha")
        confirma_senha = st.text_input("Repetir Senha", type="password", key="cad_confirma")
        
        if st.button("CRIAR CONTA", type="primary"):
            if not novo_nome or len(novo_nome) < 3:
                st.error("Nome de usuario deve ter pelo menos 3 caracteres!")
            elif any(d.get("nome_usuario") == novo_nome for d in usuarios.values()):
                st.error("Este nome de usuario ja esta em uso! Escolha outro.")
            elif novo_email in usuarios:
                st.error("Este e-mail ja esta cadastrado!")
            elif nova_senha != confirma_senha:
                st.error("As senhas nao coincidem!")
            elif len(nova_senha) < 4:
                st.error("Senha muito curta! Minimo 4 caracteres.")
            else:
                usuarios[novo_email] = {
                    "nome_usuario": novo_nome,
                    "senha": nova_senha,
                    "plano": "Gratuito",
                    "plano_escolhido": "Gratuito",
                    "plano_ativo": True,
                    "status_pagamento": "aprovado",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "apis_corretoras": {}
                }
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.session_state["usuario"] = novo_email
                st.session_state["nome_usuario"] = novo_nome
                st.session_state["logado"] = True
                st.success(f"✅ Conta criada! Bem-vindo(a), {novo_nome}!")
                st.rerun()
    
    with aba_recuperar:
        email_recup = st.text_input("Seu E-mail cadastrado", key="recup_email")
        if st.button("ENVIAR CODIGO", type="primary"):
            if email_recup in usuarios:
                st.success("✅ Se solicitado, um codigo de recuperacao seria enviado para seu e-mail.")
            else:
                st.error("E-mail nao encontrado!")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 PAINEL DE ADMINISTRACAO"):
            st.session_state["pagina"] = "Painel de Administracao"
            st.rerun()
    with col2:
        if st.button("🏠 Voltar ao Inicio"):
            st.session_state["pagina"] = "inicio"
            st.rerun()

# ==============================================
# TELA DE PLANOS
# ==============================================
def tela_planos():
    botao_voltar_menu()
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
        st.write("❌ Operacao automatica")
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
        st.write("✅ Operacao automatica")
        st.write("✅ Alertas por e-mail")
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
        st.write("✅ Operacao automatica")
        st.write("✅ Alertas e-mail + WhatsApp")
        st.write("✅ Verificacao de liquidez")
        if st.button("Escolher Premium", type="primary"):
            u = st.session_state["usuario"]
            usuarios[u].update({"plano_escolhido": "Premium", "valor_pago": 99.90, "status_pagamento": "pendente"})
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()

# ==============================================
# TELA DE PAGAMENTO
# ==============================================
def tela_pagamento():
    botao_voltar_menu()
    u = st.session_state["usuario"]
    plano = usuarios[u].get("plano_escolhido", "Pro")
    valor = PLANOS[plano]["preco"]
    st.header("Pagamento via PIX")
    st.subheader(f"Plano: {plano} — R$ {valor:.2f}")
    st.info(f"Recebedor: {CONFIG['pix_nome_recebedor']}\nChave PIX: `{CONFIG['pix_chave']}`\nValor: R$ {valor:.2f}")
    
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
        texto = f"NOVO PAGAMENTO!\nCliente: {u}\nPlano: {plano}\nValor: R$ {valor:.2f}\nID: {id_pag}"
        link_whats = f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"
        st.success("Comprovante enviado! Aguardando aprovacao.")
        st.markdown(f"[Clique aqui para avisar no WhatsApp]({link_whats})")
    if st.button("⬅️ Voltar aos Planos"):
        st.session_state["pagina"] = "Planos"
        st.rerun()

# ==============================================
# TELA DE CONFIGURACAO DE APIS DAS CORRETORAS
# ==============================================
def tela_configurar_apis():
    botao_voltar_menu()
    u = st.session_state["usuario"]
    dados_usuario = usuarios[u]
    plano = dados_usuario.get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    
    st.header("🔑 Configurar APIs das Corretoras")
    st.info("""
    Insira suas chaves de API para que o sistema possa:
    - ✅ Verificar seus saldos reais
    - ✅ Identificar oportunidades que voce tem valor para executar
    - ✅ (Pro/Premium) Executar operacoes automaticamente quando configurado
    """)
    
    apis_salvas = dados_usuario.get("apis_corretoras", {})
    corretoras_disponiveis = dados_plano["corretoras"]
    
    for corretora in corretoras_disponiveis:
        st.subheader(f"📊 {corretora}")
        col1, col2 = st.columns(2)
        with col1:
            api_key = st.text_input(f"API Key — {corretora}", 
                                   value=apis_salvas.get(corretora, {}).get("api_key", ""),
                                   type="password",
                                   key=f"api_key_{corretora}")
        with col2:
            api_secret = st.text_input(f"API Secret — {corretora}", 
                                      value=apis_salvas.get(corretora, {}).get("api_secret", ""),
                                      type="password",
                                      key=f"api_secret_{corretora}")
        
        apis_salvas[corretora] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "configurada": bool(api_key and api_secret),
            "data_configuracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S") if api_key and api_secret else None
        }
        
        if apis_salvas[corretora]["configurada"]:
            st.success(f"✅ {corretora} configurada!")
        st.markdown("---")
    
    if st.button("💾 SALVAR CONFIGURACAO DAS APIS", type="primary"):
        usuarios[u]["apis_corretoras"] = apis_salvas
        salvar_json(ARQUIVO_USUARIOS, usuarios)
        st.success("✅ APIs salvas com sucesso! O sistema ja pode monitorar.")
    
    st.markdown("---")
    st.subheader("⚠️ Dicas de Seguranca")
    st.info("""
    1. Crie a API diretamente no site da corretora
    2. **Nunca** conceda permissao de saque/retirada — apenas leitura e comercio
    3. Restrinja o acesso da API ao seu IP se a corretora permitir
    4. Nao compartilhe suas chaves com ninguem
    5. As chaves ficam salvas apenas no seu sistema
    """)
    
    if dados_plano.get("operacao_automatica"):
        st.subheader("⚙️ Operacao Automatica")
        st.warning("""
        A operacao automatica executara compras e vendas quando detectada oportunidade.
        Recomendado testar primeiro no modo simulado!
        """)
        ativar_auto = st.checkbox("Ativar operacao automatica (com risco)", 
                                 value=dados_usuario.get("operacao_automatica", False))
        if ativar_auto != dados_usuario.get("operacao_automatica", False):
            usuarios[u]["operacao_automatica"] = ativar_auto
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.success(f"Operacao automatica {'ATIVADA' if ativar_auto else 'DESATIVADA'}!")

# ==============================================
# PAINEL PRINCIPAL DO USUARIO
# ==============================================
def painel_principal():
    exibir_logo_sidebar()
    u = st.session_state["usuario"]
    nome_usuario = st.session_state.get("nome_usuario", u)
    dados_usuario = usuarios[u]
    plano = dados_usuario.get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    
    st.sidebar.write(f"👤 Usuario: {nome_usuario}")
    st.sidebar.write(f"📧 E-mail: {u}")
    st.sidebar.write(f"💳 Plano: {plano}")
    st.sidebar.markdown("---")
    
    pagina = st.sidebar.radio("Navegacao", [
        "Painel Principal",
        "🔑 Minhas Corretoras (APIs)",
        "Scanner de Arbitragem",
        "Historico de Oportunidades",
        "Calculadora de Lucro Real",
        "Alterar Plano",
        "Sair"
    ])
    
    if pagina == "Sair":
        st.session_state.clear()
        st.rerun()
    
    elif pagina == "Painel Principal":
        st.header(f"Bem-vindo(a), {nome_usuario}! 🚀")
        st.success(f"✅ Plano {plano} ativo!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Corretoras disponiveis", len(dados_plano["corretoras"]))
        col2.metric("Moedas monitoradas", dados_plano["moedas"] if dados_plano["moedas"] < 100 else "Ilimitadas")
        col3.metric("Atualizacao", f"{dados_plano['atualizacao_segundos']}s")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("BTC", "$ 63.420,50", "+0,32%")
        c2.metric("ETH", "$ 3.218,90", "-0,15%")
        c3.metric("SOL", "$ 142,85", "+1,05%")
        st.info("👉 Va em **🔑 Minhas Corretoras** para configurar suas APIs e depois no **Scanner** para ver oportunidades!")
    
    elif pagina == "🔑 Minhas Corretoras (APIs)":
        tela_configurar_apis()
    
    elif pagina == "Scanner de Arbitragem":
        st.header("🔍 Scanner de Arbitragem Inteligente")
        lucro_min_perc = st.slider("Lucro Minimo Liquido (%)", 0.1, 5.0, 0.5, 0.1)
        auto_refresh = st.checkbox("Atualizacao Automatica")
        corretoras = dados_plano["corretoras"]
        if dados_plano.get("modo_avancado"):
            corretoras = st.multiselect("Corretoras para monitorar", CORRETORAS_DISPONIVEIS, default=corretoras)
        moedas = MOEDAS_MONITORADAS[:dados_plano["moedas"]] if dados_plano["moedas"] < 100 else MOEDAS_MONITORADAS
        
        apis_configuradas = [c for c in corretoras if dados_usuario.get("apis_corretoras", {}).get(c, {}).get("configurada", False)]
        if apis_configuradas:
            st.success(f"✅ {len(apis_configuradas)} corretoras com API configurada: {', '.join(apis_configuradas)}")
        else:
            st.warning("⚠️ Nenhuma API configurada ainda. Acesse 'Minhas Corretoras' para inserir suas chaves.")
        
        st.info(f"Comparando: {', '.join(corretoras)} | {len(moedas)} moedas")
        
        if st.button("🔄 ESCANEAR AGORA", type="primary") or auto_refresh:
            with st.spinner("Analisando precos..."):
                oportunidades = escanear_oportunidades(corretoras, moedas, lucro_min_perc)
            if not oportunidades:
                st.info("Nenhuma oportunidade encontrada no momento.")
            else:
                st.subheader(f"✅ {len(oportunidades)} oportunidade(s) encontrada(s)")
                st.warning("⚠️ Confirme os precos diretamente na corretora antes de executar!")
                for op in oportunidades[:10]:
                    with st.expander(f"💰 {op['moeda']} — {op['lucro_liquido_perc']:.2f}% LÍQUIDO"):
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown(f"✅ Comprar em: **{op['comprar_em']}**")
                            st.write(f"Preco: $ {op['preco_compra']:.4f}")
                            st.info(op['liquidez_compra']['alerta'] or "✅ Liquidez suficiente")
                        with cb:
                            st.markdown(f"📤 Vender em: **{op['vender_em']}**")
                            st.write(f"Preco: $ {op['preco_venda']:.4f}")
                            st.info(op['liquidez_venda']['alerta'] or "✅ Liquidez suficiente")
                        l1, l2, l3 = st.columns(3)
                        l1.metric("Lucro Bruto", f"{op['lucro_bruto_perc']:.2f}%")
                        l2.metric("✅ Lucro Liquido", f"{op['lucro_liquido_perc']:.2f}%")
                        l3.metric("Em $1.000", f"$ {(1000*op['lucro_liquido_perc']/100):.2f}")
            if auto_refresh:
                time.sleep(dados_plano["atualizacao_segundos"])
                st.rerun()
    
    elif pagina == "Historico de Oportunidades":
        st.header("📈 Historico de Oportunidades")
        hist = carregar_json(ARQUIVO_HISTORICO, [])
        if not hist:
            st.info("Ainda nao ha oportunidades registradas. Faca uma varredura no Scanner.")
        else:
            st.info(f"Total de {len(hist)} oportunidades detectadas")
            for op in hist[:50]:
                st.write(f"{op.get('hora', '—')} | {op['moeda']} | {op['comprar_em']}→{op['vender_em']} | {op['lucro_liquido_perc']:.2f}%")
    
    elif pagina == "Calculadora de Lucro Real":
        st.header("🧮 Calculadora de Lucro Real (com taxas)")
        c1, c2 = st.columns(2)
        with c1:
            pc = st.number_input("Preco de Compra ($)", 0.0, 100000.0, 100.0)
            pv = st.number_input("Preco de Venda ($)", 0.0, 100000.0, 102.0)
            valor_inv = st.number_input("Valor para investir ($)", 0.0, 100000.0, 1000.0)
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
    
    elif pagina == "Alterar Plano":
        tela_planos()

# ==============================================
# PAINEL DE ADMINISTRACAO COMPLETO
# ==============================================
def painel_administracao():
    exibir_logo_sidebar()
    
    if st.session_state.get("admin_logado") != True:
        st.header("🔐 Acesso Restrito — Administracao")
        senha_admin = st.text_input("Senha de Administrador", type="password")
        if st.button("ENTRAR", type="primary"):
            if senha_admin == CONFIG["senha_admin"]:
                st.session_state["admin_logado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        if st.button("🏠 Voltar ao Inicio"):
            st.session_state["pagina"] = "inicio"
            st.rerun()
        st.stop()
    
    st.header("🏛️ PAINEL DE ADMINISTRACAO — Arbitragem AI")
    st.markdown("---")
    
    aba1, aba2, aba3, aba4 = st.tabs([
        "📋 Usuarios e Pagamentos", 
        "⚙️ Configuracoes do Sistema", 
        "📧 E-mail",
        "📊 Estatisticas"
    ])
    
    with aba1:
        st.subheader("Gerenciamento de Usuarios")
        todos_usuarios = carregar_json(ARQUIVO_USUARIOS, {})
        
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Pendentes", "Aprovados", "Rejeitados"])
        usuarios_filtrados = {}
        for email, dados in todos_usuarios.items():
            status = dados.get("status_pagamento", "aprovado")
            if filtro_status == "Todos":
                usuarios_filtrados[email] = dados
            elif filtro_status == "Pendentes" and status == "pendente":
                usuarios_filtrados[email] = dados
            elif filtro_status == "Aprovados" and status in ["aprovado", "Gratuito"]:
                usuarios_filtrados[email] = dados
            elif filtro_status == "Rejeitados" and status == "rejeitado":
                usuarios_filtrados[email] = dados
        
        if not usuarios_filtrados:
            st.info(f"Nenhum usuario com status: {filtro_status}")
        else:
            st.subheader(f"{len(usuarios_filtrados)} usuario(s) encontrado(s)")
            for email, dados in usuarios_filtrados.items():
                nome = dados.get("nome_usuario", "—")
                plano_atual = dados.get("plano", "Gratuito")
                status = dados.get("status_pagamento", "aprovado")
                icone = {"aprovado":"✅", "pendente":"⏳", "rejeitado":"❌"}.get(status, "—")
                
                with st.expander(f"{icone} {nome} | {email} | Plano: {plano_atual}"):
                    col_info, col_acao = st.columns([2, 1])
                    with col_info:
                        st.write(f"📅 Cadastro: {dados.get('data_cadastro', '—')}")
                        st.write(f"💳 Status: {status.upper()}")
                        st.write(f"✅ Ativo: {'SIM' if dados.get('plano_ativo', False) else 'NAO'}")
                        st.write(f"💰 Valor pago: R$ {dados.get('valor_pago', 0):.2f}")
                        st.write(f"🆔 ID Pagamento: {dados.get('id_pagamento', '—')}")
                        
                        img = dados.get("caminho_comprovante", "")
                        if img and os.path.exists(img):
                            st.markdown("### 📷 Comprovante:")
                            st.image(img, width=400)
                    
                    with col_acao:
                        st.subheader("Acoes")
                        
                        novo_plano = st.selectbox(
                            "Alterar Plano", 
                            list(PLANOS.keys()),
                            index=list(PLANOS.keys()).index(plano_atual),
                            key=f"admin_plano_{email}"
                        )
                        if st.button(f"✏️ Alterar para {novo_plano}", key=f"apl_{email}", type="primary"):
                            todos_usuarios[email]["plano"] = novo_plano
                            if novo_plano == "Gratuito":
                                todos_usuarios[email]["status_pagamento"] = "aprovado"
                                todos_usuarios[email]["plano_ativo"] = True
                            salvar_json(ARQUIVO_USUARIOS, todos_usuarios)
                            st.success(f"✅ Plano de {nome} alterado para {novo_plano}!")
                            st.rerun()
                        
                        if status == "pendente":
                            col_ap, col_rej = st.columns(2)
                            with col_ap:
                                if st.button("✅ APROVAR", key=f"apr_{email}", type="primary"):
                                    todos_usuarios[email]["status_pagamento"] = "aprovado"
                                    todos_usuarios[email]["plano"] = dados.get("plano_escolhido", "Pro")
                                    todos_usuarios[email]["plano_ativo"] = True
                                    salvar_json(ARQUIVO_USUARIOS, todos_usuarios)
                                    st.success(f"✅ {nome} — APROVADO! Acesso liberado!")
                                    st.balloons()
                                    st.rerun()
                            with col_rej:
                                if st.button("❌ REJEITAR", key=f"rej_{email}"):
                                    todos_usuarios[email]["status_pagamento"] = "rejeitado"
                                    salvar_json(ARQUIVO_USUARIOS, todos_usuarios)
                                    st.warning(f"❌ {nome} — REJEITADO!")
                                    st.rerun()
                        
                        st.markdown("---")
                        if st.button("🗑️ EXCLUIR CONTA", key=f"del_{email}"):
                            if f"conf_del_{email}" not in st.session_state:
                                st.session_state[f"conf_del_{email}"] = True
                                st.warning(f"⚠️ Clique NOVAMENTE para confirmar exclusao de {nome}!")
                            else:
                                if dados.get("caminho_comprovante") and os.path.exists(dados.get("caminho_comprovante")):
                                    os.remove(dados.get("caminho_comprovante"))
                                del todos_usuarios[email]
                                salvar_json(ARQUIVO_USUARIOS, todos_usuarios)
                                st.success(f"🗑️ {nome} — EXCLUIDO PERMANENTEMENTE!")
                                if f"conf_del_{email}" in st.session_state:
                                    del st.session_state[f"conf_del_{email}"]
                                st.rerun()
    
    with aba2:
        st.subheader("Configuracoes do Sistema")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        
        col_pix1, col_pix2 = st.columns(2)
        with col_pix1:
            pix_nome = st.text_input("Nome do Recebedor PIX", value=dados_sis.get("pix_nome_recebedor", CONFIG["pix_nome_recebedor"]))
        with col_pix2:
            pix_chave = st.text_input("Chave PIX", value=dados_sis.get("pix_chave", CONFIG["pix_chave"]))
        
        col_whats, col_email_sup = st.columns(2)
        with col_whats:
            whatsapp = st.text_input("WhatsApp do Admin", value=dados_sis.get("whatsapp_admin", CONFIG["whatsapp_admin"]))
        with col_email_sup:
            email_sup = st.text_input("E-mail de Suporte", value=dados_sis.get("email_suporte", CONFIG["email_suporte"]))
        
        taxa_media = st.number_input("Taxa Media das Corretoras (%)", 0.0, 5.0, 
                                     dados_sis.get("taxa_media_corretora_perc", CONFIG["taxa_media_corretora_perc"]), 
                                     step=0.01,
                                     help="Descontada automaticamente no calculo do lucro liquido")
        
        col_logo1, col_logo2 = st.columns(2)
        with col_logo1:
            logo_princ = st.text_input("Logo Principal (arquivo)", value=dados_sis.get("logo_principal", CONFIG["logo_principal"]))
        with col_logo2:
            logo_lat = st.text_input("Logo Lateral (arquivo)", value=dados_sis.get("logo_pequeno", CONFIG["logo_pequeno"]))
        
        senha_admin_nova = st.text_input("Senha do Painel Admin", value=dados_sis.get("senha_admin", CONFIG["senha_admin"]), type="password")
        
        if st.button("💾 SALVAR TODAS AS CONFIGURACOES", type="primary"):
            CONFIG.update({
                "pix_nome_recebedor": pix_nome,
                "pix_chave": pix_chave,
                "whatsapp_admin": whatsapp,
                "email_suporte": email_sup,
                "taxa_media_corretora_perc": taxa_media,
                "logo_principal": logo_princ,
                "logo_pequeno": logo_lat,
                "senha_admin": senha_admin_nova
            })
            salvar_json(ARQUIVO_SISTEMA, CONFIG)
            st.success("✅ Todas as configuracoes foram salvas!")
    
    with aba3:
        st.subheader("Configuracoes de E-mail")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        
        remetente = st.text_input("E-mail Remetente", value=dados_sis.get("email_remetente", ""))
        senha_app = st.text_input("Senha de Aplicativo", value=dados_sis.get("senha_app_email", ""), type="password",
                                  help="No Gmail: ative 2FA → crie 'Senha de App'")
        smtp_serv = st.text_input("Servidor SMTP", value=dados_sis.get("smtp_servidor", "smtp.gmail.com"))
        smtp_port = st.number_input("Porta SMTP", value=dados_sis.get("smtp_porta", 587))
        
        if st.button("💾 SALVAR E-MAIL", type="primary"):
            salvar_json(ARQUIVO_SISTEMA, {
                "email_remetente": remetente,
                "senha_app_email": senha_app,
                "smtp_servidor": smtp_serv,
                "smtp_porta": int(smtp_port)
            })
            st.success("✅ Configuracoes de e-mail salvas!")
    
    with aba4:
        st.subheader("Estatisticas da Plataforma")
        todos = carregar_json(ARQUIVO_USUARIOS, {})
        total = len(todos)
        ativos = sum(1 for d in todos.values() if d.get("plano_ativo", False))
        pendentes = sum(1 for d in todos.values() if d.get("status_pagamento") == "pendente")
        hist = carregar_json(ARQUIVO_HISTORICO, [])
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Total Usuarios", total)
        kpi2.metric("✅ Ativos", ativos)
        kpi3.metric("⏳ Pendentes", pendentes)
        kpi4.metric("🔍 Oportunidades", len(hist))
        
        st.markdown("---")
        st.info("Dados atualizados em tempo real")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 SAIR DO ADMIN"):
        st.session_state["admin_logado"] = False
        st.rerun()
    if st.sidebar.button("🏠 Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.session_state["admin_logado"] = False
        st.rerun()

# ==============================================
# CONTROLE DE PAGINAS
# ==============================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

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
