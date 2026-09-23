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
        "modo_avancado": False
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 50,
        "atualizacao_segundos": 60,
        "historico_horas": 72,
        "alertas_email": True,
        "alertas_whatsapp": True,
        "corretoras": ["Binance", "Bybit", "KuCoin", "OKX"],
        "modo_avancado": True
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 9999,
        "atualizacao_segundos": 15,
        "historico_horas": 168,
        "alertas_email": True,
        "alertas_whatsapp": True,
        "corretoras": ["Binance", "Bybit", "KuCoin", "OKX", "Gate.io", "Mercado Bitcoin"],
        "modo_avancado": True
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
        email = st.text_input("Seu E-mail", key="login_email")
        senha = st.text_input("Sua Senha", type="password", key="login_senha")
        if st.button("ENTRAR", type="primary"):
            if email in usuarios and usuarios[email].get("senha") == senha:
                if usuarios[email].get("plano_ativo", False) or usuarios[email].get("plano") == "Gratuito":
                    st.session_state["usuario"] = email
                    st.session_state["logado"] = True
                    st.rerun()
                else:
                    st.warning("Aguardando aprovacao do pagamento.")
            else:
                st.error("E-mail ou senha incorretos!")
    
    with aba_cadastrar:
        novo_email = st.text_input("Seu E-mail", key="cad_email")
        nova_senha = st.text_input("Criar Senha", type="password", key="cad_senha")
        confirma_senha = st.text_input("Repetir Senha", type="password", key="cad_confirma")
        if st.button("CRIAR CONTA", type="primary"):
            if novo_email in usuarios:
                st.error("E-mail ja cadastrado!")
            elif nova_senha != confirma_senha:
                st.error("Senhas nao coincidem!")
            elif len(nova_senha) < 4:
                st.error("Senha muito curta!")
            else:
                usuarios[novo_email] = {
                    "senha": nova_senha, "plano": "Gratuito", "plano_escolhido": "Gratuito",
                    "plano_ativo": True, "status_pagamento": "aprovado",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.session_state["usuario"] = novo_email
                st.session_state["logado"] = True
                st.success("Conta criada!")
                st.rerun()
    
    with aba_recuperar:
        email_recup = st.text_input("Seu E-mail", key="recup_email")
        if st.button("ENVIAR CODIGO", type="primary"):
            st.success("Codigo enviado (simulacao)!") if email_recup in usuarios else st.error("E-mail nao encontrado!")
    
    st.markdown("---")
    if st.button("PAINEL DE ADMINISTRACAO"):
        st.session_state["pagina"] = "Painel de Administracao"
        st.rerun()

# ==============================================
# TELA DE PLANOS
# ==============================================
def tela_planos():
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
    u = st.session_state["usuario"]
    plano = usuarios[u].get("plano_escolhido", "Pro")
    valor = PLANOS[plano]["preco"]
    st.header("Pagamento via PIX")
    st.subheader(f"Plano: {plano} — R$ {valor:.2f}")
    st.info(f"Recebedor: {CONFIG['pix_nome_recebedor']}\nChave PIX: `{CONFIG['pix_chave']}`\nValor: R$ {valor:.2f}")
    
    comprovante = st.file_uploader("Anexar Comprovante", type=["jpg", "jpeg", "png"])
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
        st.markdown(f"[Avisar no WhatsApp]({link_whats})")
    if st.button("Voltar aos Planos"):
        st.session_state["pagina"] = "Planos"
        st.rerun()

# ==============================================
# PAINEL PRINCIPAL DO USUARIO
# ==============================================
def painel_principal():
    exibir_logo_sidebar()
    u = st.session_state["usuario"]
    plano = usuarios[u].get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    st.sidebar.write(f"Usuario: {u}")
    st.sidebar.write(f"Plano: {plano}")
    pagina = st.sidebar.radio("Navegacao", [
        "Painel Principal", "Scanner de Arbitragem", "Historico de Oportunidades",
        "Calculadora de Lucro Real", "Alterar Plano", "Sair"
    ])
    
    if pagina == "Sair":
        st.session_state.clear()
        st.rerun()
    
    elif pagina == "Painel Principal":
        st.header("Bem-vindo(a) ao Arbitragem AI")
        st.success(f"✅ Plano {plano} ativo!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Corretoras", len(dados_plano["corretoras"]))
        col2.metric("Moedas", dados_plano["moedas"] if dados_plano["moedas"] < 100 else "Ilimitadas")
        col3.metric("Atualizacao", f"{dados_plano['atualizacao_segundos']}s")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("BTC", "$ 63.420,50", "+0,32%")
        c2.metric("ETH", "$ 3.218,90", "-0,15%")
        c3.metric("SOL", "$ 142,85", "+1,05%")
        st.info("👉 Va em **Scanner de Arbitragem** para ver oportunidades!")
    
    elif pagina == "Scanner de Arbitragem":
        st.header("🔍 Scanner Inteligente")
        lucro_min_perc = st.slider("Lucro Minimo Liquido (%)", 0.1, 5.0, 0.5, 0.1)
        auto_refresh = st.checkbox("Atualizacao Automatica")
        corretoras = dados_plano["corretoras"]
        if dados_plano.get("modo_avancado"):
            corretoras = st.multiselect("Corretoras", CORRETORAS_DISPONIVEIS, default=corretoras)
        moedas = MOEDAS_MONITORADAS[:dados_plano["moedas"]] if dados_plano["moedas"] < 100 else MOEDAS_MONITORADAS
        st.info(f"Comparando: {', '.join(corretoras)} | {len(moedas)} moedas")
        
        if st.button("🔄 ESCANEAR AGORA", type="primary") or auto_refresh:
            with st.spinner("Analisando..."):
                oportunidades = escanear_oportunidades(corretoras, moedas, lucro_min_perc)
            if not oportunidades:
                st.info("Nenhuma oportunidade encontrada.")
            else:
                st.subheader(f"✅ {len(oportunidades)} oportunidade(s)")
                st.warning("⚠️ Confirme os precos na corretora antes de operar!")
                for op in oportunidades[:10]:
                    with st.expander(f"💰 {op['moeda']} — {op['lucro_liquido_perc']:.2f}% LÍQUIDO"):
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown(f"✅ Comprar em: **{op['comprar_em']}**")
                            st.write(f"$ {op['preco_compra']:.4f}")
                            st.info(op['liquidez_compra']['alerta'] or "✅ Liquidez ok")
                        with cb:
                            st.markdown(f"📤 Vender em: **{op['vender_em']}**")
                            st.write(f"$ {op['preco_venda']:.4f}")
                            st.info(op['liquidez_venda']['alerta'] or "✅ Liquidez ok")
                        l1, l2, l3 = st.columns(3)
                        l1.metric("Lucro Bruto", f"{op['lucro_bruto_perc']:.2f}%")
                        l2.metric("✅ Lucro Liquido", f"{op['lucro_liquido_perc']:.2f}%")
                        l3.metric("Em $1.000", f"$ {(1000*op['lucro_liquido_perc']/100):.2f}")
            if auto_refresh:
                time.sleep(dados_plano["atualizacao_segundos"])
                st.rerun()
    
    elif pagina == "Historico de Oportunidades":
        st.header("📈 Historico")
        hist = carregar_json(ARQUIVO_HISTORICO, [])
        if not hist:
            st.info("Nenhum registro ainda.")
        else:
            st.info(f"Total: {len(hist)} oportunidades")
            for op in hist[:50]:
                st.write(f"{op.get('hora')} | {op['moeda']} | {op['comprar_em']}→{op['vender_em']} | {op['lucro_liquido_perc']:.2f}%")
    
    elif pagina == "Calculadora de Lucro Real":
        st.header("🧮 Calculadora com Taxas")
        c1, c2 = st.columns(2)
        with c1:
            pc = st.number_input("Preco Compra ($)", 0.0, 100000.0, 100.0)
            pv = st.number_input("Preco Venda ($)", 0.0, 100000.0, 102.0)
            valor_inv = st.number_input("Valor Investido ($)", 0.0, 100000.0, 1000.0)
            taxa = st.number_input("Taxa Corretora (%)", 0.0, 5.0, CONFIG["taxa_media_corretora_perc"])
        with c2:
            calc = calcular_lucro_liquido(pc, pv, taxa)
            qtd = valor_inv / pc if pc > 0 else 0
            st.metric("Quantidade", f"{qtd:.4f}")
            st.metric("Lucro BRUTO", f"{calc['lucro_bruto_perc']:.2f}%")
            st.metric("✅ Lucro LIQUIDO", f"{calc['lucro_liquido_perc']:.2f}%")
            if calc['lucro_liquido_perc'] <= 0:
                st.error("❌ Nao da lucro apos taxas!")
            elif calc['lucro_liquido_perc'] < 0.3:
                st.warning("⚠️ Lucro pequeno — risco de variacao")
            else:
                st.success("✅ Margem segura!")
    
    elif pagina == "Alterar Plano":
        tela_planos()

# ==============================================
# PAINEL DE ADMINISTRACAO
# ==============================================
def painel_administracao():
    exibir_logo_sidebar()
    if st.session_state.get("admin_logado") != True:
        if st.text_input("Senha Admin", type="password") == CONFIG["senha_admin"]:
            st.session_state["admin_logado"] = True
            st.rerun()
        else:
            st.stop()
    
    st.header("PAINEL DE ADMINISTRACAO")
    aba1, aba2, aba3 = st.tabs(["Pagamentos", "Sistema", "E-mail"])
    
    with aba1:
        usrs = carregar_json(ARQUIVO_USUARIOS, {})
        pendentes = {e: d for e, d in usrs.items() if d.get("status_pagamento") == "pendente"}
        if pendentes:
            st.subheader(f"{len(pendentes)} pendentes")
            for email, d in pendentes.items():
                with st.expander(f"{email} | {d.get('plano_escolhido')}"):
                    st.write(f"Valor: R$ {d.get('valor_pago',0):.2f}")
                    img = d.get("caminho_comprovante", "")
                    if img and os.path.exists(img):
                        st.image(img, width=400)
                    ap, re = st.columns(2)
                    with ap:
                        if st.button(f"APROVAR", key=f"apr_{email}", type="primary"):
                            usrs[email].update({"status_pagamento": "aprovado", "plano": d.get("plano_escolhido"), "plano_ativo": True})
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.success("Aprovado!")
                            st.rerun()
                    with re:
                        if st.button(f"REJEITAR", key=f"rej_{email}"):
                            usrs[email]["status_pagamento"] = "rejeitado"
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.rerun()
        else:
            st.info("Nenhum pendente.")
    
    with aba2:
        st.subheader("Configuracoes do Sistema")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        pix_nome = st.text_input("Nome Recebedor PIX", value=dados_sis.get("pix_nome_recebedor", CONFIG["pix_nome_recebedor"]))
        pix_chave = st.text_input("Chave PIX", value=dados_sis.get("pix_chave", CONFIG["pix_chave"]))
        whatsapp = st.text_input("WhatsApp Admin", value=dados_sis.get("whatsapp_admin", CONFIG["whatsapp_admin"]))
        taxa_media = st.number_input("Taxa Media Corretoras (%)", 0.0, 5.0, dados_sis.get("taxa_media_corretora_perc", CONFIG["taxa_media_corretora_perc"]), step=0.01)
        if st.button("SALVAR CONFIGURACOES", type="primary"):
            CONFIG.update({"pix_nome_recebedor": pix_nome, "pix_chave": pix_chave, "whatsapp_admin": whatsapp, "taxa_media_corretora_perc": taxa_media})
            salvar_json(ARQUIVO_SISTEMA, CONFIG)
            st.success("Salvo!")
    
    with aba3:
        st.subheader("E-mail")
        dados_sis = carregar_json(ARQUIVO_SISTEMA, {})
        remetente = st.text_input("E-mail Remetente", value=dados_sis.get("email_remetente", ""))
        senha_app = st.text_input("Senha de App", value=dados_sis.get("senha_app_email", ""), type="password")
        if st.button("SALVAR E-MAIL", type="primary"):
            salvar_json(ARQUIVO_SISTEMA, {"email_remetente": remetente, "senha_app_email": senha_app})
            st.success("Salvo!")
    
    if st.sidebar.button("SAIR"):
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
