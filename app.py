import streamlit as st
import json
import os
import time
import uuid
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from urllib import request
from urllib.parse import quote

# ==============================================
# 🤖 ARBITRAGEM AI — VERSÃO COMPLETA FINAL
# ==============================================

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_PAGAMENTOS = "pagamentos.json"
ARQUIVO_COMPROVANTES = "comprovantes.json"
ARQUIVO_CODIGOS = "codigos_recuperacao.json"

# ====================== 🔑 CONFIGURAÇÕES ======================
ADMIN_EMAIL = "suportearbitrageai@gmail.com"
SEU_WHATSAPP = "5521997524939"

# ⚙️ CONFIGURAÇÕES DO EMAIL PARA RECUPERAÇÃO DE SENHA
EMAIL_REMETENTE = "suportearbitrageai@gmail.com"
SENHA_APP_EMAIL = "xafe zarg dwdg blam"  # Senha de App do Gmail
SMTP_SERVIDOR = "smtp.gmail.com"
SMTP_PORTA = 587

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

# ====================== 💾 GERENCIAMENTO DE DADOS ======================
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

# ====================== 🔐 FUNÇÕES DE RECUPERAÇÃO DE SENHA ======================
def gerar_codigo_recuperacao():
    return str(random.randint(100000, 999999))

def enviar_email_recuperacao(destinatario, codigo):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = destinatario
        msg["Subject"] = "🔐 Código de Recuperação de Senha — Arbitragem AI"
        
        corpo = f"""
        <html>
        <body style="font-family:Arial, sans-serif; max-width:600px; margin:0 auto; padding:20px;">
            <div style="background:#f8f9fa; border-radius:10px; padding:30px; text-align:center;">
                <h2 style="color:#6366f1;">🤖 Arbitragem AI</h2>
                <h3 style="color:#333;">Recuperação de Senha</h3>
                <p style="font-size:16px; color:#555;">Você solicitou a recuperação de sua senha.</p>
                <div style="background:#6366f1; color:white; font-size:32px; font-weight:bold; 
                     padding:15px 30px; border-radius:8px; margin:20px auto; display:inline-block; letter-spacing:5px;">
                    {codigo}
                </div>
                <p style="color:#666;">Este código expira em <strong>15 minutos</strong>.</p>
                <p style="color:#888; font-size:14px;">Se não foi você que solicitou, ignore este email.</p>
                <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
                <p style="color:#999; font-size:12px;">Suporte: {CONFIG['email_suporte']}</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(corpo, "html"))
        
        servidor = smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP_EMAIL)
        servidor.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        servidor.quit()
        return True, "✅ Código enviado para seu e-mail!"
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False, "❌ Erro ao enviar email. Tente novamente mais tarde."

def salvar_codigo_recuperacao(email, codigo):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    expira_em = datetime.now() + timedelta(minutes=15)
    codigos[email] = {
        "codigo": codigo,
        "expira_em": expira_em.strftime("%Y-%m-%d %H:%M:%S"),
        "usado": False
    }
    salvar_json(ARQUIVO_CODIGOS, codigos)

def verificar_codigo(email, codigo_digitado):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    if email not in codigos:
        return False, "❌ Nenhum código encontrado. Solicite novamente."
    
    dados = codigos[email]
    if dados["usado"]:
        return False, "❌ Este código já foi usado. Solicite um novo."
    
    expira_em = datetime.strptime(dados["expira_em"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expira_em:
        return False, "❌ Código expirado. Solicite um novo."
    
    if dados["codigo"] != codigo_digitado:
        return False, "❌ Código incorreto. Verifique seu e-mail."
    
    return True, "✅ Código confirmado! Crie sua nova senha."

def marcar_codigo_usado(email):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    if email in codigos:
        codigos[email]["usado"] = True
        salvar_json(ARQUIVO_CODIGOS, codigos)

def alterar_senha(email, nova_senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios:
        return False, "❌ Usuário não encontrado!"
    usuarios[email]["senha"] = nova_senha
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    marcar_codigo_usado(email)
    return True, "✅ Senha alterada com sucesso! Faça login."

# ====================== 📝 FUNÇÕES DE USUÁRIO ======================
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

def email_existe(email):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    return email in usuarios
# ====================== 💳 FUNÇÕES DE PAGAMENTO ======================
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
        "id": id_transacao, "email": email, "plano": plano, "valor": valor,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "comprovante_nome": comprovante_nome, "status": "pendente"
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

# ====================== 💳 PIX E WHATSAPP ======================
def gerar_codigo_pix(valor, descricao, devedor_email=""):
    chave = CONFIG["pix_chave"]
    nome = CONFIG["pix_nome_recebedor"]
    cidade = CONFIG["pix_cidade"]
    codigo_pix = f"00020126580014br.gov.bcb.pix0136{chave}0214{descricao[:14]}5204000053039865802BR5925{nome[:25]}6015{cidade[:15]}62070503***6304"
    return codigo_pix, chave

def gerar_link_whatsapp(email, plano, valor, id_transacao, comprovante_nome=""):
    mensagem = f"""📥 NOVO PAGAMENTO PARA APROVAR!

👤 Cliente: {email}
📋 Plano: {plano}
💰 Valor: R$ {valor:.2f}
🆔 ID Transação: {id_transacao}
📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
📎 Comprovante: {comprovante_nome if comprovante_nome else 'Anexado'}

✅ Por favor, verifique o comprovante e aprove o plano no painel de administração!

🤖 Arbitragem AI"""
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
                link_whatsapp = gerar_link_whatsapp(email_cliente, plano, valor, id_pagamento, comprovante.name)
                
                st.success("""🎉 Comprovante enviado com sucesso! 
                ⏳ Seu plano está aguardando aprovação. Em breve você receberá acesso!""")
                st.balloons()
                
                st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank" style="
                    display: inline-block;
                    background: #25d366;
                    color: white;
                    padding: 14px 24px;
                    border-radius: 50px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 16px;
                    margin: 20px 0;
                    width: 100%;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(37,211,102,0.3);
                ">💬 CLIQUE AQUI PARA ENVIAR NO WHATSAPP</a>
                """, unsafe_allow_html=True)
                
                st.info("💡 Clique no botão VERDE acima! Ele abre seu WhatsApp com a mensagem pronta — é só enviar junto com a imagem do comprovante!")
                time.sleep(5)
                st.rerun()
            else:
                st.error("❌ Erro ao registrar. Contate o suporte.")

# ====================== 🔧 FUNÇÕES DE MERCADO ======================
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

# ====================== 💡 LEMBRETES DE UPGRADE ======================
def mostrar_lembrete_upgrade(plano_atual):
    if plano_atual == "Gratuito":
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(255,152,0,0.15), rgba(245,127,23,0.05)); border: 1px solid #FF9800; border-radius: 12px; padding: 16px; margin: 15px 0;'>
            <h4 style='margin:0; color:#FF9800;'>🚀 Desbloqueie mais oportunidades!</h4>
            <p style='color:#e0e0e0; font-size:13px; margin:8px 0;'>Você está vendo apenas 3 de 12 moedas e verificando a cada 5 minutos. Com o plano Pro, você monitora 8 moedas a cada 60 segundos e recebe alertas automáticos de lucro!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💳 Fazer Upgrade Agora →", type="primary", use_container_width=True):
            st.session_state.mostrar_upgrade = True
    elif plano_atual == "Pro":
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(156,39,176,0.15), rgba(123,31,162,0.05)); border: 1px solid #9C27B0; border-radius: 12px; padding: 16px; margin: 15px 0;'>
            <h4 style='margin:0; color:#9C27B0;'>👑 Seja VIP — Não perca nenhuma oportunidade!</h4>
            <p style='color:#e0e0e0; font-size:13px; margin:8px 0;'>A cada minuto que passa, novas oportunidades aparecem. Com o plano Premium, você verifica o mercado a cada 15 segundos e monitora moedas ilimitadas!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👑 Virar VIP Agora →", type="primary", use_container_width=True):
            st.session_state.mostrar_upgrade = True

# ====================== 🛡️ VERIFICAÇÃO DE APROVAÇÃO ======================
def verificar_aprovacao():
    if not st.session_state.usuario.get("plano_ativo", False):
        st.markdown("""
        <div style='background: linear-gradient(90deg, rgba(255,193,7,0.15), rgba(255,152,0,0.05)); 
                    border: 2px solid #FF9800; border-radius: 16px; padding: 30px; text-align: center; margin: 40px 0;'>
            <h2 style='color:#FF9800; margin:0;'>⏳ AGUARDANDO APROVAÇÃO</h2>
            <p style='color:#e0e0e0; font-size:16px; margin:15px 0;'>Seu pagamento está sendo verificado. 
            Enquanto isso, os recursos de negociação estão bloqueados.</p>
            <p style='color:#94a3b8;'>📧 Assim que aprovarmos, você receberá acesso completo!</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("💬 Dúvidas? Fale conosco pelo WhatsApp: +55 21 99752-4939")
        st.stop()
    return True
# ====================== 🎨 CONFIGURAÇÃO DA PÁGINA ======================
st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

def init_session():
    for chave in ["logado", "usuario", "dados_usuario", "plano_temp", "pagamento_metodo", 
                  "mostrar_upgrade", "admin_mode", "tela_recuperacao", "email_recuperacao"]:
        if chave not in st.session_state:
            st.session_state[chave] = False if chave in ["logado", "mostrar_upgrade", "admin_mode"] else None

init_session()

# ====================== 🔒 TELA DE LOGIN / CADASTRO / RECUPERAÇÃO ======================
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
        
        # 🔄 TELA DE RECUPERAÇÃO DE SENHA
        if st.session_state.tela_recuperacao:
            st.subheader("🔐 Recuperação de Senha")
            st.markdown("---")
            
            etapa = st.session_state.get("etapa_recuperacao", 1)
            
            if etapa == 1:
                st.info("📧 Digite seu e-mail cadastrado para receber o código de verificação.")
                email_rec = st.text_input("📧 Seu E-mail", key="email_rec")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📤 Enviar Código", type="primary", use_container_width=True):
                        if not email_rec or "@" not in email_rec:
                            st.error("❌ Digite um e-mail válido!")
                        elif not email_existe(email_rec):
                            st.error("❌ Este e-mail não está cadastrado!")
                        else:
                            codigo = gerar_codigo_recuperacao()
                            ok, msg = enviar_email_recuperacao(email_rec, codigo)
                            if ok:
                                salvar_codigo_recuperacao(email_rec, codigo)
                                st.session_state.email_recuperacao = email_rec
                                st.session_state.etapa_recuperacao = 2
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                with col_btn2:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.tela_recuperacao = False
                        st.session_state.etapa_recuperacao = 1
                        st.rerun()
            
            elif etapa == 2:
                st.info("✅ Código enviado! Verifique sua caixa de entrada (e spam) e digite o código abaixo.")
                codigo_digitado = st.text_input("🔢 Código de 6 dígitos", max_chars=6, key="codigo_digitado")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("➡️ Verificar Código", type="primary", use_container_width=True):
                        ok, msg = verificar_codigo(st.session_state.email_recuperacao, codigo_digitado)
                        if ok:
                            st.session_state.etapa_recuperacao = 3
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_btn2:
                    if st.button("🔄 Reenviar", use_container_width=True):
                        codigo = gerar_codigo_recuperacao()
                        ok, msg = enviar_email_recuperacao(st.session_state.email_recuperacao, codigo)
                        if ok:
                            salvar_codigo_recuperacao(st.session_state.email_recuperacao, codigo)
                            st.success("✅ Código reenviado! Verifique seu e-mail.")
                        else:
                            st.error(msg)
            
            elif etapa == 3:
                st.info("🔑 Crie sua nova senha (mínimo 4 caracteres).")
                nova_senha1 = st.text_input("🔑 Nova Senha", type="password", key="nova_senha1")
                nova_senha2 = st.text_input("🔑 Confirmar Nova Senha", type="password", key="nova_senha2")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✅ Salvar Nova Senha", type="primary", use_container_width=True):
                        if len(nova_senha1) < 4:
                            st.error("❌ Senha com mínimo 4 caracteres!")
                        elif nova_senha1 != nova_senha2:
                            st.error("❌ Senhas não coincidem!")
                        else:
                            ok, msg = alterar_senha(st.session_state.email_recuperacao, nova_senha1)
                            if ok:
                                st.success(msg)
                                st.session_state.tela_recuperacao = False
                                st.session_state.etapa_recuperacao = 1
                                st.session_state.email_recuperacao = None
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(msg)
                with col_btn2:
                    if st.button("← Voltar", use_container_width=True):
                        st.session_state.etapa_recuperacao = 1
                        st.rerun()
            
            st.stop()
        
        # 📑 ABAS DE LOGIN E CADASTRO
        aba_login, aba_cadastro = st.tabs(["🔑 ENTRAR", "✨ CRIAR CONTA"])
        
        with aba_cadastro:
            st.subheader("📋 Escolha seu Plano")
            col_p1, col_p2, col_p3 = st.columns(3)
            
            with col_p1:
                st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(76,175,80,0.15),rgba(56,142,60,0.05)); border:2px solid #4CAF50;'>
                <h3 style='color:#4CAF50; margin:0;'>🟢 Gratuito</h3>
                <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 0<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
                <p style='font-size:12px; color:#94a3b8;'>3 moedas · 2 corretoras</p></div>""", unsafe_allow_html=True)
                if st.button("✅ Escolher", key="cad_free", use_container_width=True):
                    st.session_state.plano_temp = "Gratuito"
            
            with col_p2:
                st.markdown("""<div class='plano-card plano-destaque' style='background:linear-gradient(135deg, rgba(255,152,0,0.2),rgba(245,127,23,0.08)); border:3px solid #FF9800;'>
                <span style='background:#FF9800; color:white; padding:3px 10px; border-radius:15px; font-size:10px; font-weight:700;'>MAIS POPULAR</span>
                <h3 style='color:#FF9800; margin:8px 0 0 0;'>🚀 Pro</h3>
                <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 29,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
                <p style='font-size:12px; color:#94a3b8;'>8 moedas · 4 corretoras · Alertas</p></div>""", unsafe_allow_html=True)
                if st.button("🚀 Escolher", key="cad_pro", use_container_width=True):
                    st.session_state.plano_temp = "Pro"
            
            with col_p3:
                st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'>
                <h3 style='color:#9C27B0; margin:0;'>👑 Premium</h3>
                <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
                <p style='font-size:12px; color:#94a3b8;'>Ilimitado · 15s · VIP</p></div>""", unsafe_allow_html=True)
                if st.button("👑 Escolher", key="cad_prem", use_container_width=True):
                    st.session_state.plano_temp = "Premium"
            
            plano_final = st.session_state.get("plano_temp", "Gratuito")
            st.info(f"🎯 Plano selecionado: **{plano_final}**")
            
            if plano_final != "Gratuito":
                st.markdown("---")
                st.subheader("💳 Método de Pagamento")
                st.info("Pagamento via PIX — rápido e seguro!")
            
            st.markdown("---")
            st.subheader("📝 Seus Dados")
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
    
    st.subheader("📤 Passo a passo")
    st.info("1️⃣ Copie o código acima e pague no seu banco  •  2️⃣ Tire print do comprovante  •  3️⃣ Anexe abaixo")
    
    comprovante = st.file_uploader("📎 Anexar comprovante de pagamento", type=["jpg", "jpeg", "png"], key=f"comprovante_{id_pagamento}")
    
    if comprovante:
        st.success(f"✅ Comprovante anexado: {comprovante.name}")
        st.image(comprovante, width=300)
        
        if st.button("✅ JÁ PAGUEI — ENVIAR PARA APROVAÇÃO!", type="primary", use_container_width=True):
            if registrar_pagamento_pendente(email_cliente, plano, valor, id_pagamento, comprovante.name):
                link_whatsapp = gerar_link_whatsapp(email_cliente, plano, valor, id_pagamento, comprovante.name)
                
                st.success("""🎉 Comprovante enviado com sucesso! 
                ⏳ Seu plano está aguardando aprovação. Em breve você receberá acesso!""")
                st.balloons()
                
                st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank" style="
                    display: inline-block;
                    background: #25d366;
                    color: white;
                    padding: 14px 24px;
                    border-radius: 50px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 16px;
                    margin: 20px 0;
                    width: 100%;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(37,211,102,0.3);
                ">💬 ENVIAR NO WHATSAPP — Falar com Suporte</a>
                """, unsafe_allow_html=True)
                
                st.info("💡 Clique no botão VERDE! Ele abre seu WhatsApp com a mensagem pronta — é só enviar junto com a imagem do comprovante!")
                time.sleep(8)
                st.rerun()
            else:
                st.error("❌ Erro ao registrar. Contate o suporte.")
    st.markdown("---")
    if st.button("← Voltar", use_container_width=True):
        st.session_state.tela_recuperacao = False
        st.session_state.etapa_recuperacao = 1
        st.rerun()
(msg)
        
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
                        if dados.get("status_pagamento") == "pendente":
                            st.warning("⏳ Seu pagamento está aguardando aprovação! Você pode usar o app, mas alguns recursos serão liberados após confirmação.")
                        st.success(f"✅ Bem-vindo, {email_log.split('@')[0]}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(dados)
            
            # 🔗 LINK ESQUECI MINHA SENHA
            st.markdown("---")
            if st.button("🔐 Esqueci minha senha", use_container_width=True):
                st.session_state.tela_recuperacao = True
                st.session_state.etapa_recuperacao = 1
                st.rerun()
        
        st.markdown("<hr style='border-color:#334155; margin-top:30px;'>", unsafe_allow_html=True)
        st.warning(f"⚠️ Ferramenta de análise apenas. Não é recomendação de investimento. Suporte: {CONFIG['email_suporte']}")
    st.stop()

# ====================== ✅ USUÁRIO LOGADO ======================
if not st.session_state.logado or not st.session_state.usuario:
    st.warning("🔒 Você precisa fazer login primeiro!")
    st.stop()

user_email = st.session_state.usuario.get("email", "")
user_plano = st.session_state.usuario.get("plano", "Gratuito")
status_pagamento = st.session_state.usuario.get("status_pagamento", "aprovado")
dados = st.session_state.dados_usuario or carregar_dados_usuario(user_email, user_plano)
config_usuario = dados.get("config", {"moedas_selecionadas": MOEDAS[:3], "lucro_min": 0.3, "intervalo": 60})
chaves = dados.get("chaves", {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS})
limites = PLANOS.get(user_plano, PLANOS["Gratuito"])

if status_pagamento == "pendente":
    st.warning("⏳ **Pagamento pendente!** Seu plano está aguardando aprovação. Enviamos a mensagem no WhatsApp, aguarde nossa confirmação! 💬")

# ====================== 🔐 PAINEL DE ADMINISTRAÇÃO ======================
if user_email == ADMIN_EMAIL:
    with st.sidebar:
        st.markdown("---")
        if st.button("🔐 PAINEL ADMIN", type="secondary"):
            st.session_state.admin_mode = not st.session_state.get("admin_mode", False)
    
    if st.session_state.get("admin_mode", False):
        st.markdown("""<style>.stApp {background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);}</style>""", unsafe_allow_html=True)
        st.markdown("# 🔐 PAINEL DE ADMINISTRAÇÃO")
        st.info(f"👤 Administrador: **{user_email}**")
        st.markdown("---")
        
        aba_aprov, aba_usuarios = st.tabs(["📋 Aprovar Pagamentos", "👥 Todos os Usuários"])
        
        with aba_aprov:
            st.subheader("📋 Comprovantes Pendentes de Aprovação")
            comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
            pendentes = [c for c in comprovantes if c["status"] == "pendente"]
            
            if not pendentes:
                st.success("✅ Nenhum pagamento pendente!")
            else:
                for c in pendentes:
                    with st.expander(f"📌 {c['email']} — {c['plano']} — R$ {c['valor']:.2f}", expanded=True):
                        st.write(f"**📅 Data:** {c['data']}")
                        st.write(f"**🆔 ID:** {c['id']}")
                        st.write(f"**📎 Comprovante:** {c['comprovante_nome']}")
                        
                        col_aprov, col_rejeita = st.columns(2)
                        with col_aprov:
                            if st.button(f"✅ APROVAR", key=f"aprov_{c['id']}", type="primary"):
                                if aprovar_usuario(c["email"]):
                                    st.success(f"✅ {c['email']} APROVADO! Plano ativado por 30 dias!")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                        with col_rejeita:
                            if st.button(f"❌ Rejeitar", key=f"rejei_{c['id']}"):
                                st.warning("❌ Rejeitado. Avise o cliente pelo WhatsApp.")
        
        with aba_usuarios:
            st.subheader("👥 Todos os Usuários")
            usuarios = carregar_json(ARQUIVO_USUARIOS, {})
            for email, dados_user in usuarios.items():
                status_icon = "✅" if dados_user.get("plano_ativo", False) else ("⏳" if dados_user.get("status_pagamento") == "pendente" else "❌")
                with st.expander(f"{status_icon} {email} — {dados_user.get('plano', 'Gratuito')}"):
                    st.write(f"**📅 Cadastro:** {dados_user.get('data_cadastro', '—')}")
                    st.write(f"**📅 Expira em:** {dados_user.get('data_expiracao', '—')}")
                    st.write(f"**📊 Status:** {dados_user.get('status_pagamento', 'aprovado')}")
                    st.write(f"**💳 Pagamentos:** {len(dados_user.get('pagamentos', []))}")
                    
                    if not dados_user.get("plano_ativo", False):
                        if st.button(f"🔓 Ativar Plano Manualmente", key=f"ativar_{email}"):
                            if aprovar_usuario(email):
                                st.success(f"✅ {email} ativado com sucesso!")
                                time.sleep(1)
                                st.rerun()
        
        st.markdown("---")
        st.info("💡 Dica: Clique em '🔐 PAINEL ADMIN' na barra lateral para sair do modo admin")
        st.stop()

# ====================== 💳 TELA DE UPGRADE ======================
if st.session_state.get("mostrar_upgrade", False):
    st.markdown("""<style>.stApp {background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);}</style>""", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>💳 Escolha seu Novo Plano</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Desbloqueie todo o potencial de lucro! 🚀💰</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("""<div class='plano-card plano-destaque' style='background:linear-gradient(135deg, rgba(255,152,0,0.2),rgba(245,127,23,0.08)); border:3px solid #FF9800;'>
        <h3 style='color:#FF9800; margin:0;'>🚀 Upgrade para Pro</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 29,90<span style='font-size:14px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>8 moedas · 4 corretoras · Alertas automáticos</p></div>""", unsafe_allow_html=True)
        if st.button("💳 Assinar Pro", type="primary", use_container_width=True):
            exibir_pagamento_pix("Pro", user_email)
    
    with col_p2:
        st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'>
        <h3 style='color:#9C27B0; margin:0;'>👑 Upgrade para Premium</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:14px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>Ilimitado · 15s · Suporte VIP 24/7</p></div>""", unsafe_allow_html=True)
    with col_p2:
        st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'>
        <h3 style='color:#9C27B0; margin:0;'>👑 Upgrade para Premium</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:14px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>Ilimitado · 15s · Suporte VIP 24/7</p></div>""", unsafe_allow_html=True)
        if st.button("👑 Assinar Premium", type="primary", use_container_width=True):
            exibir_pagamento_pix("Premium", user_email)
    
    st.markdown("---")
    if st.button("← Voltar ao Painel", use_container_width=True):
        st.session_state.mostrar_upgrade = False
        st.rerun()
    st.stop()

# ====================== 📊 BARRA LATERAL ======================
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🤖 Arbitragem AI</h2>", unsafe_allow_html=True)
    st.markdown("---")
    status_icon = "✅ Ativo" if st.session_state.usuario.get("plano_ativo", False) else "⏳ Pendente"
    st.info(f"👤 {user_email}\n🎯 Plano: **{user_plano}**\n📊 Status: **{status_icon}**")
    
    if user_plano != "Gratuito" and st.session_state.usuario.get("data_expiracao"):
        st.info(f"📅 Expira em: **{st.session_state.usuario.get('data_expiracao', '—')}**")
    
    st.markdown("---")
    pagina = st.radio("📱 Menu", [
        "Painel Principal",
        "Analisar Mercado",
        "Minhas Corretoras",
        "Configuracoes",
        "Meu Plano"
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

# ====================== 📊 PAINEL PRINCIPAL ======================
if pagina == "Painel Principal":
    st.markdown("<h1>📊 Painel de Controle</h1>", unsafe_allow_html=True)
    mostrar_lembrete_upgrade(user_plano)
    
    if not st.session_state.usuario.get("plano_ativo", False):
        st.warning("⏳ **Status:** Aguardando aprovação — Recursos em breve liberados!")
    
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
    
    if st.session_state.usuario.get("plano_ativo", False):
        st.info("""
        1️⃣ Vá em **Minhas Corretoras** e cole suas chaves API
        2️⃣ Vá em **Configuracoes** e escolha quais moedas monitorar
        3️⃣ Clique em **Analisar Mercado** para buscar oportunidades
        4️⃣ 💰 Lucre com as diferenças de preço!
        """)
    else:
        st.info("""
        ⏳ **Aguardando aprovação...** Assim que confirmarmos seu pagamento, 
        você poderá acessar todos os recursos! ✅
        """)

# ====================== 🔍 ANALISAR MERCADO ======================
elif pagina == "Analisar Mercado":
    verificar_aprovacao()
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

# ====================== 🔐 MINHAS CORRETORAS ======================
elif pagina == "Minhas Corretoras":
    verificar_aprovacao()
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

# ====================== ⚙️ CONFIGURAÇÕES ======================
elif pagina == "Configuracoes":
    verificar_aprovacao()
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

# ====================== 💳 MEU PLANO ======================
elif pagina == "Meu Plano":
    st.markdown("<h1>💳 Gerenciar Assinatura</h1>", unsafe_allow_html=True)
    status_icon = "✅ ATIVO" if st.session_state.usuario.get("plano_ativo", False) else "⏳ PENDENTE DE APROVAÇÃO"
    expiracao_texto = st.session_state.usuario.get("data_expiracao", "Ilimitado / Gratuito")
    
    st.info(f"""
📋 **Plano Atual:** {user_plano}
📊 **Status:** {status_icon}
📅 **Expira em:** {expiracao_texto}
""")
    
    st.markdown("---")
    st.subheader("📋 Detalhes dos Planos")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(76,175,80,0.15),rgba(56,142,60,0.05)); border:2px solid #4CAF50;'>
        <h3 style='color:#4CAF50; margin:0;'>🟢 Gratuito</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 0<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>3 moedas · 2 corretoras · Análise manual</p>
        </div>""", unsafe_allow_html=True)
    
    with col_p2:
        st.markdown("""<div class='plano-card plano-destaque' style='background:linear-gradient(135deg, rgba(255,152,0,0.2),rgba(245,127,23,0.08)); border:3px solid #FF9800;'>
        <span style='background:#FF9800; color:white; padding:3px 10px; border-radius:15px; font-size:10px; font-weight:700;'>MAIS POPULAR</span>
        <h3 style='color:#FF9800; margin:8px 0 0 0;'>🚀 Pro</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 29,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>8 moedas · 4 corretoras · Alertas automáticos</p>
        </div>""", unsafe_allow_html=True)
        if user_plano == "Gratuito":
            if st.button("💳 Assinar Pro", type="primary", use_container_width=True):
                st.session_state.mostrar_upgrade = True
                st.rerun()
    
    with col_p3:
        st.markdown("""<div class='plano-card' style='background:linear-gradient(135deg, rgba(156,39,176,0.15),rgba(123,31,162,0.05)); border:2px solid #9C27B0;'>
        <h3 style='color:#9C27B0; margin:0;'>👑 Premium</h3>
        <div style='font-size:30px; font-weight:700; margin:10px 0;'>R$ 79,90<span style='font-size:12px; color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>Ilimitado · 15s · Suporte VIP 24/7</p>
        </div>""", unsafe_allow_html=True)
        if user_plano != "Premium":
            if st.button("👑 Assinar Premium", type="primary", use_container_width=True):
                st.session_state.mostrar_upgrade = True
                st.rerun()
    
    st.markdown("---")
    st.info(f"💳 Pagamento via PIX aprovado manualmente por você. Acesse o Painel Admin com: {ADMIN_EMAIL}")
