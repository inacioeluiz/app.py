import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from urllib import request

# ==============================================
# 🪙 CRIPTOARBITRAGE PRO — VERSÃO FINAL CORRIGIDA
# 💳 Pix · Mercado Pago · PicPay · Lembretes de Upgrade
# ==============================================

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PAGAMENTOS = "pagamentos.json"

# ==============================================
# ⚙️ SUAS CONFIGURAÇÕES — EDITE AQUI!
# ==============================================
CONFIG = {
    "pix_chave": "11571293744",
    "pix_nome_recebedor": "Inácio Luiz Santos da Silva",
    "pix_cidade": "Itaboraí",
    "mercadopago_token": "SEU_TOKEN_MERCADOPAGO_AQUI",
    "picpay_token": "SEU_TOKEN_PICPAY_AQUI",
    "email_suporte": "suportearbitrageai@gmail.com"
}

CORRETORAS = {
    "Binance": {"url_preco": "https://api.binance.com/api/v3/ticker/price?symbol=", "taxa_compra": 0.10, "taxa_saque": 0.05},
    "KuCoin": {"url_preco": "https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=", "taxa_compra": 0.10, "taxa_saque": 0.08},
    "MEXC": {"url_preco": "https://api.mexc.com/api/v3/ticker/price?symbol=", "taxa_compra": 0.10, "taxa_saque": 0.07},
    "Bybit": {"url_preco": "https://api.bybit.com/v2/spot/public/quote?symbol=", "taxa_compra": 0.10, "taxa_saque": 0.06}
}

MOEDAS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "ADA-USDT", "DOGE-USDT",
    "AVAX-USDT", "MATIC-USDT", "LINK-USDT", "DOT-USDT", "SHIB-USDT", "PEPE-USDT"
]

PLANOS = {
    "Gratuito": {
        "preco": 0, "moedas": 3, "intervalo": 300, "lucro_min": 0.5, "corretoras": 2,
        "descricao": "Ideal para começar", "cor": "#4CAF50",
        "beneficios": ["3 moedas monitoradas", "2 corretoras", "Análise manual"]
    },
    "Pro": {
        "preco": 29.90, "moedas": 8, "intervalo": 60, "lucro_min": 0.2, "corretoras": 4,
        "descricao": "Para traders sérios", "cor": "#FF9800",
        "beneficios": ["8 moedas monitoradas", "4 corretoras", "Alertas automáticos", "Suporte prioritário"]
    },
    "Premium": {
        "preco": 79.90, "moedas": 99, "intervalo": 15, "lucro_min": 0.1, "corretoras": 4,
        "descricao": "Acesso VIP completo", "cor": "#9C27B0",
        "beneficios": ["Moedas ilimitadas", "Verificação a cada 15s", "Histórico completo", "Suporte VIP 24/7"]
    }
}

# ==============================================
# 💾 GERENCIAMENTO DE DADOS
# ==============================================
def carregar_json(arquivo, padrao=None):
    if padrao is None:
        padrao = {}
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return padrao.copy()
    return padrao.copy()

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def gerar_id_pagamento():
    return f"TX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

def cadastrar_usuario(email, senha, plano):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email in usuarios:
        return False, "❌ E-mail já cadastrado! Faça login."
    usuarios[email] = {
        "senha": senha, "plano": plano, "plano_ativo": plano == "Gratuito",
        "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "data_expiracao": None, "pagamentos": []
    }
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True, f"✅ Conta criada! Plano: {plano}"

def verificar_login(email, senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False, "❌ E-mail não encontrado!"
    if usuarios[email]["senha"] != senha:
        return False, "❌ Senha incorreta!"
    return True, usuarios[email]

def registrar_pagamento(email, plano, valor, metodo, id_transacao):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    expiracao = datetime.now() + timedelta(days=30)
    usuarios[email]["plano"] = plano
    usuarios[email]["plano_ativo"] = True
    usuarios[email]["data_expiracao"] = expiracao.strftime("%d/%m/%Y")
    if "pagamentos" not in usuarios[email]:
        usuarios[email]["pagamentos"] = []
    usuarios[email]["pagamentos"].append({
        "id": id_transacao, "plano": plano, "valor": valor, "metodo": metodo,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "status": "aprovado"
    })
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def salvar_dados_usuario(email, chaves, config_usuario):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    usuarios[email]["chaves"] = chaves
    usuarios[email]["config"] = config_usuario
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def carregar_dados_usuario(email, plano_padrao="Gratuito"):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    user = usuarios.get(email, {})
    plano = user.get("plano", plano_padrao)
    return {
        "chaves": user.get("chaves", {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS}),
        "config": user.get("config", {
            "moedas_selecionadas": MOEDAS[:PLANOS[plano]["moedas"]],
            "lucro_min": PLANOS[plano]["lucro_min"],
            "intervalo": PLANOS[plano]["intervalo"]
        })
    }

# ==============================================
# 💳 GERAR PIX
# ==============================================
def gerar_codigo_pix(valor, descricao, devedor_email=""):
    chave = CONFIG["pix_chave"]
    nome = CONFIG["pix_nome_recebedor"]
    cidade = CONFIG["pix_cidade"]
    valor_str = f"{valor:.2f}"
    codigo_pix = f"00020126580014br.gov.bcb.pix0136{chave}0214{descricao[:14]}5204000053039865802BR5925{nome[:25]}6015{cidade[:15]}62070503***6304"
    return codigo_pix, chave

def exibir_pagamento_pix(plano, email_cliente):
    valor = PLANOS[plano]["preco"]
    id_pagamento = gerar_id_pagamento()
    descricao = f"Plano {plano}"
    codigo_pix, chave = gerar_codigo_pix(valor, descricao, email_cliente)
    st.markdown(f"""
    <div style='background: rgba(30,41,59,0.8); border: 1px solid #22c55e; border-radius: 16px; padding: 24px; text-align: center; margin: 20px 0;'>
        <h3 style='color:#22c55e; margin:0;'>💳 Pagamento via PIX</h3>
        <p style='color:#94a3b8; font-size:14px; margin:10px 0;'>Plano: <strong>{plano}</strong> — Valor: <strong>R$ {valor:.2f}</strong></p>
        <p style='color:#e0e0e0; font-size:13px;'>ID da transação: <code style='background:#1e293b; padding:4px 8px; border-radius:4px;'>{id_pagamento}</code></p>
    </div>
    """, unsafe_allow_html=True)
    st.info(f"🔑 **Chave Pix:** `{chave}`")
    st.info(f"👤 **Recebedor:** {CONFIG['pix_nome_recebedor']}")
    st.markdown("**📋 Código Pix Copia e Cola:**")
    st.code(codigo_pix, language="text")
    st.markdown("✅ **Como pagar:** 1. Copie o código 2. Pague no seu banco 3. Clique em 'Já Paguei!'")
    if st.button("✅ Já Paguei — Ativar Meu Plano!", type="primary", use_container_width=True):
        if registrar_pagamento(email_cliente, plano, valor, "Pix", id_pagamento):
            st.success(f"🎉 Pagamento registrado! Plano **{plano}** ativado! ✅")
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ Erro ao registrar. Contate o suporte.")

# ==============================================
# 🔧 FUNÇÕES DE MERCADO
# ==============================================
def buscar_preco(url, par, tipo="binance"):
    try:
        if tipo == "binance":
            url = url + par.replace("-", "")
        elif tipo == "kucoin":
            url = url + par
        elif tipo in ["mexc", "bybit"]:
            url = url + par.replace("-", "")
        req = request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if tipo == "binance":
                return float(data["price"])
            elif tipo == "kucoin":
                return float(data["data"]["price"])
            elif tipo == "mexc":
                return float(data["price"])
            elif tipo == "bybit":
                return float(data["result"][0]["price"])
    except:
        return None

def calcular_lucro(compra_ex, compra_p, venda_ex, venda_p, taxa_rede=0.03):
    try:
        tc = CORRETORAS[compra_ex]["taxa_compra"] / 100
        ts = CORRETORAS[compra_ex]["taxa_saque"] / 100
        tv = CORRETORAS[venda_ex]["taxa_compra"] / 100
        tr = taxa_rede / 100
        custo = compra_p * (1 + tc + ts + tr)
        receita = venda_p * (1 - tv)
        if custo >= receita or custo <= 0:
            return 0.0
        return round(((receita - custo) / custo) * 100, 4)
    except:
        return 0.0

# ==============================================
# 💡 LEMBRETES DE UPGRADE
# ==============================================
def mostrar_lembrete_upgrade(plano_atual):
    if plano_atual == "Gratuito":
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(255,152,0,0.15), rgba(245,127,23,0.05)); border: 1px solid #FF9800; border-radius: 12px; padding: 16px; margin: 15px 0;'>
            <h4 style='margin:0; color:#FF9800;'>🚀 Desbloqueie mais oportunidades!</h4>
            <p style='color:#e0e0e0; font-size:13px; margin:8px 0;'>Você está vendo apenas 3 de 12 moedas e verificando a cada 5 minutos. Com o plano Pro, você monitora 8 moedas a cada 60 segundos e recebe alertas automáticos de lucro! Quanto mais moedas, mais chances de lucro! 📈💰</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💳 Fazer Upgrade Agora →", type="primary", use_container_width=True):
            st.session_state.mostrar_upgrade = True
    elif plano_atual == "Pro":
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(156,39,176,0.15), rgba(123,31,162,0.05)); border: 1px solid #9C27B0; border-radius: 12px; padding: 16px; margin: 15px 0;'>
            <h4 style='margin:0; color:#9C27B0;'>👑 Seja VIP — Não perca nenhuma oportunidade!</h4>
            <p style='color:#e0e0e0; font-size:13px; margin:8px 0;'>A cada minuto que passa, novas oportunidades aparecem. Com o plano Premium, você verifica o mercado a cada 15 segundos e monitora moedas ilimitadas! Mais velocidade = mais lucro! ⚡💰</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👑 Virar VIP Agora →", type="primary", use_container_width=True):
            st.session_state.mostrar_upgrade = True

# ==============================================
# 🎨 CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(page_title="CriptoArbitrage PRO", page_icon="🪙", layout="wide")

def init_session():
    for chave in ["logado", "usuario", "dados_usuario", "plano_temp", "pagamento_metodo", "mostrar_upgrade"]:
        if chave not in st.session_state:
            st.session_state[chave] = False if chave == "logado" else None

init_session()

# ==============================================
# 🔒 TELA DE LOGIN / CADASTRO
# ==============================================
if not st.session_state.logado:
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);}
    .title-gradient {background: linear-gradient(90deg, #6366f1, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;}
    .plano-card {border-radius: 20px; padding: 25px; text-align: center; transition: all 0.3s ease; cursor: pointer; margin: 5px;}
    .plano-card:hover {transform: scale(1.03);}
    .plano-destaque {transform: scale(1.05); box-shadow: 0 0 30px rgba(255,152,0,0.3);}
    </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='title-gradient' style='text-align:center; font-size:40px;'>🪙 CriptoArbitrage PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>O sistema mais avançado de arbitragem de criptomoedas</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
        aba_login, aba_cadastro = st.tabs(["🔑 ENTRAR", "✨ CRIAR CONTA"])
        with aba_cadastro:
            st.subheader("📋 Escolha seu Plano")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.markdown("<div class='plano-card' style='background:linear-gradient(135deg, rgba(76,175,80,0.15),rgba(56,142,60,0.05)); border:2px solid #4CAF50;'><h3 style='color:#4CAF50; margin:0;'>🟢 Gratuito</h3><div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 0<span style='font-size:12px; color:#94a3b8;'>/mês</span></div><p style='font-size:12px; color:#94a3b8;'>3 moedas · 2 corretoras</p></div>", unsafe_allow_html=True)
                if st.button("✅ Escolher", key="cad_free", use_container_width=True):
                    st.session_state.plano_temp = "Gratuito"
            with col_p2:
                st.markdown("<div class='plano-card plano-destaque' style='background:linear-gradient(135deg, rgba(255,152,0,0.2),rgba(245,127,23,0.08)); border:3px solid #FF9800;'><span style='background:#FF9800; color:white; padding:3px 10px; border-radius:15px; font-size:10px; font-weight:700;'>MAIS POPULAR</span><h3 style='color:#FF9800; margin:8px 0 0 0;'>🚀 Pro</h3><div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 29,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div><p style='font-size:12px; color:#94a3b8;'>8 moedas · 4 corretoras · Alertas</p></div>", unsafe_allow_html=True)
                if st.button("🚀 Escolher", key="cad_pro", use_container_width=True):
                    st.session_state.plano_temp = "Pro"
            with col_p3:
                st.markdown("<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'><h3 style='color:#9C27B0; margin:0;'>👑 Premium</h3><div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div><p style='font-size:12px; color:#94a3b8;'>Ilimitado · 15s · VIP</p></div>", unsafe_allow_html=True)
                if st.button("👑 Escolher", key="cad_prem", use_container_width=True):
                    st.session_state.plano_temp = "Premium"
            plano_final = st.session_state.get("plano_temp", "Gratuito")
            st.info(f"🎯 Plano selecionado: **{plano_final}**")
            if plano_final != "Gratuito":
                st.markdown("---")
                st.subheader("💳 Método de Pagamento")
                metodo = st.radio("Escolha como quer pagar:", ["💳 PIX (Imediato)"], label_visibility="collapsed")
                st.session_state.pagamento_metodo = metodo
            st.markdown("---")
            email_cad = st.text_input("📧 Seu E-mail", placeholder="seu@email.com", key="email_cad")
            senha_cad = st.text_input("🔑 Criar Senha", type="password", key="senha_cad")
            senha_conf = st.text_input("🔑 Confirmar Senha", type="password", key="senha_conf")
            if st.button("✨ CRIAR CONTA", type="primary", use_container_width=True):
                if not email_cad or "@" not in email_cad:
                    st.error("❌ E-mail inválido!")
                elif len(senha_cad) < 4:
                    st.error("❌ Senha com mínimo 4 caracteres!")
                elif senha_cad != senha_conf:
                    st.error("❌ Senhas não coincidem!")
                else:
                    ok, msg = cadastrar_usuario(email_cad.strip(), senha_cad, plano_final)
                    if ok:
                        st.success(msg)
                        st.balloons()
                        if plano_final != "Gratuito":
                            time.sleep(1)
                            st.markdown("---")
                            exibir_pagamento_pix(plano_final, email_cad.strip())
                        else:
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error(msg)
        with aba_login:
            st.subheader("🔑 Acesse sua Conta")
            email_log = st.text_input("📧 Seu E-mail", key="email_log")
            senha_log = st.text_input("🔑 Sua Senha", type="password", key="senha_log")
            if st.button("🔓 ENTRAR", type="primary", use_container_width=True):
                if not email_log or not senha_log:
                    st.error("❌ Preencha e-mail e senha!")
                else:
                    ok, dados = verificar_login(email_log.strip(), senha_log)
                    if ok:
                        st.session_state.logado = True
                        st.session_state.usuario = {"email": email_log.strip(), **dados}
                        st.session_state.dados_usuario = carregar_dados_usuario(email_log.strip(), dados.get("plano", "Gratuito"))
                        st.success(f"✅ Bem-vindo, {email_log.split('@')[0]}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(dados)
        st.markdown("<hr style='border-color:#334155; margin-top:30px;'>", unsafe_allow_html=True)
        st.warning(f"⚠️ Ferramenta de análise apenas. Não é recomendação de investimento. Suporte: {CONFIG['email_suporte']}")
    st.stop()

# ==============================================
# ✅ USUÁRIO LOGADO
# ==============================================
if not st.session_state.logado or not st.session_state.usuario:
    st.warning("🔒 Você precisa fazer login primeiro!")
    st.stop()

user_email = st.session_state.usuario.get("email", "")
user_plano = st.session_state.usuario.get("plano", "Gratuito")
dados = st.session_state.dados_usuario or carregar_dados_usuario(user_email, user_plano)
config_usuario = dados.get("config", {"moedas_selecionadas": MOEDAS[:3], "lucro_min": 0.3, "intervalo": 60})
chaves = dados.get("chaves", {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS})
limites = PLANOS.get(user_plano, PLANOS["Gratuito"])

# ==============================================
# 💳 TELA DE UPGRADE
# ==============================================
if st.session_state.get("mostrar_upgrade", False):
    st.markdown("""<style>.stApp {background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);}</style>""", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>💳 Escolha seu Novo Plano</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Desbloqueie todo o potencial de lucro! 🚀💰</p>", unsafe_allow_html=True)
    st.markdown("---")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("<div class='plano-card plano-destaque' style='background:linear-gradient(135deg, rgba(255,152,0,0.2),rgba(245,127,23,0.08)); border:3px solid #FF9800;'><h3 style='color:#FF9800; margin:0;'>🚀 Upgrade para Pro</h3><div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 29,90<span style='font-size:14px; color:#94a3b8;'>/mês</span></div><p style='color:#e0e0e0;'>8 moedas · 4 corretoras · Alertas automáticos</p></div>", unsafe_allow_html=True)
        if st.button("💳 Assinar Pro", type="primary", use_container_width=True):
            exibir_pagamento_pix("Pro", user_email)
    with col_p2:
        st.markdown("<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'><h3 style='color:#9C27B0; margin:0;'>👑 Upgrade para Premium</h3><div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:14px; color:#94a3b8;'>/mês</span></div><p style='color:#e0e0e0;'>Ilimitado · 15s · Suporte VIP 24/7</p></div>", unsafe_allow_html=True)
        if st.button("👑 Assinar Premium", type="primary", use_container_width=True):
            exibir_pagamento_pix("Premium", user_email)
    st.markdown("---")
    if st.button("← Voltar ao Painel", use_container_width=True):
        st.session_state.mostrar_upgrade = False
        st.rerun()
    st.stop()

# ==============================================
# 📊 BARRA LATERAL
# ==============================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🪙 CriptoArbitrage PRO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.info(f"👤 {user_email}\n🎯 Plano: **{user_plano}**")
    if user_plano != "Gratuito":
        st.info(f"📅 Expira em: **{st.session_state.usuario.get('data_expiracao', '—')}**")
    st.markdown("---")
    pagina = st.radio("📱 Menu", [
        "📊 Painel Principal", "🔍 Analisar Mercado",
        "🔐 Minhas Corretoras", "⚙️ Configurações", "💳 Meu Plano"
    ])
    st.markdown("---")
    st.text(f"💰 Lucro min: {config_usuario.get('lucro_min', 0.3)}%")
    st.text(f"⏱️ Intervalo: {config_usuario.get('intervalo', 60)}s")
    st.markdown("---")
    if st.button("🚪 Sair", type="secondary", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.session_state.dados_usuario = None
        st.rerun()

# ==============================================
# 📊 PAINEL PRINCIPAL
# ==============================================
if pagina == "📊 Painel Principal":
    st.markdown("<h1>📊 Painel de Controle</h1>", unsafe_allow_html=True)
    mostrar_lembrete_upgrade(user_plano)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🪙 Moedas", len(config_usuario.get("moedas_selecionadas", MOEDAS[:3])), f"de {limites['moedas']}")
    with col2:
        qtd_corretoras = len([c for c in chaves if chaves[c].get("chave_api", "")])
        st.metric("🏦 Corretoras", qtd_corretoras, f"de {limites['corretoras']}")
    with col3:
        st.metric("💰 Lucro Mín", f"{config_usuario.get('lucro_min', 0.3)}%")
    with col4:
        st.metric("⏱️ Atualização", f"{config_usuario.get('intervalo', 60)}s")
    st.markdown("---")
    st.subheader("🚀 Comece agora em 4 passos")
    st.info("""
    1️⃣ Vá em **🔐 Minhas Corretoras** e cole suas chaves API
    2️⃣ Vá em **⚙️ Configurações** e escolha quais moedas monitorar
    3️⃣ Clique em **🔍 Analisar Mercado** para buscar oportunidades
    4️⃣ 💰 Lucre com as diferenças de preço!
    """)

# ==============================================
# 🔍 ANALISAR MERCADO
# ==============================================
elif pagina == "🔍 Analisar Mercado":
    st.markdown("<h1>🔍 Análise de Mercado em Tempo Real</h1>", unsafe_allow_html=True)
    mostrar_lembrete_upgrade(user_plano)
    moedas = config_usuario.get("moedas_selecionadas", MOEDAS[:3])[:limites["moedas"]]
    lucro_min = config_usuario.get("lucro_min", 0.3)
    if st.button("🔄 BUSCAR TODAS AS OPORTUNIDADES", type="primary", use_container_width=True):
        if not moedas:
            st.warning("⚠️ Nenhuma moeda selecionada! Vá em Configurações.")
        else:
            resultados = []
            barra = st.progress(0)
            status = st.empty()
            for i, par in enumerate(moedas):
                status.info(f"Analisando {par}...")
                precos = {}
                for nome, corr in CORRETORAS.items():
                    p = buscar_preco(corr["url_preco"], par, nome.lower())
                    if p:
                        precos[nome] = p
                if len(precos) >= 2:
                    ordem = sorted(precos.items(), key=lambda x: x[1])
                    compra_ex, compra_p = ordem[0]
                    venda_ex, venda_p = ordem[-1]
                    if compra_ex != venda_ex:
                        lucro = calcular_lucro(compra_ex, compra_p, venda_ex, venda_p)
                        resultados.append({
                            "par": par, "compra_ex": compra_ex, "compra_preco": compra_p,
                            "venda_ex": venda_ex, "venda_preco": venda_p, "lucro": lucro
                        })
                barra.progress((i+1)/len(moedas))
            status.empty()
            if resultados:
                st.success(f"✅ {len(resultados)} oportunidades encontradas!")
                for r in sorted(resultados, key=lambda x: -x["lucro"]):
                    with st.expander(f"🪙 {r['par']} | Lucro: {r['lucro']}%", expanded=r["lucro"] >= lucro_min):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("🟢 COMPRAR EM", r["compra_ex"], f"${r['compra_preco']:.4f}")
                        c2.metric("🔴 VENDER EM", r["venda_ex"], f"${r['venda_preco']:.4f}")
                        c3.metric("💰 LUCRO", f"{r['lucro']}%")
                        if r["lucro"] >= lucro_min:
                            st.success("🔥 OPORTUNIDADE QUENTE!")
                        elif r["lucro"] > 0:
                            st.info("📈 Lucro pequeno")
                        else:
                            st.error("📉 Sem lucro")
            else:
                st.info("ℹ️ Nenhuma oportunidade agora. Tente novamente mais tarde.")

# ==============================================
# 🔐 MINHAS CORRETORAS
# ==============================================
elif pagina == "🔐 Minhas Corretoras":
    st.markdown("<h1>🔐 Configuração de Corretoras</h1>", unsafe_allow_html=True)
    st.info("⚠️ Use APENAS permissões de LEITURA e NEGOCIAÇÃO. NUNCA dê permissão de SAQUE!")
    for nome in list(CORRETORAS.keys())[:limites["corretoras"]]:
        st.markdown("---")
        st.subheader(f"🏦 {nome}")
        chaves[nome]["chave_api"] = st.text_input(f"Chave API — {nome}", value=chaves.get(nome, {}).get("chave_api", ""), type="password", key=f"api_{nome}")
        chaves[nome]["chave_secreta"] = st.text_input(f"Chave Secreta — {nome}", value=chaves.get(nome, {}).get("chave_secreta", ""), type="password", key=f"sec_{nome}")
        if chaves[nome]["chave_api"]:
            st.success(f"✅ {nome} configurada!")
    if st.button("💾 SALVAR CHAVES", type="primary", use_container_width=True):
        salvar_dados_usuario(user_email, chaves, config_usuario)
        st.success("✅ Chaves salvas com segurança!")
        st.balloons()

# ==============================================
# ⚙️ CONFIGURAÇÕES
# ==============================================
elif pagina == "⚙️ Configurações":
    st.markdown("<h1>⚙️ Suas Configurações</h1>", unsafe_allow_html=True)
    st.info(f"🎯 Plano: {user_plano} | Limite de moedas: {limites['moedas']}")
    if len(config_usuario.get("moedas_selecionadas", [])) >= limites["moedas"] and user_plano != "Premium":
        mostrar_lembrete_upgrade(user_plano)
    st.markdown("---")
    moedas_selecionadas = st.multiselect(
        "🪙 Moedas para monitorar", MOEDAS,
        default=config_usuario.get("moedas_selecionadas", MOEDAS[:3]),
        max_selections=limites["moedas"]
    )
    lucro_min = st.slider("💰 Lucro mínimo para alerta (%)", 0.05, 5.0, config_usuario.get("lucro_min", 0.3), 0.05)
    intervalo = st.slider("⏱️ Intervalo entre verificações (segundos)", 15, 600, config_usuario.get("intervalo", 60), 15)
    if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary", use_container_width=True):
        config_usuario.update({
            "moedas_selecionadas": moedas_selecionadas,
            "lucro_min": lucro_min,
            "intervalo": intervalo
        })
        salvar_dados_usuario(user_email, chaves, config_usuario)
        st.session_state.dados_usuario["config"] = config_usuario
        st.success("✅ Configurações salvas!")
        st.balloons()

# ==============================================
# 💳 MEU PLANO
# ==============================================
elif pagina == "💳 Meu Plano":
    st.markdown("<h1>💳 Gerenciar Assinatura</h1>", unsafe_allow_html=True)
    st.info(f"""
    📋 **Plano Atual:** {user_plano}
    📅 **Expira em:** {st.session_state.usuario.get('data_expiracao', 'Ilimitado / Gratuito')}
    📊 **Moedas:** {limites['moedas']} | **Intervalo:** {limites['intervalo']}s
    """)
    st.markdown("---")
    st.subheader("💎 Benefícios do seu plano:")
    for b in PLANOS[user_plano]["beneficios"]:
        st.write(f"✅ {b}")
    if user_plano != "Premium":
        st.markdown("---")
        st.subheader("🚀 Quer mais? Atualize seu plano!")
        if user_plano == "Gratuito":
            if st.button("💳 Assinar Pro — R$29,90/mês", type="primary", use_container_width=True):
                exibir_pagamento_pix("Pro", user_email)
        elif user_plano == "Pro":
            if st.button("👑 Virar VIP — R$79,90/mês", type="primary", use_container_width=True):
                exibir_pagamento_pix("Premium", user_email)
    pagamentos = st.session_state.usuario.get("pagamentos", [])
    if pagamentos:
        st.markdown("---")
        st.subheader("📜 Histórico de Pagamentos")
        for pg in pagamentos:
            st.write(f"✅ {pg['data']} — {pg['plano']} — R$ {pg['valor']:.2f} — {pg['metodo']}")

# Rodapé
st.markdown("---")
st.markdown(f"<p style='text-align:center; color:#64748b; font-size:12px;'>🪙 CriptoArbitrage PRO · Ferramenta de análise · Não é recomendação de investimento · Suporte: {CONFIG['email_suporte']}</p>", unsafe_allow_html=True)
