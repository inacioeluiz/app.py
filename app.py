import streamlit as st
import json
import os
import requests
from datetime import datetime
from urllib.parse import quote

# ==============================================
# ⚙️ CONFIGURAÇÕES — ATUALIZE SEUS DADOS ABAIXO!
# ==============================================
st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

CONFIG = {
    "pix_nome_recebedor": "Seu Nome Completo",
    "pix_chave": "sua.chave.pix@exemplo.com",
    "whatsapp_admin": "5521997524939",
    "email_suporte": "seuemail@exemplo.com",
    "coinmarketcap_api_key": ""  # Coloque sua chave aqui
}

SENHA_ADMIN = "admin123"
ARQUIVO_USUARIOS = "usuarios.json"

PLANOS = {
    "Gratuito": {
        "preco": 0.00,
        "moedas": 3,
        "intervalo": 120,
        "suporte": "Básico",
        "descricao": "Ideal para começar"
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 999,
        "intervalo": 60,
        "suporte": "Prioritário",
        "descricao": "Para quem quer crescer"
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 999,
        "intervalo": 15,
        "suporte": "VIP 24/7",
        "descricao": "Máxima velocidade"
    }
}

CORRETORAS = {
    "Binance": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Bybit": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "KuCoin": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Gate.io": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "OKX": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1}
}

# ==============================================
# 📂 BANCO DE DADOS
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
# 💳 PIX — CÓDIGO + QR Code
# ==============================================
def gerar_codigo_pix(valor, descricao, email):
    chave = CONFIG["pix_chave"]
    nome = CONFIG["pix_nome_recebedor"]
    return f"00020126580014br.gov.bcb.pix0136{chave}5204000053039865802BR59{len(nome):02d}{nome}6008BRASILIA62070503***64330015{email}0103{descricao}6502BR7301{valor:.2f}".replace(".", ""), chave

def gerar_link_qr_pix(codigo_pix):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(codigo_pix)}"

def registrar_pagamento_pendente(email, plano, valor, id_pag, nome_arquivo=""):
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

def notificar_admin(email, plano, valor, id_pag, arquivo=""):
    texto = f"""🔔 NOVO PAGAMENTO PENDENTE!

👤 Cliente: {email}
💳 Plano: {plano}
💰 Valor: R$ {valor:.2f}
🆔 ID: {id_pag}
📎 Comprovante: {arquivo or "Aguardando envio"}

Acesse o Painel de Administração para aprovar! ✅"""
    link_whats = f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"
    
    if "notificacoes" not in st.session_state:
        st.session_state["notificacoes"] = []
    st.session_state["notificacoes"].insert(0, {
        "tipo": "pagamento_pendente",
        "email": email,
        "plano": plano,
        "valor": valor,
        "id": id_pag,
        "hora": datetime.now().strftime("%d/%m %H:%M"),
        "lida": False
    })
    return link_whats

def exibir_escolha_planos(email_cliente):
    st.markdown("## 💳 Escolha seu Plano")
    st.markdown("---")
    
    cols = st.columns(3)
    for idx, (nome, dados) in enumerate(PLANOS.items()):
        destaque = nome != "Gratuito"
        with cols[idx]:
            st.markdown(f"""
            <div style='background:rgba(30,41,59,0.8);border:2px solid {"#f59e0b" if destaque else "#4b5563"};border-radius:16px;padding:24px;text-align:center;height:100%;{"transform:scale(1.05);" if destaque else ""}'>
                <h3 style='color:{"#f59e0b" if destaque else "#9ca3af"};margin:0;'>{nome}</h3>
                <p style='color:#94a3b8;font-size:13px;'>{dados['descricao']}</p>
                <p style='font-size:32px;font-weight:bold;margin:15px 0;'>
                    {'Grátis' if dados['preco'] == 0 else f"R$ {dados['preco']:.2f}"}
                </p>
                <p style='font-size:13px;color:#94a3b8;'>
                    🔄 Atualização: {dados['intervalo']}s<br>
                    ⚙️ Moedas: {dados['moedas']}<br>
                    📞 Suporte: {dados['suporte']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"✅ Escolher — {nome}", key=f"plano_{nome}", use_container_width=True, type="primary" if destaque else "secondary"):
                st.session_state["plano_escolhido"] = nome
                st.rerun()
    
    if "plano_escolhido" in st.session_state:
        plano = st.session_state["plano_escolhido"]
        valor = PLANOS[plano]["preco"]
        
        if valor == 0:
            usuarios = carregar_json(ARQUIVO_USUARIOS)
            if email_cliente in usuarios:
                usuarios[email_cliente]["plano"] = plano
                usuarios[email_cliente]["status_pagamento"] = "aprovado"
                usuarios[email_cliente]["plano_ativo"] = True
                salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.success(f"✅ Plano {plano} ativado! Bem-vindo!")
            st.balloons()
            del st.session_state["plano_escolhido"]
            st.session_state.usuario = carregar_dados_usuario(email_cliente, plano)
            st.rerun()
        else:
            id_pag = gerar_id_pagamento()
            codigo_pix, chave_pix = gerar_codigo_pix(valor, f"Plano {plano} - {email_cliente}", email_cliente)
            url_qr = gerar_link_qr_pix(codigo_pix)
            
            st.markdown(f"""
            <div style='background:rgba(30,41,59,0.9);border:2px solid #22c55e;border-radius:16px;padding:24px;text-align:center;margin:20px 0;'>
            <h3 style='color:#22c55e;margin:0;'>💳 Pagamento via PIX — {plano}</h3>
            <p style='font-size:28px;font-weight:bold;color:white;margin:10px 0;'>R$ {valor:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"🔑 **Chave Pix:** `{chave_pix}`")
            st.info(f"👤 **Recebedor:** {CONFIG['pix_nome_recebedor']}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("### 📱 QR Code")
                st.image(url_qr, width=200)
            with col2:
                st.markdown("### 📋 Código Pix Copia e Cola")
                st.code(codigo_pix, language="text")
                st.info("1️⃣ Copie → 2️⃣ Cole no app do banco → 3️⃣ Pague")
            
            st.markdown("---")
            st.subheader("📤 Envie o comprovante para liberação")
            comprovante = st.file_uploader("Anexar comprovante de pagamento", type=["jpg", "jpeg", "png"])
            
            if comprovante:
                st.success(f"✅ Comprovante carregado: {comprovante.name}")
                st.image(comprovante, width=300)
                
                if st.button("✅ JÁ PAGUEI — SOLICITAR LIBERAÇÃO", type="primary", use_container_width=True):
                    registrar_pagamento_pendente(email_cliente, plano, valor, id_pag, comprovante.name)
                    link_whats = notificar_admin(email_cliente, plano, valor, id_pag, comprovante.name)
                    
                    st.success("🎉 Solicitação enviada! Aguardando aprovação!")
                    st.balloons()
                    
                    st.markdown(f"""
                    <div style='text-align:center;padding:20px;background:rgba(37,211,102,0.1);border-radius:12px;margin:20px 0;'>
                    <h4 style='color:#25d366;margin:0;'>📱 Avisar no WhatsApp</h4>
                    <a href="{link_whats}" target="_blank" style="display:inline-block;background:#25d366;color:white;padding:12px 24px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:16px;margin:10px 0;">💬 Enviar mensagem</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info(f"📧 Suporte: {CONFIG['email_suporte']}")
                    st.info("⏳ Assim que aprovado, seu plano será liberado!")
                    del st.session_state["plano_escolhido"]
                    st.stop()

# ==============================================
# 🔍 PREÇOS — CoinMarketCap (API CORRIGIDA) + CoinGecko + Binance
# ==============================================
@st.cache_data(ttl=60)
def buscar_precos_rodape():
    moedas = ["BTC", "ETH", "SOL", "XRP", "ADA"]
    precos = {}
    
    # Fonte 1: CoinMarketCap — usando a estrutura correta
    if CONFIG["coinmarketcap_api_key"]:
        try:
            headers = {"X-CMC_PRO_API_KEY": CONFIG["coinmarketcap_api_key"]}
            params = {"symbol": ",".join(moedas), "convert": "USD"}
            resp = requests.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
                timeout=10
            )
            dados = resp.json()
            if "data" in dados and isinstance(dados["data"], dict):
                for sigla in moedas:
                    if sigla in dados["data"]:
                        precos[sigla] = dados["data"][sigla]["quote"]["USD"]["price"]
                if len(precos) == 5:
                    return precos, "CoinMarketCap"
        except Exception as e:
            pass
    
    # Fonte 2: CoinGecko — reserva confiável
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,cardano&vs_currencies=usd"
        resp = requests.get(url, timeout=10)
        dados = resp.json()
        mapeamento = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple", "ADA": "cardano"}
        for sigla in moedas:
            gid = mapeamento[sigla]
            if gid in dados and "usd" in dados[gid]:
                precos[sigla] = dados[gid]["usd"]
        if len(precos) == 5:
            return precos, "CoinGecko"
    except:
        pass
    
    # Fonte 3: Binance — última reserva
    try:
        for sigla in moedas:
            resp = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sigla}USDT", timeout=8)
            dados = resp.json()
            if "price" in dados:
                precos[sigla] = float(dados["price"])
        if len(precos) == 5:
            return precos, "Binance"
    except:
        pass
    
    return precos, "Offline"

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
    except:
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
# 📡 RODAPÉ COM PREÇOS
# ==============================================
def exibir_rodape_precos():
    moedas_rodape = ["BTC", "ETH", "SOL", "XRP", "ADA"]
    precos, fonte = buscar_precos_rodape()
    
    st.markdown("<hr style='margin:0.3rem 0;opacity:0.2'>", unsafe_allow_html=True)
    cols = st.columns(5)
    for idx, sigla in enumerate(moedas_rodape):
        with cols[idx]:
            p = precos.get(sigla)
            if p:
                st.markdown(f"<div style='text-align:center;line-height:1.1;'><span style='font-size:13px;color:#94a3b8;'>{sigla}</span><br><span style='font-size:15px;font-weight:bold;color:#fff;'>${p:,.2f}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center;line-height:1.1;'><span style='font-size:13px;color:#94a3b8;'>{sigla}</span><br><span style='font-size:13px;color:#ef4444;'>—</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;font-size:11px;color:#64748b;padding:4px 0;'>Dados: {fonte} • Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} • Arbitragem AI © 2026</div>", unsafe_allow_html=True)

# ==============================================
# 🛠️ PAINEL DE ADMINISTRAÇÃO
# ==============================================
def painel_administracao():
    st.header("🛠️ PAINEL DE ADMINISTRAÇÃO")
    
    if "notificacoes" in st.session_state and st.session_state["notificacoes"]:
        st.subheader("🔔 Notificações Recentes")
        for notif in st.session_state["notificacoes"][:5]:
            icone = "🟢" if notif["lida"] else "🔴"
            st.info(f"{icone} {notif['hora']} — {notif['email']} | {notif['plano']} | R$ {notif['valor']:.2f}")
        st.markdown("---")
    
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    pendentes = {
        email: dados 
        for email, dados in usuarios.items()
        if dados.get("status_pagamento") == "pendente" and not dados.get("plano_ativo", False)
    }
    
    if pendentes:
        st.subheader(f"⏳ {len(pendentes)} Aguardando Aprovação")
        st.markdown("---")
        for email, dados in pendentes.items():
            with st.expander(f"📋 {email} — {dados.get('plano_escolhido', '—')}"):
                st.write(f"💰 Valor: R$ {dados.get('valor_pago', 0):.2f}")
                st.write(f"🆔 ID: {dados.get('id_pagamento', '—')}")
                st.write(f"📎 Comprovante: {dados.get('comprovante', '—')}")
                st.write(f"📅 Data: {dados.get('data_pagamento', '—')}")
                col_aprov, col_rej = st.columns(2)
                with col_aprov:
                    if st.button(f"✅ APROVAR E LIBERAR", key=f"apr_{email}", type="primary"):
                        usuarios[email]["status_pagamento"] = "aprovado"
                        usuarios[email]["plano_ativo"] = True
                        salvar_json(ARQUIVO_USUARIOS, usuarios)
                        st.success(f"✅ {email} — PLANO LIBERADO!")
                        st.balloons()
                        st.rerun()
                with col_rej:
                    if st.button(f"❌ REJEITAR", key=f"rej_{email}"):
                        usuarios[email]["status_pagamento"] = "rejeitado"
                        salvar_json(ARQUIVO_USUARIOS, usuarios)
                        st.warning(f"❌ {email} — Rejeitado!")
                        st.rerun()
    else:
        st.info("✅ Nenhum pagamento pendente no momento.")
    
    st.markdown("---")
    st.subheader("📊 Todos os Clientes")
    if not usuarios:
        st.info("Ainda não há clientes cadastrados.")
    else:
        for email, dados in usuarios.items():
            icone = {"aprovado":"✅", "pendente":"⏳", "rejeitado":"❌"}.get(dados.get("status_pagamento","aprovado"), "❓")
            plano_atual = dados.get("plano", "Gratuito")
            status = dados.get("status_pagamento", "aprovado")
            with st.expander(f"{icone} {email} | Plano: {plano_atual} | {status.upper()}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    novo_plano = st.selectbox(
                        "Alterar Plano", list(PLANOS.keys()),
                        index=list(PLANOS.keys()).index(plano_atual),
                        key=f"plano_{email}"
                    )
                    if st.button(f"🔄 Aplicar", key=f"apl_{email}"):
                        usuarios[email]["plano"] = novo_plano
                        if novo_plano == "Gratuito":
                            usuarios[email]["status_pagamento"] = "aprovado"
                            usuarios[email]["plano_ativo"] = True
                        salvar_json(ARQUIVO_USUARIOS, usuarios)
                        st.success(f"✅ Plano alterado para {novo_plano}!")
                        st.rerun()
                with col2:
                    st.write(f"📅 Cadastro: {dados.get('data_cadastro', '—')}")
                    st.write(f"🔑 Status: {status}")
                    st.write(f"⚡ Ativo: {'SIM' if dados.get('plano_ativo', False) else 'NÃO'}")
                with col3:
                    if st.button("🗑️ EXCLUIR", key=f"del_{email}"):
                        if f"conf_del_{email}" not in st.session_state:
                            st.session_state[f"conf_del_{email}"] = True
                            st.warning(f"⚠️ Clique NOVAMENTE para confirmar exclusão de {email}")
                        else:
                            del usuarios[email]
                            salvar_json(ARQUIVO_USUARIOS, usuarios)
                            st.success(f"🗑️ {email} — EXCLUÍDO!")
                            if f"conf_del_{email}" in st.session_state:
                                del st.session_state[f"conf_del_{email}"]
                            st.rerun()
    
    st.markdown("---")
    st.subheader("⚙️ Configurações do Sistema")
    novo_nome = st.text_input("Nome do recebedor do PIX", value=CONFIG["pix_nome_recebedor"])
    nova_chave = st.text_input("Chave PIX", value=CONFIG["pix_chave"])
    novo_email = st.text_input("E-mail de suporte", value=CONFIG["email_suporte"])
    nova_chave_cmc = st.text_input("API Key CoinMarketCap (opcional)", value=CONFIG["coinmarketcap_api_key"], type="password")
    
    if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary"):
        CONFIG["pix_nome_recebedor"] = novo_nome
        CONFIG["pix_chave"] = nova_chave
        CONFIG["email_suporte"] = novo_email
        CONFIG["coinmarketcap_api_key"] = nova_chave_cmc
        st.success("✅ Configurações salvas! Atualize a página para tudo funcionar!")

# ==============================================
# 🔐 FUNÇÕES DE LOGIN
# ==============================================
def verificar_login(email, senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False, "Email não encontrado!"
    if usuarios[email]["senha"] != senha:
        return False, "Senha incorreta!"
    return True, usuarios[email]

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

def carregar_dados_usuario(email, plano_padrao="Gratuito"):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    return usuarios.get(email, {
        "plano": plano_padrao,
        "status_pagamento": "aprovado",
        "plano_ativo": True,
        "chaves": {},
        "config": {"lucro_min": 0.3, "intervalo": 60}
    })

# ==============================================
# 🚀 INTERFACE PRINCIPAL
# ==============================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "admin" not in st.session_state:
    st.session_state.admin = False

st.title("🤖 Arbitragem AI")
st.warning(f"⚠️ Apenas análise. Não é recomendação de investimento. Suporte: {CONFIG['email_suporte']}")
st.markdown("---")

if st.session_state.admin:
    painel_administracao()
    if st.button("🚪 Sair do Admin", type="secondary"):
        st.session_state.admin = False
        st.rerun()
    exibir_rodape_precos()
    st.stop()

if not st.session_state.usuario:
    aba1, aba2, aba3, aba4 = st.tabs(["🔑 Entrar", "✨ Criar Conta", "🔓 Recuperar Senha", "🛠️ Admin"])
    
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
        if email_cad and senha_cad and "@" in email_cad and len(senha_cad) >= 4:
            exibir_escolha_planos(email_cad)
        else:
            st.info("👆 Preencha email e senha acima para escolher seu plano")
    
    with aba3:
        st.info("🔧 Recuperação: contate o suporte pelo WhatsApp ou e-mail.")
    
    with aba4:
        st.subheader("🛠️ Painel de Administração")
        senha_admin = st.text_input("Senha de Administrador", type="password", key="senha_admin")
        if st.button("🔓 ACESSAR PAINEL", type="primary", use_container_width=True):
            if senha_admin == SENHA_ADMIN:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    
    exibir_rodape_precos()

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
            "💳 Alterar Plano"
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
            st.info("🔍 Scanner em desenvolvimento...")
    
    elif pagina == "⏰ Histórico":
        st.info("⏰ Histórico em desenvolvimento...")
    
    elif pagina == "🔔 Alertas":
        st.info("🔔 Alertas em desenvolvimento...")
    
    elif pagina == "🧮 Calculadora de Lucro":
        st.info("🧮 Calculadora em desenvolvimento...")
    
    elif pagina == "📈 Resumo de Mercado":
        st.info("📈 Resumo em desenvolvimento...")
    
    elif pagina == "⚙️ Minhas Corretoras":
        st.header("⚙️ Minhas Corretoras")
        st.info("Integração com corretoras em desenvolvimento...")
    
    elif pagina == "🔧 Configurações":
        st.header("🔧 Configurações")
        st.info("Configurações em desenvolvimento...")
    
    elif pagina == "💳 Alterar Plano":
        st.header("💳 Alterar / Atualizar Plano")
        exibir_escolha_planos(user_email)
    
    exibir_rodape_precos()
