import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from urllib import request

# ==============================================
# 🤖 ARBITRAGEM AI — VERSÃO COMPLETA
# 💳 Pix + Upload de Comprovante + Aprovação Manual + WhatsApp + Bloqueio de Páginas
# ==============================================

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PAGAMENTOS = "pagamentos.json"
ARQUIVO_COMPROVANTES = "comprovantes.json"
ADMIN_EMAIL = "suportearbitrageai@gmail.com"
SEU_WHATSAPP = "5521997524939"

# ==============================================
# ⚙️ SUAS CONFIGURAÇÕES
# ==============================================
CONFIG = {
    "pix_chave": "11571293744",
    "pix_nome_recebedor": "Inácio Luiz Santos da Silva",
    "pix_cidade": "Itaboraí",
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
        "status_pagamento": "aprovado" if plano == "Gratuito" else "pendente",
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

def registrar_pagamento_pendente(email, plano, valor, id_transacao, comprovante_nome=""):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    
    usuarios[email]["plano"] = plano
    usuarios[email]["plano_ativo"] = False
    usuarios[email]["status_pagamento"] = "pendente"
    
    if "pagamentos" not in usuarios[email]:
        usuarios[email]["pagamentos"] = []
    
    usuarios[email]["pagamentos"].append({
        "id": id_transacao, "plano": plano, "valor": valor, "metodo": "Pix",
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "status": "pendente",
        "comprovante": comprovante_nome
    })
    
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    
    comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
    comprovantes.append({
        "id": id_transacao,
        "email": email,
        "plano": plano,
        "valor": valor,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "comprovante_nome": comprovante_nome,
        "status": "pendente"
    })
    salvar_json(ARQUIVO_COMPROVANTES, comprovantes)
    
    return True

def aprovar_usuario(email):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    usuarios[email]["plano_ativo"] = True
    usuarios[email]["status_pagamento"] = "aprovado"
    expiracao = datetime.now() + timedelta(days=30)
    usuarios[email]["data_expiracao"] = expiracao.strftime("%d/%m/%Y")
    
    comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
    for c in comprovantes:
        if c["email"] == email and c["status"] == "pendente":
            c["status"] = "aprovado"
    salvar_json(ARQUIVO_COMPROVANTES, comprovantes)
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

def gerar_link_whatsapp(email, plano, valor, id_transacao):
    mensagem = f"""📥 NOVO PAGAMENTO PARA APROVAR!

👤 Cliente: {email}
📋 Plano: {plano}
💰 Valor: R$ {valor:.2f}
🆔 ID Transação: {id_transacao}
📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

✅ Comprovante anexado! Por favor, verifique e aprove o plano do cliente no painel de administração.

🤖 Arbitragem AI"""
    from urllib.parse import quote
    link = f"https://wa.me/{SEU_WHATSAPP}?text={quote(mensagem)}"
    return link

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
    st.markdown("---")
    
    st.subheader("📤 Envie seu comprovante")
    st.info("1. Pague o Pix acima  •  2. Tire print do comprovante  •  3. Anexe a imagem abaixo")
    
    comprovante = st.file_uploader("Anexar comprovante de pagamento", type=["jpg", "jpeg", "png"], key=f"comprovante_{id_pagamento}")
    
    if comprovante:
        st.success(f"✅ Comprovante enviado: {comprovante.name}")
        st.image(comprovante, width=300)
        
        if st.button("✅ JÁ PAGUEI — ENVIAR PARA APROVAÇÃO!", type="primary", use_container_width=True):
            if registrar_pagamento_pendente(email_cliente, plano, valor, id_pagamento, comprovante.name):
                link_whatsapp = gerar_link_whatsapp(email_cliente, plano, valor, id_pagamento)
                st.success("""🎉 Comprovante enviado com sucesso! 
                ⏳ Seu plano está aguardando aprovação. Em breve você receberá acesso!""")
                st.balloons()
                
                st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank" style="
                    display: inline-block;
                    background: #25d366;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 50px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 16px;
                    margin: 15px 0;
                    width: 100%;
                    text-align: center;
                ">💬 ENVIAR COMPROVANTE NO WHATSAPP</a>
                """, unsafe_allow_html=True)
                
                st.info("💡 Clique no botão acima para abrir o WhatsApp e enviar a imagem do comprovante para nós! Assim que aprovarmos, seu plano será ativado.")
                time.sleep(3)
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
# 🛡️ BLOQUEIA PÁGINAS SE PENDENTE
# ==============================================
def verificar_aprovacao():
    if not st.session_state.usuario.get("plano_ativo", False):
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(255,193,7,0.15), rgba(255,152,0,0.05)); 
                    border: 2px solid #FF9800; border-radius: 16px; padding: 30px; text-align: center; margin: 40px 0;'>
            <h2 style='color:#FF9800; margin:0;'>⏳ AGUARDANDO APROVAÇÃO</h2>
            <p style='color:#e0e0e0; font-size:16px; margin:15px 0;'>Seu pagamento está sendo verificado. 
            Enquanto isso, os recursos de negociação estão bloqueados.</p>
            <p style='color:#94a3b8;'>📧 Enviamos uma mensagem no WhatsApp com as instruções. 
            Assim que aprovarmos, você receberá acesso completo!</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("💬 Dúvidas? Fale conosco pelo WhatsApp: +55 21 99752-4939")
        st.stop()
    return True

# ==============================================
# 🎨 CONFIGURAÇÃO DA PÁGINA
# ==============================================
st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

def init_session():
    for chave in ["logado", "usuario", "dados_usuario", "plano_temp", "pagamento_metodo", "mostrar_upgrade", "admin_mode"]:
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
        st.markdown("<h1 class='title-gradient' style='text-align:center; font-size:40px;'>🤖 Arbitragem AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>Inteligência Artificial lucrando para você 24h</p>", unsafe_allow_html=True)
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
                