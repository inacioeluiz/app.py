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
    
    st.markdown("---")
    st.subheader("⚙️ Configurações do Sistema")
    novo_nome = st.text_input("Nome do recebedor do PIX", value=CONFIG["pix_nome_recebedor"])
    nova_chave = st.text_input("Chave PIX", value=CONFIG["pix_chave"])
    novo_email = st.text_input("E-mail de suporte", value=CONFIG["email_suporte"])
    nova_chave_cmc = st.text_input("API Key CoinMarketCap (opcional)", value=CONFIG.get("coinmarketcap_api_key", ""), type="password")
    
    if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary"):
        CONFIG["pix_nome_recebedor"] = novo_nome
        CONFIG["pix_chave"] = nova_chave
        CONFIG["email_suporte"] = novo_email
        CONFIG["coinmarketcap_api_key"] = nova_chave_cmc
        st.success("✅ Salvo! Atualize a página!")

# ==============================================
# 🔐 AUTENTICAÇÃO
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
        "config": {"lucro_min": 0.3, "intervalo": 60},
        "alertas": []
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
        "config": {"lucro_min": 0.3, "intervalo": 60},
        "alertas": []
    })

def salvar_lembrar_me(email, senha):
    salvar_json(ARQUIVO_LEMBRAR, {"email": email, "senha": senha, "lembrar": True})

def carregar_lembrar_me():
    dados = carregar_json(ARQUIVO_LEMBRAR)
    if dados.get("lembrar", False):
        return dados.get("email", ""), dados.get("senha", "")
    return "", ""

def limpar_lembrar_me():
    if os.path.exists(ARQUIVO_LEMBRAR):
        os.remove(ARQUIVO_LEMBRAR)

# ==============================================
# 🚀 INTERFACE PRINCIPAL
# ==============================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "admin" not in st.session_state:
    st.session_state.admin = False

email_salvo, senha_salva = carregar_lembrar_me()
tem_dados_salvos = bool(email_salvo and senha_salva)

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
        email_login = st.text_input("Seu email", value=email_salvo, key="email_login")
        senha_login = st.text_input("Sua senha", value=senha_salva, type="password", key="senha_login")
        lembrar_me = st.checkbox("🔒 Lembrar meu login e senha", value=tem_dados_salvos, key="lembrar_me")
        
        if st.button("🔑 ENTRAR", type="primary", use_container_width=True):
            ok, resp = verificar_login(email_login, senha_login)
            if ok:
                st.session_state.usuario = resp
                st.session_state.usuario["email"] = email_login
                if lembrar_me:
                    salvar_lembrar_me(email_login, senha_login)
                else:
                    limpar_lembrar_me()
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
    perm = PLANOS[user_plano]["recursos"]
    
    if not ativo and user_plano != "Gratuito":
        with st.sidebar:
            st.markdown(f"""
            <div style='background:rgba(239,68,68,0.1);border-radius:12px;padding:12px;margin-bottom:20px;'>
            <p style='margin:0;'>👤 <strong>{user_email}</strong></p>
            <p style='margin:5px 0;'>💳 Plano: {user_plano}</p>
            <p style='margin:0;color:#f59e0b;'>⏳ Aguardando aprovação</p>
            </div>
            """, unsafe_allow_html=True)
            st.warning("Acesso restrito até aprovação.")
            st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
            if st.button("🚪 Sair da conta", type="secondary", use_container_width=True):
                if not carregar_json(ARQUIVO_LEMBRAR).get("lembrar", False):
                    limpar_lembrar_me()
                st.session_state.usuario = None
                st.rerun()
        st.title("🔐 Acesso Restrito")
        st.info("Seu pagamento está aguardando aprovação. Você receberá notificação quando for liberado.")
        st.info(f"📧 Contato: {CONFIG['email_suporte']}")
        exibir_rodape_precos()
        st.stop()
    
    with st.sidebar:
        st.markdown(f"""
        <div style='background:rgba(34,197,94,0.1);border-radius:12px;padding:12px;margin-bottom:20px;'>
        <p style='margin:0;'>👤 <strong>{user_email}</strong></p>
        <p style='margin:5px 0;'>💳 Plano: {user_plano}</p>
        <p style='margin:0;color:#22c55e;'>✅ ATIVO</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        pagina = st.radio("Menu", [
            "📊 Painel Principal", "🔍 Scanner de Arbitragem", "⏰ Histórico",
            "🔔 Alertas", "🧮 Calculadora de Lucro", "📈 Resumo de Mercado",
            "⚙️ Minhas Corretoras", "🔧 Configurações", "📑 Relatórios", "💳 Alterar Plano"
        ])
        st.markdown(f"<div style='font-size:12px;color:#94a3b8;'>⚙️ Moedas: {limite_moedas_usuario()}<br>🔄 Atualização: {intervalo_atualizacao_usuario()}s</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair da conta", type="secondary", use_container_width=True):
            if not carregar_json(ARQUIVO_LEMBRAR).get("lembrar", False):
                limpar_lembrar_me()
            st.session_state.usuario = None
            st.rerun()
    
    # 📊 PAINEL PRINCIPAL
    if pagina == "📊 Painel Principal":
        st.header("📊 Painel Principal")
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Plano Ativo", user_plano)
        with col2: st.metric("Moedas Monitoradas", limite_moedas_usuario())
        with col3: st.metric("Atualização", f"{intervalo_atualizacao_usuario()}s")
        with col4: st.metric("Status", "✅ Ativo")
        st.markdown("---")
        precos, _ = buscar_precos_rodape()
        if precos:
            cols = st.columns(5)
            for i, (m, p) in enumerate(precos.items()):
                with cols[i]: st.metric(m, f"${p:,.2f}")
        st.info("🔄 Acesse **Scanner de Arbitragem** para ver oportunidades em tempo real.")
        if user_plano == "Gratuito":
            st.warning("💡 Dica: Atualize para o plano **Pro** para monitorar mais moedas!")
    
    # 🔍 SCANNER
    elif pagina == "🔍 Scanner de Arbitragem":
        if not perm["scanner_basico"]:
            bloqueio_acesso()
        else:
            st.header("🔍 Scanner de Arbitragem")
            qtd = limite_moedas_usuario()
            moedas_disp = LISTA_MOEDAS_COMPLETA[:qtd]
            with st.expander("⚙️ Configurar"):
                moedas_sel = st.multiselect("Moedas", options=moedas_disp, default=moedas_disp[:min(5, qtd)])
                lucro_min = st.slider("Lucro mínimo (%)", 0.05, 5.0, 0.3, 0.05)
            if not moedas_sel:
                st.info("👆 Selecione moedas.")
            else:
                with st.spinner("Analisando..."):
                    oportunidades = escanear_oportunidades(moedas_sel, lucro_min)
                if perm["historico_24h"] and oportunidades:
                    salvar_no_historico(oportunidades)
                if oportunidades:
                    st.success(f"✅ {len(oportunidades)} oportunidade(s)!")
                    for op in oportunidades:
                        st.markdown(f"""
                        <div style='background:rgba(34,197,94,0.08);border-left:4px solid #22c55e;padding:15px;margin:10px 0;'>
                        <h4 style='margin:0;color:#22c55e;'>🪙 {op['moeda']} — {op['lucro_pct']}%</h4>
                        <p>Comprar: <strong>{op['comprar_bolsa']}</strong> ${op['comprar_preco']:.4f}<br>
                        Vender: <strong>{op['vender_bolsa']}</strong> ${op['vender_preco']:.4f}<br>
                        ⏰ {op['horario']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("⏳ Nenhuma oportunidade agora. Tente mais tarde.")
    
    # ⏰ HISTÓRICO
    elif pagina == "⏰ Histórico":
        if not perm["historico_24h"]:
            bloqueio_acesso("Histórico apenas Pro/Premium")
        else:
            st.header("⏰ Histórico de Oportunidades")
            hist = carregar_json(ARQUIVO_HISTORICO)
            if not hist:
                st.info("📋 Sem registro ainda.")
            else:
                limite = datetime.now() - timedelta(hours=24)
                recentes = []
                for op in hist.values():
                    try:
                        dt = datetime.strptime(op["horario"], "%d/%m/%Y %H:%M:%S")
                        if dt >= limite:
                            recentes.append(op)
                    except:
                        pass
                if not recentes:
                    st.info("📋 Nenhuma nos últimos 24h.")
                else:
                    st.success(f"📊 {len(recentes)} oportunidades nas últimas 24h")
                    for op in sorted(recentes, key=lambda x: x["horario"], reverse=True):
                        st.markdown(f"**{op['moeda']}** | {op['lucro_pct']}% | {op['horario']}")
    
    # 🔔 ALERTAS
    elif pagina == "🔔 Alertas":
        st.header("🔔 Alertas")
        max_alertas = perm["alertas_quantidade"]
        st.info(f"Você pode configurar até {max_alertas} alerta(s)")
        alertas = st.session_state.usuario.get("alertas", [])
        if len(alertas) >= max_alertas:
            st.warning("Limite de alertas atingido.")
        else:
            with st.form("novo_alerta"):
                moeda = st.selectbox("Moeda", LISTA_MOEDAS_COMPLETA[:limite_moedas_usuario()])
                lucro_alvo = st.number_input("Lucro alvo (%)", min_value=0.1, value=1.0, step=0.1)
                email_alerta = st.checkbox("Receber por e-mail", disabled=not perm["alertas_email"])
                if st.form_submit_button("🔔 Criar Alerta"):
                    alertas.append({"moeda": moeda, "lucro_alvo": lucro_alvo, "email": email_alerta, "ativa": True})
                    st.session_state.usuario["alertas"] = alertas
                    st.success(f"✅ Alerta criado!")
                    st.rerun()
        if alertas:
            st.subheader("Seus Alertas")
            for i, a in enumerate(alertas):
                st.markdown(f"{i+1}. {a['moeda']} → {a['lucro_alvo']}% | {'✅ Ativo' if a['ativa'] else '⏸️ Inativo'}")
    
    # 🧮 CALCULADORA
    elif pagina == "🧮 Calculadora de Lucro":
        st.header("🧮 Calculadora de Lucro")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            preco_compra = st.number_input("Preço de Compra (US$)", min_value=0.0, step=0.0001, format="%.4f")
            preco_venda = st.number_input("Preço de Venda (US$)", min_value=0.0, step=0.0001, format="%.4f")
            valor_investido = st.number_input("Valor Investido (US$)", min_value=0.0, step=1.0)
        
        with col2:
            st.info("📊 Resultado")
            if compra > 0 and preco_venda > 0 and valor_investido > 0:
                qtd_moedas = valor_investido / compra
                valor_venda = qtd_moedas * preco_venda
                lucro_bruto = valor_venda - valor_investido
                taxa_compra = CORRETORAS["Binance"]["taxa_compra"] / 100
                taxa_venda = CORRETORAS["Binance"]["taxa_venda"] / 100
                custos = (valor_investido * taxa_compra) + (valor_venda * taxa_venda)
                lucro_liquido = lucro_bruto - custos
                percentual = (lucro_liquido / valor_investido) * 100 if valor_investido > 0 else 0
                
                st.metric("Quantidade de Moedas", f"{qtd_moedas:.6f}")
                st.metric("Valor na Venda", f"US$ {valor_venda:.2f}")
                st.metric("Lucro Bruto", f"US$ {lucro_bruto:.2f}")
                st.metric("Taxas Estimadas", f"US$ {custos:.2f}")
                st.metric("💵 LUCRO LÍQUIDO", f"US$ {lucro_liquido:.2f}", f"{percentual:.2f}%")
            else:
                st.info("Preencha os valores à esquerda")

    # 📈 RESUMO DE MERCADO
    elif pagina == "📈 Resumo de Mercado":
        st.header("📈 Resumo de Mercado")
        st.markdown("---")
        precos, fonte = buscar_precos_rodape()
        if precos:
            for moeda, preco in precos.items():
                st.metric(f"{moeda} / USDT", f"${preco:,.4f}")
            st.info(f"Fonte: {fonte} • Atualizado automaticamente a cada 60 segundos")
        else:
            st.warning("Não foi possível carregar os preços. Tente novamente.")

    # ⚙️ MINHAS CORRETORAS
    elif pagina == "⚙️ Minhas Corretoras":
        if not perm["corretoras_integracao"]:
            bloqueio_acesso("Integração com corretoras disponível apenas nos planos Pro e Premium")
        else:
            st.header("⚙️ Minhas Corretoras")
            st.markdown("---")
            st.info("🔑 Insira suas chaves API de cada corretora para integração")
            
            chaves_usuario = st.session_state.usuario.get("chaves", {})
            
            for corretora in CORRETORAS.keys():
                with st.expander(f"🔌 {corretora}"):
                    api_key = st.text_input(f"API Key — {corretora}", 
                                           value=chaves_usuario.get(corretora, {}).get("api_key", ""), 
                                           type="password", key=f"api_{corretora}")
                    api_secret = st.text_input(f"API Secret — {corretora}", 
                                              value=chaves_usuario.get(corretora, {}).get("api_secret", ""), 
                                              type="password", key=f"secret_{corretora}")
                    
                    if st.button(f"💾 Salvar — {corretora}", key=f"save_{corretora}"):
                        if "chaves" not in st.session_state.usuario:
                            st.session_state.usuario["chaves"] = {}
                        st.session_state.usuario["chaves"][corretora] = {
                            "api_key": api_key,
                            "api_secret": api_secret
                        }
                        st.success(f"✅ {corretora} salva!")
                        st.rerun()

    # 🔧 CONFIGURAÇÕES
    elif pagina == "🔧 Configurações":
        if not perm["configuracoes"]:
            bloqueio_acesso("Configurações avançadas disponíveis apenas nos planos Pro e Premium")
        else:
            st.header("🔧 Configurações da Conta")
            st.markdown("---")
            
            config = st.session_state.usuario.get("config", {"lucro_min": 0.3, "intervalo": 60})
            
            novo_lucro = st.slider("Lucro mínimo padrão (%)", 0.05, 5.0, float(config.get("lucro_min", 0.3)), 0.05)
            novo_intervalo = st.slider("Intervalo de verificação (segundos)", 15, 300, int(config.get("intervalo", 60)), 15)
            
            st.markdown("---")
            st.subheader("🔐 Alterar Senha")
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.button("💾 SALVAR TUDO", type="primary", use_container_width=True):
                st.session_state.usuario["config"] = {
                    "lucro_min": novo_lucro,
                    "intervalo": novo_intervalo
                }
                if nova_senha:
                    if nova_senha != confirma_senha:
                        st.error("❌ Senhas não coincidem!")
                    else:
                        usuarios = carregar_json(ARQUIVO_USUARIOS)
                        if usuarios.get(user_email, {}).get("senha") == senha_atual:
                            usuarios[user_email]["senha"] = nova_senha
                            salvar_json(ARQUIVO_USUARIOS, usuarios)
                            st.success("✅ Senha alterada!")
                        else:
                            st.error("❌ Senha atual incorreta!")
                else:
                    st.success("✅ Configurações salvas!")
                st.rerun()

    # 📑 RELATÓRIOS
    elif pagina == "📑 Relatórios":
        if not perm["relatorios"]:
            bloqueio_acesso("Relatórios detalhados disponíveis apenas no plano Premium")
        else:
            st.header("📑 Relatórios")
            st.markdown("---")
            st.info("📊 Relatório completo de oportunidades detectadas")
            
            historico = carregar_json(ARQUIVO_HISTORICO)
            if historico:
                st.subheader("📈 Resumo Geral")
                total = len(historico)
                media_lucro = sum(op.get("lucro_pct", 0) for op in historico.values()) / total if total > 0 else 0
                max_lucro = max((op.get("lucro_pct", 0) for op in historico.values()), default=0)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Oportunidades", total)
                col2.metric("Média de Lucro", f"{media_lucro:.2f}%")
                col3.metric("Maior Lucro", f"{max_lucro:.2f}%")
                
                st.download_button(
                    "📥 Baixar Relatório Completo (CSV)",
                    data="moeda,comprar_em,vender_em,lucro_pct,horario\n" + 
                    "\n".join([f"{op['moeda']},{op['comprar_bolsa']},{op['vender_bolsa']},{op['lucro_pct']},{op['horario']}" 
                              for op in historico.values()]),
                    file_name=f"relatorio_arbitragem_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Ainda não há dados para gerar relatório.")

    # 💳 ALTERAR PLANO
    elif pagina == "💳 Alterar Plano":
        st.header("💳 Alterar Plano")
        st.markdown("---")
        st.info(f"Plano atual: **{user_plano}**")
        st.markdown("---")
        exibir_escolha_planos(user_email)

    exibir_rodape_precos()
