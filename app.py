import streamlit as st
import json
import os
import time
import requests
from datetime import datetime
from urllib.parse import quote

# ==============================================
# ⚙️ CONFIGURAÇÕES DO SISTEMA — ATUALIZE ABAIXO!
# ==============================================
st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

CONFIG = {
    "pix_nome_recebedor": "Inacio Silva",
    "pix_chave": "11571293744",
    "whatsapp_admin": "5521997524939",
    "email_suporte": "suportearbitrageai@gmail.com"
}

ARQUIVO_USUARIOS = "usuarios.json"

PLANOS = {
    "Gratuito": {"preco": 0, "moedas": 3, "intervalo": 120, "suporte": "Básico"},
    "Pro": {"preco": 49.90, "moedas": 999, "intervalo": 60, "suporte": "Prioritário"},
    "Premium": {"preco": 99.90, "moedas": 999, "intervalo": 15, "suporte": "VIP 24/7"}
}

CORRETORAS = {
    "Binance": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Bybit": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "KuCoin": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Gate.io": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "OKX": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1}
}

# ==============================================
# 📂 FUNÇÕES DE BANCO DE DADOS
# ==============================================
def carregar_json(arquivo):
    if not os.path.exists(arquivo):
        return {}
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return True

def gerar_id_pagamento():
    return f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ==============================================
# 🔐 AUTENTICAÇÃO
# ==============================================
def criar_conta(email, senha, plano):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email in usuarios:
        return False, "Email já cadastrado!"
    
    usuarios[email] = {
        "senha": senha,
        "plano": plano,
        "status_pagamento": "aprovado" if plano == "Gratuito" else "pendente",
        "plano_ativo": True if plano == "Gratuito" else False,
        "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "chaves": {},
        "config": {"lucro_min": 0.3, "intervalo": 60}
    }
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True, "Conta criada com sucesso!"

def verificar_login(email, senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False, "Email não encontrado!"
    if usuarios[email]["senha"] != senha:
        return False, "Senha incorreta!"
    return True, usuarios[email]

def carregar_dados_usuario(email, plano_padrao="Gratuito"):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    return usuarios.get(email, {
        "plano": plano_padrao,
        "status_pagamento": "aprovado",
        "plano_ativo": True,
        "chaves": {},
        "config": {"lucro_min": 0.3, "intervalo": 60}
    })

def salvar_dados_usuario(email, chaves, config_usuario):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    usuarios[email]["chaves"] = chaves
    usuarios[email]["config"] = config_usuario
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

# ==============================================
# 💳 PAGAMENTO VIA PIX
# ==============================================
def gerar_codigo_pix(valor, descricao, email):
    chave = CONFIG["pix_chave"]
    nome = CONFIG["pix_nome_recebedor"]
    return f"00020126580014br.gov.bcb.pix0136{chave}5204000053039865802BR59{len(nome):02d}{nome}6008BRASILIA62070503***64330015{email}0103{descricao}6502BR7301.00", chave

def registrar_pagamento_pendente(email, plano, valor, id_pag, nome_arquivo):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    usuarios[email]["plano_escolhido"] = plano
    usuarios[email]["valor_pago"] = valor
    usuarios[email]["id_pagamento"] = id_pag
    usuarios[email]["comprovante"] = nome_arquivo
    usuarios[email]["status_pagamento"] = "pendente"
    usuarios[email]["data_pagamento"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def gerar_link_whatsapp(email, plano, valor, id_pag, arquivo):
    texto = f"""NOVO PAGAMENTO PENDENTE! 📋

👤 Cliente: {email}
💳 Plano: {plano}
💰 Valor: R$ {valor:.2f}
🆔 ID: {id_pag}
📎 Comprovante: {arquivo}

Acesse o painel para aprovar! ✅"""
    return f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"

def exibir_pagamento_pix(plano, email_cliente):
    valor = PLANOS[plano]["preco"]
    id_pag = gerar_id_pagamento()
    desc = f"Plano {plano} - {email_cliente}"
    codigo_pix, chave_pix = gerar_codigo_pix(valor, desc, email_cliente)

    st.session_state["pix_plano"] = plano
    st.session_state["pix_valor"] = valor
    st.session_state["pix_id"] = id_pag
    st.session_state["pix_email"] = email_cliente

    st.markdown(f"""
    <div style='background:rgba(30,41,59,0.9);border:1px solid #22c55e;border-radius:16px;padding:24px;text-align:center;margin:20px 0;'>
    <h3 style='color:#22c55e;margin:0;'>💳 Pagamento via PIX</h3>
    <p style='color:#94a3b8;font-size:14px;margin:10px 0;'>Plano: <strong>{plano}</strong> — Valor: <strong>R$ {valor:.2f}</strong></p>
    <p style='color:#e2e8f0;font-size:13px;'>ID: <code style='background:#1e293b;padding:4px 8px;border-radius:4px;'>{id_pag}</code></p>
    </div>""", unsafe_allow_html=True)

    st.info(f"🔑 **Chave Pix:** `{chave_pix}`")
    st.info(f"👤 **Recebedor:** {CONFIG['pix_nome_recebedor']}")
    st.code(codigo_pix, language="text")
    st.markdown("---")
    st.subheader("📤 Passo a passo")
    st.info("1️⃣ Copie o código e pague no seu banco • 2️⃣ Tire print do comprovante • 3️⃣ Anexe abaixo")

    plano_atual = st.session_state.get("pix_plano", plano)
    valor_atual = st.session_state.get("pix_valor", valor)
    id_atual = st.session_state.get("pix_id", id_pag)
    email_atual = st.session_state.get("pix_email", email_cliente)

    comprovante = st.file_uploader("📎 Anexar comprovante de pagamento", type=["jpg","jpeg","png"], key=f"comp_{id_atual}")

    if comprovante:
        st.success(f"✅ Comprovante carregado: {comprovante.name}")
        st.image(comprovante, width=300)
        st.markdown("---")

        if st.button("✅ JÁ PAGUEI — ENVIAR PARA APROVAÇÃO!", type="primary", use_container_width=True):
            if registrar_pagamento_pendente(email_atual, plano_atual, valor_atual, id_atual, comprovante.name):
                link_whats = gerar_link_whatsapp(email_atual, plano_atual, valor_atual, id_atual, comprovante.name)
                st.success("🎉 Comprovante enviado com sucesso!")
                st.balloons()

                st.markdown(f"""
                <div style='text-align:center;padding:20px;background:rgba(37,211,102,0.1);border-radius:12px;margin:20px 0;'>
                <h3 style='color:#25d366;margin:0;'>📱 Envie pelo WhatsApp</h3>
                <a href="{link_whats}" target="_blank" style="display:inline-block;background:#25d366;color:white;padding:14px 30px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:18px;margin:20px 0;box-shadow:0 4px 12px rgba(37,211,102,0.3);">💬 CLIQUE AQUI — ENVIAR NO WHATSAPP</a>
                <p style='color:#94a3b8;font-size:14px;'>Abre em nova aba → envie a mensagem com a imagem!</p>
                </div>
                """, unsafe_allow_html=True)

                st.info("✅ Pronto! Aguarde a aprovação que chegará em breve!")
                st.info("💡 Não precisa ficar na página aberta. Você receberá notificação!")

                for chave in ["pix_plano","pix_valor","pix_id","pix_email"]:
                    if chave in st.session_state:
                        del st.session_state[chave]
                st.stop()
            else:
                st.error("❌ Erro ao registrar. Contate o suporte.")
    else:
        st.info("👆 Selecione o comprovante acima para habilitar o botão")

# ==============================================
# 🔍 SCANNER DE ARBITRAGEM
# ==============================================
def buscar_preco_bolsa(simbolo, corretora):
    par = simbolo.upper() + "USDT"
    urls = {
        "Binance": f"https://api.binance.com/api/v3/ticker/price?symbol={par}",
        "Bybit": f"https://api.bybit.com/v2/public/tickers?symbol={par}",
        "KuCoin": f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={par}",
        "Gate.io": f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={simbolo.upper()}_USDT",
        "OKX": f"https://www.okx.com/api/v5/market/ticker?instId={simbolo.upper()}-USDT"
    }
    if corretora not in urls:
        return None
    try:
        resp = requests.get(urls[corretora], timeout=10)
        dados = resp.json()
        if corretora == "Binance" and "price" in dados:
            return float(dados["price"])
        elif corretora == "Bybit" and "result" in dados and dados["result"]:
            return float(dados["result"][0]["last_price"])
        elif corretora == "KuCoin" and dados.get("code") == "200000" and "data" in dados:
            return float(dados["data"]["price"])
        elif corretora == "Gate.io" and isinstance(dados, list) and len(dados) > 0:
            return float(dados[0]["last"])
        elif corretora == "OKX" and dados.get("code") == "0" and "data" in dados:
            return float(dados["data"][0]["last"])
    except Exception as e:
        pass
    return None

def escanear_oportunidades(lista_moedas=["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "MATIC"]):
    corretoras_ativas = list(CORRETORAS.keys())
    oportunidades = []
    for moeda in lista_moedas:
        precos = {}
        for bolsa in corretoras_ativas:
            preco = buscar_preco_bolsa(moeda, bolsa)
            if preco and preco > 0:
                precos[bolsa] = preco
        if len(precos) >= 2:
            mais_barata = min(precos.items(), key=lambda x: x[1])
            mais_cara = max(precos.items(), key=lambda x: x[1])
            spread_pct = ((mais_cara[1] - mais_barata[1]) / mais_barata[1]) * 100
            if spread_pct >= 0.1:
                oportunidades.append({
                    "moeda": moeda,
                    "comprar_bolsa": mais_barata[0],
                    "comprar_preco": mais_barata[1],
                    "vender_bolsa": mais_cara[0],
                    "vender_preco": mais_cara[1],
                    "lucro_pct": round(spread_pct, 2)
                })
    return sorted(oportunidades, key=lambda x: x["lucro_pct"], reverse=True)

def salvar_no_historico(oportunidade):
    if "historico" not in st.session_state:
        st.session_state["historico"] = []
    oportunidade["hora"] = datetime.now().strftime("%d/%m %H:%M")
    st.session_state["historico"].insert(0, oportunidade)
    st.session_state["historico"] = st.session_state["historico"][:50]

# ==============================================
# ⏰ HISTÓRICO DE OPORTUNIDADES
# ==============================================
def exibir_historico():
    st.title("⏰ Histórico de Oportunidades")
    historico = st.session_state.get("historico", [])
    if not historico:
        st.info("Ainda sem histórico. Escaneie no Scanner para começar!")
        return
    st.info(f"📋 {len(historico)} oportunidades registradas")
    for op in historico[:15]:
        cor = "#22c55e" if op["lucro_pct"] >= 1 else "#f59e0b"
        st.markdown(f"""
        <div style='background:rgba(30,41,59,0.5);border-left:3px solid {cor};border-radius:8px;padding:12px;margin:6px 0;'>
            <strong>{op['moeda']}</strong> • {op['hora']} • 
            <span style='color:{cor};font-weight:bold;'>+{op['lucro_pct']}%</span><br>
            <small>Compra: {op['comprar_bolsa']} | Venda: {op['vender_bolsa']}</small>
        </div>
        """, unsafe_allow_html=True)

# ==============================================
# 📊 RESUMO DE MERCADO
# ==============================================
def exibir_resumo_mercado():
    st.title("📊 Resumo de Mercado")
    st.info("Preços em tempo real — Binance")
    moedas = [("BTC", "Bitcoin"), ("ETH", "Ethereum"), ("SOL", "Solana"), ("XRP", "Ripple"), ("ADA", "Cardano")]
    cols = st.columns(len(moedas))
    for idx, (sigla, nome) in enumerate(moedas):
        preco = buscar_preco_bolsa(sigla, "Binance")
        with cols[idx]:
            if preco:
                st.metric(sigla, f"${preco:,.2f}")
            else:
                st.metric(sigla, "—")

# ==============================================
# 🔔 SISTEMA DE ALERTAS
# ==============================================
def exibir_sistema_alertas():
    st.title("🔔 Alertas de Oportunidade")
    lucro_alvo = st.slider("Avisar quando lucro for ≥ (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    if st.button("🔔 VERIFICAR AGORA", type="primary", use_container_width=True):
        with st.spinner("Buscando oportunidades..."):
            ops = escanear_oportunidades()
            alertas = [o for o in ops if o["lucro_pct"] >= lucro_alvo]
        if alertas:
            st.success(f"🚨 {len(alertas)} oportunidades acima de {lucro_alvo}%!")
            for alerta in alertas:
                st.markdown(f"""
                <div style='background:rgba(34,197,94,0.1);border-radius:8px;padding:12px;margin:8px 0;'>
                <h4 style='margin:0;'>⚡ {alerta['moeda']} — {alerta['lucro_pct']}%</h4>
                <p>✅ Comprar: {alerta['comprar_bolsa']} → ${alerta['comprar_preco']:.4f}</p>
                <p>📤 Vender: {alerta['vender_bolsa']} → ${alerta['vender_preco']:.4f}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"✅ Nenhuma oportunidade acima de {lucro_alvo}% no momento.")

# ==============================================
# 🧮 CALCULADORA DE LUCRO REAL
# ==============================================
def calcular_lucro_liquido(valor_inv, preco_c, preco_v, taxa_c=0.1, taxa_v=0.1):
    valor_apos_taxa = valor_inv * (1 - taxa_c / 100)
    qtd = valor_apos_taxa / preco_c
    valor_bruto = qtd * preco_v
    valor_final = valor_bruto * (1 - taxa_v / 100)
    lucro = valor_final - valor_inv
    return lucro, (lucro / valor_inv) * 100, valor_final

def exibir_calculadora():
    st.title("🧮 Calculadora de Lucro Real")
    st.info("Desconta taxas → mostra o que REALMENTE entra no bolso!")
    col1, col2 = st.columns(2)
    with col1:
        valor_inv = st.number_input("Valor a investir (R$)", min_value=10.0, value=1000.0, step=50.0)
        preco_c = st.number_input("Preço de Compra", min_value=0.0001, step=0.0001, format="%.4f")
        taxa_c = st.number_input("Taxa Compra (%)", value=0.1, step=0.01)
    with col2:
        preco_v = st.number_input("Preço de Venda", min_value=0.0001, step=0.0001, format="%.4f")
        taxa_v = st.number_input("Taxa Venda (%)", value=0.1, step=0.01)
    if st.button("🧮 CALCULAR LUCRO", type="primary", use_container_width=True):
        lucro_val, lucro_pct, valor_final = calcular_lucro_liquido(valor_inv, preco_c, preco_v, taxa_c, taxa_v)
        cor = "#22c55e" if lucro_val > 0 else "#ef4444"
        st.markdown(f"""
        <div style='background:rgba(30,41,59,0.7);border-radius:12px;padding:24px;text-align:center;'>
            <h2 style='color:{cor};margin:0;'>Lucro Líquido: R$ {lucro_val:.2f}</h2>
            <p style='font-size:18px;'>{lucro_pct:.2f}%</p>
            <p>Investimento: R$ {valor_inv:.2f} → Saldo Final: R$ {valor_final:.2f}</p>
            <p style='color:#94a3b8;font-size:13px;'>Taxas: {taxa_c}% (compra) + {taxa_v}% (venda) já descontadas</p>
        </div>
        """, unsafe_allow_html=True)

# ==============================================
# 🔍 SCANNER ATUALIZADO COM FILTRO E COMPARTILHAR
# ==============================================
def exibir_scanner_arbitragem():
    st.title("🔍 Scanner de Arbitragem")
    st.markdown("Compara preços em tempo real entre Binance, Bybit, KuCoin, Gate.io e OKX!")
    st.info("🔒 **Modo Seguro** — Apenas sinais. Você executa manualmente.")
    
    lucro_minimo = st.slider("Mostrar apenas lucro ≥ (%)", min_value=0.1, max_value=5.0, value=0.3, step=0.1)
    moedas = st.multiselect("Escolha as moedas", 
                            ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "MATIC"],
                            default=["BTC", "ETH", "SOL", "XRP"])
    
    if st.button("🔍 ESCANEAR", type="primary", use_container_width=True):
        with st.spinner("Buscando em todas as bolsas..."):
            ops = escanear_oportunidades(moedas)
        
        ops = [o for o in ops if o["lucro_pct"] >= lucro_minimo]
        
        if not ops:
            st.success("✅ Sem oportunidades no momento. Preços alinhados!")
            return
        
        st.subheader(f"✅ {len(ops)} Oportunidades Encontradas!")
        st.markdown("---")
        
        for op in ops:
            salvar_no_historico(op)
            cor = "#22c55e" if op["lucro_pct"] >= 1 else "#f59e0b"
            
            texto_msg = f"""🚨 OPORTUNIDADE DE ARBITRAGEM! 🚨

🪙 {op['moeda']}
✅ COMPRAR: {op['comprar_bolsa']} → ${op['comprar_preco']:.4f}
📤 VENDER: {op['vender_bolsa']} → ${op['vender_preco']:.4f}
💰 Lucro: {op['lucro_pct']}%

Via Arbitragem AI 🤖"""
            link_whats = f"https://wa.me/?text={quote(texto_msg)}"
            
            st.markdown(f"""
            <div style='background:rgba(30,41,59,0.7);border-left:4px solid {cor};border-radius:12px;padding:16px;margin:12px 0;'>
                <h3 style='margin:0 0 10px 0;color:white;'>🪙 {op['moeda']} — Lucro: <span style='color:{cor}'>{op['lucro_pct']}%</span></h3>
                <p style='margin:4px 0;'>✅ <strong>COMPRAR:</strong> {op['comprar_bolsa']} → US$ {op['comprar_preco']:.4f}</p>
                <p style='margin:4px 0;'>📤 <strong>VENDER:</strong> {op['vender_bolsa']} → US$ {op['vender_preco']:.4f}</p>
                <a href="{link_whats}" target="_blank" style="display:inline-block;margin-top:10px;background:#25d366;color:white;padding:6px 14px;border-radius:50px;text-decoration:none;font-size:13px;">📱 Compartilhar no WhatsApp</a>
            </div>
            """, unsafe_allow_html=True)

# ==============================================
# 🚀 INTERFACE PRINCIPAL
# ==============================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

st.title("🤖 Arbitragem AI")
st.warning(f"⚠️ Ferramenta de análise apenas. Não é recomendação de investimento. Suporte: {CONFIG['email_suporte']}")
st.markdown("---")

if not st.session_state.usuario:
    aba1, aba2, aba3 = st.tabs(["🔑 Entrar", "✨ Criar Conta", "🔓 Recuperar Senha"])
    
    with aba1:
        st.subheader("Fazer Login")
        email_login = st.text_input("Seu email", key="email_login")
        senha_login = st.text_input("Sua senha", type="password", key="senha_login")
        if st.button("🔑 ENTRAR", type="primary", use_container_width=True):
            ok, resp = verificar_login(email_login, senha_login)
            if ok:
                st.session_state.usuario = resp
                st.rerun()
            else:
                st.error(resp)
    
    with aba2:
        st.subheader("Criar Nova Conta")
        email_cad = st.text_input("Seu email", key="email_cad")
        senha_cad = st.text_input("Criar senha", type="password", key="senha_cad")
        plano_escolhido = st.selectbox("Escolha seu plano", list(PLANOS.keys()))
        
        if st.button("✅ CRIAR CONTA", type="primary", use_container_width=True):
            if "@" not in email_cad:
                st.error("Digite um email válido!")
            elif len(senha_cad) < 4:
                st.error("Senha com pelo menos 4 caracteres!")
            else:
                ok, msg = criar_conta(email_cad, senha_cad, plano_escolhido)
                if ok:
                    st.success(msg)
                    st.balloons()
                    if plano_escolhido != "Gratuito":
                        exibir_pagamento_pix(plano_escolhido, email_cad)
                        st.stop()
                    else:
                        st.session_state.usuario = carregar_dados_usuario(email_cad, plano_escolhido)
                        st.rerun()
                else:
                    st.error(msg)
    
    with aba3:
        st.info("🔧 Recuperação: contate o suporte pelo WhatsApp.")

else:
    user_email = st.session_state.usuario.get("email", "")
    user_plano = st.session_state.usuario.get("plano", "Gratuito")
    ativo = st.session_state.usuario.get("plano_ativo", True)
    status = st.session_state.usuario.get("status_pagamento", "aprovado")
    
    with st.sidebar:
        st.markdown(f"""
        <div style='background:rgba(34,197,94,0.1);border-radius:12px;padding:12px;margin-bottom:20px;'>
        <p style='margin:0;'>👤 <strong>{user_email}</strong></p>
        <p style='margin:5px 0;'>💳 Plano: {user_plano}</p>
        <p style='margin:0;color:{"#22c55e" if ativo else "#f59e0b"};'>⏳ Status: {"ATIVO" if ativo else status.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not ativo and user_plano != "Gratuito":
            st.warning("⏳ Aguardando aprovação do pagamento.")
        
        st.markdown("---")
        pagina = st.radio("Menu", [
            "📊 Painel Principal",
            "🔍 Scanner de Arbitragem",
            "⏰ Histórico",
            "🔔 Alertas",
            "🧮 Calculadora de Lucro",
            "📈 Resumo de Mercado",
            "⚙️ Minhas Corretoras",
            "🔧 Configurações",
            "💳 Meu Plano"
        ])
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Sair da conta", type="secondary", use_container_width=True):
            st.session_state.usuario = None
            st.rerun()
    
    if pagina == "📊 Painel Principal":
        st.header("📊 Painel Principal")
        dados = carregar_dados_usuario(user_email, user_plano)
        cfg = dados.get("config", {})
        col1, col2 = st.columns(2)
        with col1:
            st.text(f"💰 Lucro mínimo: {cfg.get('lucro_min', 0.3)}%")
        with col2:
            st.text(f"⏱️ Intervalo: {cfg.get('intervalo', 60)}s")
        st.markdown("---")
        if not ativo and user_plano != "Gratuito":
            st.info("⏳ Pagamento pendente! Envie o comprovante pelo WhatsApp.")
        else:
            st.success("✅ Plano ativo! Aproveite!")
    
    elif pagina == "🔍 Scanner de Arbitragem":
        if not ativo and user_plano != "Gratuito":
            st.warning("🔒 Libere seu plano para acessar.")
        else:
            exibir_scanner_arbitragem()
    
    elif pagina == "⏰ Histórico":
        exibir_historico()
    
    elif pagina == "🔔 Alertas":
        exibir_sistema_alertas()
    
    elif pagina == "🧮 Calculadora de Lucro":
        exibir_calculadora()
    
    elif pagina == "📈 Resumo de Mercado":
        exibir_resumo_mercado()
    
    elif pagina == "⚙️ Minhas Corretoras":
        st.header("⚙️ Minhas Corretoras")
        dados = carregar_dados_usuario(user_email, user_plano)
        chaves = dados.get("chaves", {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS})
        for nome in CORRETORAS:
            st.subheader(f"🔌 {nome}")
            api = st.text_input(f"Chave API — {nome}", value=chaves.get(nome, {}).get("chave_api", ""), type="password", key=f"api_{nome}")
            seg = st.text_input(f"Chave Secreta — {nome}", value=chaves.get(nome, {}).get("chave_secreta", ""), type="password", key=f"seg_{nome}")
            chaves[nome] = {"chave_api": api, "chave_secreta": seg}
            st.markdown("---")
        if st.button("💾 SALVAR CHAVES", type="primary", use_container_width=True):
            if salvar_dados_usuario(user_email, chaves, dados.get("config", {})):
                st.success("✅ Salvo!")
    
    elif pagina == "🔧 Configurações":
        st.header("🔧 Configurações")
        dados = carregar_dados_usuario(user_email, user_plano)
        cfg = dados.get("config", {})
        lucro_min = st.number_input("Lucro mínimo para alerta (%)", value=float(cfg.get("lucro_min", 0.3)), step=0.1)
        intervalo = st.number_input("Intervalo de verificação (segundos)", value=int(cfg.get("intervalo", 60)), step=5)
        if st.button("💾 SALVAR", type="primary", use_container_width=True):
            if salvar_dados_usuario(user_email, dados.get("chaves", {}), {"lucro_min": lucro_min, "intervalo": intervalo}):
                st.success("✅ Configurações salvas!")
    
    elif pagina == "💳 Meu Plano":
        st.header("💳 Gerenciar Assinatura")
        st.markdown(f"""
        <div style='background:rgba(30,41,59,0.7);border-radius:12px;padding:16px;margin:10px 0;'>
        <p><strong>Plano Atual:</strong> {user_plano}</p>
        <p><strong>Status:</strong> {status.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        if not ativo and user_plano != "Gratuito":
            st.info("Aguardando aprovação do comprovante enviado.")
