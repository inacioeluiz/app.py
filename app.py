import streamlit as st
import json
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import quote

# ==============================================
# ⚙️ CONFIGURAÇÕES — COLOQUE SEUS DADOS AQUI!
# ==============================================
st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

CONFIG = {
    "pix_nome_recebedor": "Inacio Silva",
    "pix_chave": "11571293744",
    "whatsapp_admin": "5521997524939",
    "email_suporte": "suportearbitrageai@gmail.com"
}

SENHA_ADMIN = "1911Gilson@"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_LEMBRAR = "lembrar_me.json"
PASTA_COMPROVANTES = "comprovantes"
ARQUIVO_HISTORICO = "historico_alertas.json"

os.makedirs(PASTA_COMPROVANTES, exist_ok=True)

# ==============================================
# 🔒 PERMISSÕES POR PLANO
# ==============================================
PLANOS = {
    "Gratuito": {
        "preco": 0.00,
        "moedas": 3,
        "intervalo": 120,
        "suporte": "Básico",
        "descricao": "Ideal para começar",
        "recursos": {
            "painel_principal": True,
            "scanner_basico": True,
            "scanner_avancado": False,
            "historico_24h": False,
            "alertas_quantidade": 1,
            "alertas_email": False,
            "calculadora_lucro": True,
            "resumo_mercado": True,
            "corretoras_integracao": False,
            "configuracoes": False,
            "relatorios": False,
            "multiplas_corretoras": 2,
            "atualizacao_segundos": 120,
            "suporte_prioritario": False
        }
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 50,
        "intervalo": 60,
        "suporte": "Prioritário",
        "descricao": "Para quem quer crescer",
        "recursos": {
            "painel_principal": True,
            "scanner_basico": True,
            "scanner_avancado": True,
            "historico_24h": True,
            "alertas_quantidade": 10,
            "alertas_email": True,
            "calculadora_lucro": True,
            "resumo_mercado": True,
            "corretoras_integracao": True,
            "configuracoes": True,
            "relatorios": False,
            "multiplas_corretoras": 5,
            "atualizacao_segundos": 60,
            "suporte_prioritario": True
        }
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 999,
        "intervalo": 15,
        "suporte": "VIP 24/7",
        "descricao": "Máxima velocidade",
        "recursos": {
            "painel_principal": True,
            "scanner_basico": True,
            "scanner_avancado": True,
            "historico_24h": True,
            "alertas_quantidade": 999,
            "alertas_email": True,
            "calculadora_lucro": True,
            "resumo_mercado": True,
            "corretoras_integracao": True,
            "configuracoes": True,
            "relatorios": True,
            "multiplas_corretoras": 5,
            "atualizacao_segundos": 15,
            "suporte_prioritario": True
        }
    }
}

CORRETORAS = {
    "Binance": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Bybit": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "KuCoin": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "Gate.io": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1},
    "OKX": {"ativa": True, "taxa_compra": 0.1, "taxa_venda": 0.1}
}

LISTA_MOEDAS_COMPLETA = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "MATIC", "DOT", "LINK", "ATOM", "NEAR", "FIL", "UNI", "AAVE"]

# ==============================================
# 📂 FUNÇÕES AUXILIARES
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

def salvar_comprovante(arquivo_upload, id_pagamento):
    extensao = arquivo_upload.name.split(".")[-1].lower()
    nome_arquivo = f"{id_pagamento}.{extensao}"
    caminho = os.path.join(PASTA_COMPROVANTES, nome_arquivo)
    with open(caminho, "wb") as f:
        f.write(arquivo_upload.getbuffer())
    return caminho

def gerar_id_pagamento():
    return f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"

def verificar_permissao(recurso):
    if "usuario" not in st.session_state or not st.session_state.usuario:
        return False
    plano = st.session_state.usuario.get("plano", "Gratuito")
    return PLANOS[plano]["recursos"].get(recurso, False)

def limite_moedas_usuario():
    if "usuario" not in st.session_state or not st.session_state.usuario:
        return 3
    plano = st.session_state.usuario.get("plano", "Gratuito")
    return PLANOS[plano]["moedas"]

def intervalo_atualizacao_usuario():
    if "usuario" not in st.session_state or not st.session_state.usuario:
        return 120
    plano = st.session_state.usuario.get("plano", "Gratuito")
    return PLANOS[plano]["intervalo"]

def bloqueio_acesso(mensagem="🔒 Recurso disponível apenas nos planos Pro e Premium"):
    st.markdown(f"""
    <div style='background:rgba(239,68,68,0.1);border:1px solid #ef4444;border-radius:12px;padding:30px;text-align:center;'>
    <h3 style='color:#ef4444;margin:0;'>🔒 ACESSO RESTRITO</h3>
    <p style='color:#94a3b8;margin:15px 0;'>{mensagem}</p>
    </div>
    """, unsafe_allow_html=True)
    return False

# ==============================================
# 💳 PIX E PAGAMENTOS
# ==============================================
def gerar_codigo_pix(valor, descricao, email):
    chave = CONFIG["pix_chave"]
    nome = CONFIG["pix_nome_recebedor"]
    return f"00020126580014br.gov.bcb.pix0136{chave}5204000053039865802BR59{len(nome):02d}{nome}6008BRASILIA62070503***64330015{email}0103{descricao}6502BR7301{valor:.2f}".replace(".", ""), chave

def gerar_link_qr_pix(codigo_pix):
    return f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(codigo_pix)}"

def registrar_pagamento_pendente(email, plano, valor, id_pag, caminho_imagem=""):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False
    usuarios[email]["plano_escolhido"] = plano
    usuarios[email]["valor_pago"] = valor
    usuarios[email]["id_pagamento"] = id_pag
    usuarios[email]["caminho_comprovante"] = caminho_imagem
    usuarios[email]["status_pagamento"] = "pendente"
    usuarios[email]["data_pagamento"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def notificar_admin(email, plano, valor, id_pag, caminho_imagem=""):
    texto = f"""🔔 NOVO PAGAMENTO PENDENTE!

👤 Cliente: {email}
💳 Plano: {plano}
💰 Valor: R$ {valor:.2f}
🆔 ID: {id_pag}
📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

📎 Comprovante: {'✅ Salvo no sistema' if caminho_imagem else '⚠️ Sem imagem'}

Acesse o PAINEL DE ADMINISTRAÇÃO para verificar e aprovar! ✅"""
    
    link_whats = f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"
    
    if "notificacoes" not in st.session_state:
        st.session_state["notificacoes"] = []
    st.session_state["notificacoes"].insert(0, {
        "tipo": "pagamento_pendente",
        "email": email,
        "plano": plano,
        "valor": valor,
        "id": id_pag,
        "caminho_imagem": caminho_imagem,
        "hora": datetime.now().strftime("%d/%m %H:%M"),
        "lida": False
    })
    return link_whats

def exibir_escolha_planos(email_cliente):
    st.markdown("## 💳 Escolha seu Plano")
    st.markdown("---")
    
    st.markdown("### 📋 Comparativo de Planos")
    st.markdown("""
    | Recurso | Gratuito 🆓 | Pro 🚀 | Premium 👑 |
    |---|---|---|---|
    | Scanner de arbitragem | ✅ Básico | ✅ Completo | ✅ Completo |
    | Moedas monitoradas | 3 | 50 | Ilimitado |
    | Atualização | 2 min | 1 min | 15 seg |
    | Histórico de oportunidades | ❌ | ✅ 24h | ✅ Completo |
    | Alertas ativos | 1 | 10 | Ilimitado |
    | Alertas por e-mail | ❌ | ✅ | ✅ |
    | Integração corretoras | ❌ | ✅ | ✅ |
    | Calculadora de lucro | ✅ | ✅ | ✅ |
    | Relatórios | ❌ | ❌ | ✅ |
    | Suporte | Básico | Prioritário | VIP 24/7 |
    | Preço | Grátis | R$ 49,90/mês | R$ 99,90/mês |
    """)
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
                    {'Grátis' if dados['preco'] == 0 else f"R$ {dados['preco']:.2f}<small style='font-size:12px'>/mês</small>"}
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
            st.session_state.usuario["email"] = email_cliente
            st.rerun()
        else:
            id_pag = gerar_id_pagamento()
            codigo_pix, chave_pix = gerar_codigo_pix(valor, f"Plano {plano} - {email_cliente}", email_cliente)
            url_qr = gerar_link_qr_pix(codigo_pix)
            
            st.markdown(f"""
            <div style='background:rgba(30,41,59,0.9);border:2px solid #22c55e;border-radius:16px;padding:24px;text-align:center;margin:20px 0;'>
            <h3 style='color:#22c55e;margin:0;'>💳 Pagamento via PIX — {plano}</h3>
            <p style='font-size:28px;font-weight:bold;color:white;margin:10px 0;'>R$ {valor:.2f}/mês</p>
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
            comprovante = st.file_uploader("📎 Anexar comprovante de pagamento", type=["jpg", "jpeg", "png"])
            
            if comprovante:
                st.success(f"✅ Comprovante carregado: {comprovante.name}")
                st.image(comprovante, width=350, caption="Pré-visualização")
                
                if st.button("✅ JÁ PAGUEI — ENVIAR COMPROVANTE", type="primary", use_container_width=True):
                    caminho_imagem = salvar_comprovante(comprovante, id_pag)
                    registrar_pagamento_pendente(email_cliente, plano, valor, id_pag, caminho_imagem)
                    link_whats = notificar_admin(email_cliente, plano, valor, id_pag, caminho_imagem)
                    
                    st.success("🎉 Enviado! Aguardando aprovação!")
                    st.balloons()
                    
                    st.markdown(f"""
                    <div style='text-align:center;padding:20px;background:rgba(37,211,102,0.1);border-radius:12px;margin:20px 0;'>
                    <h4 style='color:#25d366;margin:0;'>📱 Avisar no WhatsApp</h4>
                    <a href="{link_whats}" target="_blank" style="display:inline-block;background:#25d366;color:white;padding:12px 24px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:16px;">💬 Clique aqui</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info(f"📧 Suporte: {CONFIG['email_suporte']}")
                    st.info("⏳ Assim que aprovado, o plano é liberado na hora!")
                    del st.session_state["plano_escolhido"]
                    st.stop()

# ==============================================
# 🔍 PREÇOS E SCANNER
# ==============================================
@st.cache_data(ttl=60)
def buscar_precos_rodape():
    moedas = ["BTC", "ETH", "SOL", "XRP", "ADA"]
    precos = {}
    
    chave_cmc = CONFIG.get("coinmarketcap_api_key", "")
    if chave_cmc and chave_cmc.strip():
        try:
            headers = {"X-CMC_PRO_API_KEY": chave_cmc.strip()}
            params = {"symbol": ",".join(moedas), "convert": "USD"}
            resp = requests.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                headers=headers, params=params, timeout=10
            )
            dados = resp.json()
            if "data" in dados and isinstance(dados["data"], dict):
                for sigla in moedas:
                    if sigla in dados["data"]:
                        precos[sigla] = dados["data"][sigla]["quote"]["USD"]["price"]
                if len(precos) == 5:
                    return precos, "CoinMarketCap"
        except:
            pass
    
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

def escanear_oportunidades(lista_moedas, min_lucro=0.05):
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
            if spread_pct >= min_lucro:
                oportunidades.append({
                    "moeda": moeda,
                    "comprar_bolsa": mais_barata[0],
                    "comprar_preco": mais_barata[1],
                    "vender_bolsa": mais_cara[0],
                    "vender_preco": mais_cara[1],
                    "lucro_pct": round(spread_pct, 2),
                    "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                })
    return sorted(oportunidades, key=lambda x: x["lucro_pct"], reverse=True)

def salvar_no_historico(oportunidades):
    historico = carregar_json(ARQUIVO_HISTORICO)
    for op in oportunidades:
        historico[f"{op['moeda']}_{op['horario']}"] = op
    if len(historico) > 1000:
        chaves = sorted(historico.keys(), reverse=True)[:1000]
        historico = {k: historico[k] for k in chaves}
    salvar_json(ARQUIVO_HISTORICO, historico)

# ==============================================
# 📡 RODAPÉ
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
# FUNÇÃO DE ENVIO DE E-MAIL
# ==============================================
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email(destinatario, assunto, mensagem_html):
    try:
        remetente = CONFIG.get("email_remetente", "")
        senha = CONFIG.get("senha_app_email", "")
        servidor_smtp = CONFIG.get("smtp_servidor", "smtp.gmail.com")
        porta = CONFIG.get("smtp_porta", 587)
        
        if not remetente or not senha:
            return False, "Configurações de e-mail incompletas"
        
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
# 🛠️ PAINEL DE ADMINISTRAÇÃO
# ==============================================
    elif pagina == "🛠️ Painel de Administração":
        if st.session_state.get("admin_logado") != True:
            senha_admin = st.text_input("🔐 Senha de Administrador", type="password")
            if st.button("🔑 ENTRAR", type="primary"):
                if senha_admin == "admin123":
                    st.session_state["admin_logado"] = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
            st.stop()
        
        st.header("🛠️ PAINEL DE ADMINISTRAÇÃO")
        st.markdown("---")
        
        # 📬 ABA DE CONFIGURAÇÕES
        aba_admin1, aba_admin2, aba_admin3 = st.tabs(["📋 Pagamentos", "⚙️ Sistema", "📧 E-mail"])
        
        with aba_admin1:
            st.subheader("🔔 Pagamentos Pendentes")
            if "notificacoes" in st.session_state and st.session_state["notificacoes"]:
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
                st.subheader(f"⏳ {len(pendentes)} Aguardando VERIFICAÇÃO")
                st.markdown("---")
                for email, dados in pendentes.items():
                    with st.expander(f"📋 {email} — {dados.get('plano_escolhido', '—')}"):
                        st.write(f"💰 Valor: R$ {dados.get('valor_pago', 0):.2f}")
                        st.write(f"🆔 ID Pagamento: {dados.get('id_pagamento', '—')}")
                        st.write(f"📅 Data: {dados.get('data_pagamento', '—')}")
                        
                        caminho_img = dados.get("caminho_comprovante", "")
                        if caminho_img and os.path.exists(caminho_img):
                            st.markdown("### 📎 COMPROVANTE ENVIADO:")
                            st.image(caminho_img, caption=f"Comprovante — {email}", width=400)
                            st.success("✅ Imagem carregada — Verifique a originalidade!")
                        else:
                            st.warning("⚠️ Nenhuma imagem anexada!")
                        
                        col_aprov, col_rej = st.columns(2)
                        with col_aprov:
                            if st.button(f"✅ APROVAR E LIBERAR", key=f"apr_{email}", type="primary"):
                                usuarios[email]["status_pagamento"] = "aprovado"
                                usuarios[email]["plano_ativo"] = True
                                salvar_json(ARQUIVO_USUARIOS, usuarios)
                                
                                # ✅ ENVIAR E-MAIL PARA O CLIENTE
                                if CONFIG.get("email_remetente") and CONFIG.get("senha_app_email"):
                                    assunto = "✅ Pagamento APROVADO — Acesso Liberado!"
                                    html = f"""
                                    <html>
                                    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0;padding:20px;background:#f9fafb;">
                                    <div style="background:white;border-radius:12px;padding:25px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                    <h2 style="color:#22c55e;margin-top:0;">✅ Seu plano foi liberado!</h2>
                                    <p>Olá, <strong>{email}</strong>,</p>
                                    <p>Seu pagamento foi confirmado e o plano <strong>{dados.get('plano_escolhido', '—')}</strong> está ativo!</p>
                                    <p>Acesse o aplicativo e comece a usar agora mesmo.</p>
                                    <p style="color:#999;font-size:12px;margin-top:30px;">Arbitragem AI © 2026</p>
                                    </div>
                                    </body>
                                    </html>
                                    """
                                    enviado, _ = enviar_email(email, assunto, html)
                                    if enviado:
                                        st.info("📧 E-mail enviado ao cliente!")
                                
                                st.success(f"✅ {email} — PLANO LIBERADO!")
                                st.balloons()
                                st.rerun()
                        with col_rej:
                            if st.button(f"❌ REJEITAR", key=f"rej_{email}"):
                                usuarios[email]["status_pagamento"] = "rejeitado"
                                salvar_json(ARQUIVO_USUARIOS, usuarios)
                                st.warning(f"❌ {email} — REJEITADO!")
                                st.rerun()
            else:
                st.info("✅ Nenhum pagamento pendente.")
            
            st.markdown("---")
            st.subheader("📊 Todos os Clientes")
            if not usuarios:
                st.info("Ainda não há clientes.")
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
                            if dados.get("caminho_comprovante") and os.path.exists(dados.get("caminho_comprovante")):
                                st.image(dados.get("caminho_comprovante"), width=200, caption="Comprovante")
                        with col3:
                            if st.button("🗑️ EXCLUIR", key=f"del_{email}"):
                                if f"conf_del_{email}" not in st.session_state:
                                    st.session_state[f"conf_del_{email}"] = True
                                    st.warning(f"⚠️ Clique NOVAMENTE para excluir {email}")
                                else:
                                    if dados.get("caminho_comprovante") and os.path.exists(dados.get("caminho_comprovante")):
                                        os.remove(dados.get("caminho_comprovante"))
                                    del usuarios[email]
                                    salvar_json(ARQUIVO_USUARIOS, usuarios)
                                    st.success(f"🗑️ {email} — EXCLUÍDO!")
                                    if f"conf_del_{email}" in st.session_state:
                                        del st.session_state[f"conf_del_{email}"]
                                    st.rerun()
        
        with aba_admin2:
            st.subheader("💰 Dados do Sistema")
            novo_nome = st.text_input("Nome do recebedor do PIX", value=CONFIG["pix_nome_recebedor"])
            nova_chave = st.text_input("Chave PIX", value=CONFIG["pix_chave"])
            novo_email_sup = st.text_input("E-mail de suporte", value=CONFIG["email_suporte"])
            nova_chave_cmc = st.text_input("API Key CoinMarketCap (opcional)", value=CONFIG.get("coinmarketcap_api_key", ""), type="password")
            novo_whatsapp = st.text_input("WhatsApp do Administrador", value=CONFIG["whatsapp_admin"])
            
            if st.button("💾 SALVAR DADOS DO SISTEMA", type="primary"):
                CONFIG["pix_nome_recebedor"] = novo_nome
                CONFIG["pix_chave"] = nova_chave
                CONFIG["email_suporte"] = novo_email_sup
                CONFIG["coinmarketcap_api_key"] = nova_chave_cmc
                CONFIG["whatsapp_admin"] = novo_whatsapp
                st.success("✅ Dados salvos! Atualize a página.")
        
        with aba_admin3:
            st.subheader("📧 Configurações de E-mail")
            st.info("Preencha abaixo para receber notificações e avisar os clientes por e-mail.")
            
            email_rem = st.text_input("E-mail Remetente", value=CONFIG.get("email_remetente", ""))
            senha_app = st.text_input("Senha de Aplicativo", value=CONFIG.get("senha_app_email", ""), type="password",
                                      help="Não é a senha normal! Para Gmail: ative verificação em 2 etapas → gere 'Senha de App'")
            smtp_serv = st.text_input("Servidor SMTP", value=CONFIG.get("smtp_servidor", "smtp.gmail.com"))
            smtp_port = st.number_input("Porta SMTP", value=CONFIG.get("smtp_porta", 587))
            
            if st.button("💾 SALVAR CONFIGURAÇÕES DE E-MAIL", type="primary"):
                CONFIG["email_remetente"] = email_rem
                CONFIG["senha_app_email"] = senha_app
                CONFIG["smtp_servidor"] = smtp_serv
                CONFIG["smtp_porta"] = int(smtp_port)
                st.success("✅ Configurações de e-mail salvas!")
            
            st.markdown("---")
            st.subheader("🧪 Testar Envio")
            email_teste = st.text_input("E-mail para teste", placeholder="seuemail@exemplo.com")
            if st.button("📤 ENVIAR E-MAIL DE TESTE"):
                if not CONFIG.get("email_remetente") or not CONFIG.get("senha_app_email"):
                    st.error("⚠️ Preencha e salve as configurações acima primeiro!")
                else:
                    assunto = "✅ Teste — Arbitragem AI"
                    html = """
                    <html>
                    <body style="font-family:Arial,sans-serif;padding:20px;">
                    <h2 style="color:#22c55e;">✅ Funcionou!</h2>
                    <p>O e-mail está configurado corretamente.</p>
                    <p>Arbitragem AI © 2026</p>
                    </body>
                    </html>
                    """
                    enviado, msg = enviar_email(email_teste, assunto, html)
                    if enviado:
                        st.success("✅ E-mail enviado com sucesso! Verifique a caixa de entrada.")
                    else:
                        st.error(f"❌ Erro: {msg}")
