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

ADMIN_EMAIL = "suportearbitrageai@gmail.com"
SEU_WHATSAPP = "5521997524939"

EMAIL_REMETENTE = "suportearbitrageai@gmail.com"
SENHA_APP_EMAIL = "ylovqquzkfajgxgt"
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

def gerar_codigo_recuperacao():
    return str(random.randint(100000, 999999))

def enviar_email_recuperacao(destinatario, codigo):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = destinatario
        msg["Subject"] = "🔐 Código de Recuperação de Senha — Arbitragem AI"
        corpo = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0;padding:20px;">
        <div style="background:#f8f9fa;border-radius:10px;padding:30px;text-align:center;">
        <h2 style="color:#6366f1;">🤖 Arbitragem AI</h2>
        <h3>Recuperação de Senha</h3>
        <p>Você solicitou a recuperação de sua senha.</p>
        <div style="background:#6366f1;color:white;font-size:32px;font-weight:bold;padding:15px 30px;border-radius:8px;margin:20px auto;letter-spacing:5px;">{codigo}</div>
        <p>Este código expira em <strong>15 minutos</strong>.</p>
        <p style="color:#888;font-size:14px;">Se não foi você, ignore este email.</p>
        <p style="color:#999;font-size:12px;">Suporte: {CONFIG['email_suporte']}</p>
        </div></body></html>"""
        msg.attach(MIMEText(corpo, "html"))
        servidor = smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_APP_EMAIL)
        servidor.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        servidor.quit()
        return True, "✅ Código enviado para seu e-mail!"
    except Exception as e:
        print(f"Erro email: {e}")
        return False, "❌ Erro ao enviar email. Tente novamente mais tarde."

def salvar_codigo_recuperacao(email, codigo):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    expira_em = datetime.now() + timedelta(minutes=15)
    codigos[email] = {"codigo": codigo, "expira_em": expira_em.strftime("%Y-%m-%d %H:%M:%S"), "usado": False}
    salvar_json(ARQUIVO_CODIGOS, codigos)

def verificar_codigo(email, codigo_digitado):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    if email not in codigos: return False, "❌ Nenhum código encontrado. Solicite novamente."
    dados = codigos[email]
    if dados["usado"]: return False, "❌ Este código já foi usado. Solicite um novo."
    if datetime.now() > datetime.strptime(dados["expira_em"], "%Y-%m-%d %H:%M:%S"): return False, "❌ Código expirado. Solicite um novo."
    if dados["codigo"] != codigo_digitado: return False, "❌ Código incorreto. Verifique seu e-mail."
    return True, "✅ Código confirmado! Crie sua nova senha."

def marcar_codigo_usado(email):
    codigos = carregar_json(ARQUIVO_CODIGOS, {})
    if email in codigos:
        codigos[email]["usado"] = True
        salvar_json(ARQUIVO_CODIGOS, codigos)

def alterar_senha(email, nova_senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios: return False, "❌ Usuário não encontrado!"
    usuarios[email]["senha"] = nova_senha
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    marcar_codigo_usado(email)
    return True, "✅ Senha alterada com sucesso! Faça login."

def cadastrar_usuario(email, senha, plano):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email in usuarios: return False, "❌ E-mail já cadastrado! Faça login."
    usuarios[email] = {"senha": senha, "plano": plano, "plano_ativo": plano == "Gratuito", "status_pagamento": "aprovado" if plano == "Gratuito" else "pendente", "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "data_expiracao": None, "pagamentos": []}
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True, f"✅ Conta criada! Plano: {plano}"

def verificar_login(email, senha):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios: return False, "❌ E-mail não encontrado!"
    if usuarios[email]["senha"] != senha: return False, "❌ Senha incorreta!"
    return True, usuarios[email]

def email_existe(email):
    return email in carregar_json(ARQUIVO_USUARIOS)

def registrar_pagamento_pendente(email, plano, valor, id_transacao, comprovante_nome=""):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios: return False
    usuarios[email]["plano"] = plano
    usuarios[email]["plano_ativo"] = False
    usuarios[email]["status_pagamento"] = "pendente"
    if "pagamentos" not in usuarios[email]: usuarios[email]["pagamentos"] = []
    usuarios[email]["pagamentos"].append({"id": id_transacao, "plano": plano, "valor": valor, "metodo": "Pix", "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "status": "pendente", "comprovante": comprovante_nome})
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
    comprovantes.append({"id": id_transacao, "email": email, "plano": plano, "valor": valor, "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "comprovante_nome": comprovante_nome, "status": "pendente"})
    salvar_json(ARQUIVO_COMPROVANTES, comprovantes)
    return True

def aprovar_usuario(email):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios: return False
    usuarios[email]["plano_ativo"] = True
    usuarios[email]["status_pagamento"] = "aprovado"
    usuarios[email]["data_expiracao"] = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
    comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
    for c in comprovantes:
        if c["email"] == email and c["status"] == "pendente": c["status"] = "aprovado"
    salvar_json(ARQUIVO_COMPROVANTES, comprovantes)
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def salvar_dados_usuario(email, chaves, config_usuario):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    if email not in usuarios: return False
    usuarios[email]["chaves"] = chaves
    usuarios[email]["config"] = config_usuario
    salvar_json(ARQUIVO_USUARIOS, usuarios)
    return True

def carregar_dados_usuario(email, plano_padrao="Gratuito"):
    usuarios = carregar_json(ARQUIVO_USUARIOS)
    user = usuarios.get(email, {})
    plano = user.get("plano", plano_padrao)
    return {"chaves": user.get("chaves", {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS}), "config": user.get("config", {"moedas_selecionadas": MOEDAS[:PLANOS[plano]["moedas"]], "lucro_min": PLANOS[plano]["lucro_min"], "intervalo": PLANOS[plano]["intervalo"]})}

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
    return f"https://wa.me/{+5521997524939}?text={quote(mensagem)}"
def buscar_preco(url, simbolo, exchange):
    try:
        from urllib import request
        with request.urlopen(url + simbolo.replace("-", ""), timeout=10) as resp:
            dados = json.loads(resp.read().decode())
            preco = float(dados.get("price", 0))
            return preco if preco > 0 else None
    except Exception as e:
        print(f"Erro {exchange}: {e}")
        return None
      
def calcular_lucro(compra_ex, compra_p, venda_ex, venda_p):
    taxa_compra = CORRETORAS[compra_ex]["taxa_compra"] / 100
    taxa_venda = CORRETORAS[venda_ex]["taxa_saque"] / 100
    preco_compra_final = compra_p * (1 + taxa_compra)
    preco_venda_final = venda_p * (1 - taxa_venda)
    lucro_perc = ((preco_venda_final - preco_compra_final) / preco_compra_final) * 100
    return round(lucro_perc, 2)

def exibir_pagamento_pix(plano, email_cliente):
    valor = PLANOS[plano]["preco"]
    id_pag = gerar_id_pagamento()
    desc = f"Plano {plano} - {email_cliente}"
    codigo_pix, chave_pix = gerar_codigo_pix(valor, desc, email_cliente)
    
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
    
    comprovante = st.file_uploader("📎 Anexar comprovante", type=["jpg","jpeg","png"], key=f"comp_{id_pag}")
    
    if comprovante:
        st.success(f"✅ Comprovante: {comprovante.name}")
        st.image(comprovante, width=300)
        
    if st.button("✅ JÁ PAGUEI — ENVIAR PARA APROVAÇÃO!", type="primary", use_container_width=True):
        if not comprovante:
            st.error("⚠️ Por favor, anexe o comprovante primeiro!")
        else:
            if registrar_pagamento_pendente(email_cliente, plano, valor, id_pag, comprovante.name):
                link_whats = gerar_link_whatsapp(email_cliente, plano, valor, id_pag, comprovante.name)
                st.success("🎉 Comprovante enviado com sucesso!")
                st.balloons()
                
                st.markdown(f"""
                <div style='text-align:center;padding:20px;background:rgba(37,211,102,0.1);border-radius:12px;margin:20px 0;'>
                <h3 style='color:#25d366;margin:0;'>📱 Abra o WhatsApp para enviar o comprovante</h3>
                <a href="{link_whats}" target="_blank" style="display:inline-block;background:#25d366;color:white;padding:14px 30px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:18px;margin:20px 0;box-shadow:0 4px 12px rgba(37,211,102,0.3);">💬 CLIQUE AQUI — ENVIAR NO WHATSAPP</a>
                <p style='color:#94a3b8;font-size:14px;'>Abre em uma nova aba → envie a mensagem junto com a imagem!</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.info("✅ Depois de enviar, feche esta página — seu plano será aprovado em breve!")
                st.markdown("---")
                st.info("💡 Você receberá um e-mail/WhatsApp quando seu plano for aprovado!")
                st.stop()  # ✅ PARA AQUI — NÃO VOLTA MAIS!
            else:
                st.error("❌ Erro ao registrar. Contate o suporte.")

def verificar_aprovacao():
    if not st.session_state.usuario.get("plano_ativo", False):
        st.warning("⏳ **Aguardando aprovação** — Recursos liberados em breve!")
        st.stop()

st.set_page_config(page_title="Arbitragem AI", page_icon="🤖", layout="wide")

# ======================================
# ✅ INICIALIZAÇÃO DAS VARIÁVEIS
# ======================================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = {}
if "etapa_recuperacao" not in st.session_state:
    st.session_state.etapa_recuperacao = 0
if "email_recuperacao" not in st.session_state:
    st.session_state.email_recuperacao = ""

# ✅ VARIÁVEL FORA DO BLOCO — AQUI FUNCIONA!
pagina = "Painel Principal"

if "logado" not in st.session_state: st.session_state.logado = False
if "usuario" not in st.session_state: st.session_state.usuario = {}
if "pagina" not in st.session_state: st.session_state.pagina = "login"
if "etapa_recuperacao" not in st.session_state: st.session_state.etapa_recuperacao = 0
if "email_recuperacao" not in st.session_state: st.session_state.email_recuperacao = ""

st.markdown("""
<style>
.stButton>button {border-radius:12px;}
div.stButton > button:first-child {background: linear-gradient(90deg, #6366f1, #8b5cf6);border:none;}
div[data-testid="stForm"] {background:#1e293b;border-radius:16px;padding:20px;}
.plano-card {background:#1e293b;border-radius:16px;padding:20px;text-align:center;}
</style>
""", unsafe_allow_html=True)

if not st.session_state.logado:
    st.title("🤖 Arbitragem AI")
    st.subheader("Sistema Profissional de Arbitragem de Criptomoedas")
    
    aba_login, aba_cadastro, aba_recuperar = st.tabs(["🔑 Entrar", "✨ Criar Conta", "🔓 Recuperar Senha"])
    
    with aba_cadastro:
        st.subheader("Criar sua conta")
        email_cad = st.text_input("Seu e-mail", key="cad_email")
        senha_cad = st.text_input("Criar senha", type="password", key="cad_senha")
        plano_escolhido = st.selectbox("Escolha seu plano", list(PLANOS.keys()), key="cad_plano")
        
        if st.button("✅ Criar Conta", type="primary", use_container_width=True):
            if not email_cad or "@" not in email_cad:
                st.error("❌ Digite um e-mail válido!")
            elif len(senha_cad) < 4:
                st.error("❌ Senha precisa ter pelo menos 4 caracteres!")
            else:
                ok, msg = cadastrar_usuario(email_cad, senha_cad, plano_escolhido)
                if ok:
                    st.success(msg)
                    st.balloons()
                    if plano_escolhido == "Gratuito":
                        st.session_state.logado = True
                        st.session_state.usuario = carregar_dados_usuario(email_cad, plano_escolhido)
                        st.session_state.usuario["email"] = email_cad
                        st.session_state.usuario["plano"] = plano_escolhido
                        st.session_state.usuario["plano_ativo"] = True
                        st.rerun()
                    else:
                        exibir_pagamento_pix(plano_escolhido, email_cad)
                else:
                    st.error(msg)
    
    with aba_login:
        st.subheader("Acessar sua conta")
        email_log = st.text_input("Seu e-mail", key="log_email")
        senha_log = st.text_input("Sua senha", type="password", key="log_senha")
        
        if st.button("🔑 Entrar", type="primary", use_container_width=True):
            if not email_log or not senha_log:
                st.error("❌ Preencha e-mail e senha!")
            else:
                ok, dados = verificar_login(email_log, senha_log)
                if ok:
                    st.session_state.logado = True
                    st.session_state.usuario = carregar_dados_usuario(email_log, dados.get("plano", "Gratuito"))
                    st.session_state.usuario["email"] = email_log
                    st.session_state.usuario.update(dados)
                    st.success("✅ Login bem-sucedido!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(dados)
    
    with aba_recuperar:
        st.subheader("Recuperar senha")
        if st.session_state.etapa_recuperacao == 0:
            email_rec = st.text_input("Digite seu e-mail cadastrado", key="rec_email")
            if st.button("📧 Enviar Código", type="primary", use_container_width=True):
                if not email_existe(email_rec):
                    st.error("❌ E-mail não encontrado!")
                else:
                    st.session_state.email_recuperacao = email_rec
                    codigo = gerar_codigo_recuperacao()
                    salvar_codigo_recuperacao(email_rec, codigo)
                    ok, msg = enviar_email_recuperacao(email_rec, codigo)
                    if ok:
                        st.success(msg)
                        st.info(f"💡 Para teste: seu código é **{codigo}**")
                        st.session_state.etapa_recuperacao = 1
                        st.rerun()
                    else:
                        st.warning("⚠️ Usando código de teste: " + codigo)
                        st.session_state.etapa_recuperacao = 1
                        st.rerun()
        
        elif st.session_state.etapa_recuperacao == 1:
            st.info(f"📧 Código enviado para: **{st.session_state.email_recuperacao}**")
            codigo_digitado = st.text_input("Digite o código recebido", key="rec_codigo")
            nova_senha = st.text_input("Nova senha", type="password", key="rec_nova_senha")
            confirmar_senha = st.text_input("Confirmar nova senha", type="password", key="rec_confirma_senha")
            
            if st.button("🔓 Redefinir Senha", type="primary", use_container_width=True):
                ok, msg = verificar_codigo(st.session_state.email_recuperacao, codigo_digitado)
                if not ok:
                    st.error(msg)
                elif nova_senha != confirmar_senha:
                    st.error("❌ As senhas não coincidem!")
                elif len(nova_senha) < 4:
                    st.error("❌ Senha muito curta! Mínimo 4 caracteres.")
                else:
                    ok, msg = alterar_senha(st.session_state.email_recuperacao, nova_senha)
                    if ok:
                        st.success(msg)
                        st.session_state.etapa_recuperacao = 0
                        st.session_state.email_recuperacao = ""
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)
            
            if st.button("← Voltar", use_container_width=True):
                st.session_state.etapa_recuperacao = 0
                st.session_state.email_recuperacao = ""
                st.rerun()

else:
    user_email = st.session_state.usuario["email"]
    user_plano = st.session_state.usuario.get("plano", "Gratuito")
    plano_ativo = st.session_state.usuario.get("plano_ativo", False)
    limites = PLANOS[user_plano]
    
    if "chaves" not in st.session_state.usuario:
        st.session_state.usuario["chaves"] = {n: {"chave_api": "", "chave_secreta": ""} for n in CORRETORAS}
    if "config" not in st.session_state.usuario:
        st.session_state.usuario["config"] = {
            "moedas_selecionadas": MOEDAS[:limites["moedas"]],
            "lucro_min": limites["lucro_min"],
            "intervalo": limites["intervalo"]
        }
    user_email = st.session_state.usuario.get("email", "") if st.session_state.get("usuario") else ""
    chaves = st.session_state.usuario["chaves"]
    config_usuario = st.session_state.usuario["config"]
    
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>🤖 Arbitragem AI</h2>", unsafe_allow_html=True)
        st.markdown("---")
        status_icon = "✅ Ativo" if plano_ativo else "⏳ Pendente"
        st.info(f"👤 {user_email}\n🎯 Plano: **{user_plano}**\n📊 Status: **{status_icon}**")
        
        if user_plano != "Gratuito" and st.session_state.usuario.get("data_expiracao"):
            st.info(f"📅 Expira em: **{st.session_state.usuario['data_expiracao']}**")
        
        st.markdown("---")
        pagina = st.radio("📱 Menu", [
            "Painel Principal",
            "Analisar Mercado",
            "Minhas Corretoras",
            "Configurações",
            "Meu Plano",
            "Painel Admin" if user_email == ADMIN_EMAIL else None
        ])
        if pagina is None: pagina = "Painel Principal"
        
        st.markdown("---")
        st.text(f"💰 Lucro min: {config_usuario.get('lucro_min', 0.3)}%")
        st.text(f"⏱️ Intervalo: {config_usuario.get('intervalo', 60)}s")
        st.markdown("---")
        
        if st.button("🚪 Sair", type="secondary", use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario = {}
            st.rerun()
if st.session_state.logado and pagina == "Painel Principal":
    st.markdown("<h1>📊 Painel de Controle</h1>", unsafe_allow_html=True)
    
    if not plano_ativo:
        st.warning("⏳ **Status:** Aguardando aprovação — Recursos liberados em breve!")
    
    if user_plano == "Gratuito":
        st.info("💡 Quer mais moedas, mais corretoras e alertas automáticos? Vá em **Meu Plano** e faça upgrade!")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🪙 Moedas", len(config_usuario.get("moedas_selecionadas", MOEDAS[:3])), f"de {limites['moedas']}")
    with c2:
        qtd_cor = len([c for c in chaves if chaves[c].get("chave_api", "")])
        st.metric("🏦 Corretoras", qtd_cor, f"de {limites['corretoras']}")
    with c3:
        st.metric("💰 Lucro Mín", f"{config_usuario.get('lucro_min', 0.3)}%")
    with c4:
        st.metric("⏱️ Atualização", f"{config_usuario.get('intervalo', 60)}s")
    
    st.markdown("---")
    st.subheader("🚀 Comece em 4 passos")
    
    if plano_ativo:
        st.info("""
        1️⃣ Vá em **Minhas Corretoras** e cole suas chaves API
        2️⃣ Vá em **Configurações** e escolha quais moedas monitorar
        3️⃣ Clique em **Analisar Mercado** para buscar oportunidades
        4️⃣ 💰 Lucre com as diferenças de preço!
        """)
    else:
        st.info("""
        ⏳ **Aguardando aprovação...** Assim que confirmarmos seu pagamento, 
        você acessa todos os recursos! ✅
        """)

elif pagina == "Analisar Mercado":
    verificar_aprovacao()
    st.markdown("<h1>🔍 Análise de Mercado em Tempo Real</h1>", unsafe_allow_html=True)
    
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
                    comp_ex, comp_p = ordem[0]
                    vend_ex, vend_p = ordem[-1]
                    if comp_ex != vend_ex:
                        lucro = calcular_lucro(comp_ex, comp_p, vend_ex, vend_p)
                        resultados.append({
                            "par": par, "compra_ex": comp_ex, "compra_preco": comp_p,
                            "venda_ex": vend_ex, "venda_preco": vend_p, "lucro": lucro
                        })
                barra.progress((i+1)/len(moedas))
            
            status.empty()
            
            if resultados:
                st.success(f"✅ {len(resultados)} oportunidades encontradas!")
                for r in sorted(resultados, key=lambda x: -x["lucro"]):
                    with st.expander(f"🪙 {r['par']} | Lucro: {r['lucro']}%", expanded=r["lucro"] >= lucro_min):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("🟢 COMPRAR", r["compra_ex"], f"${r['compra_preco']:.4f}")
                        c2.metric("🔴 VENDER", r["venda_ex"], f"${r['venda_preco']:.4f}")
                        c3.metric("💰 LUCRO", f"{r['lucro']}%")
                        if r["lucro"] >= lucro_min:
                            st.success("🔥 OPORTUNIDADE QUENTE!")
                        elif r["lucro"] > 0:
                            st.info("📈 Lucro pequeno")
                        else:
                            st.error("📉 Sem lucro")
            else:
                st.info("ℹ️ Nenhuma oportunidade agora. Tente novamente mais tarde.")

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
        st.session_state.usuario["chaves"] = chaves
        st.success("✅ Chaves salvas com segurança!")
        st.balloons()

elif pagina == "Configurações":
    verificar_aprovacao()
    st.markdown("<h1>⚙️ Suas Configurações</h1>", unsafe_allow_html=True)
    st.info(f"🎯 Plano: {user_plano} | Limite de moedas: {limites['moedas']}")
    
    if len(config_usuario.get("moedas_selecionadas", [])) >= limites["moedas"] and user_plano != "Premium":
        st.warning("💡 Limite de moedas atingido! Faça upgrade para monitorar mais!")
    
    st.markdown("---")
    moedas_sel = st.multiselect(
        "🪙 Moedas para monitorar", MOEDAS,
        default=config_usuario.get("moedas_selecionadas", MOEDAS[:3]),
        max_selections=limites["moedas"]
    )
    lucro_min = st.slider("💰 Lucro mínimo para alerta (%)", 0.05, 5.0, config_usuario.get("lucro_min", 0.3), 0.05)
    intervalo = st.slider("⏱️ Intervalo entre verificações (segundos)", 15, 600, config_usuario.get("intervalo", 60), 15)
    
    if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary", use_container_width=True):
        config_usuario.update({
            "moedas_selecionadas": moedas_sel,
            "lucro_min": lucro_min,
            "intervalo": intervalo
        })
        salvar_dados_usuario(user_email, chaves, config_usuario)
        st.session_state.usuario["config"] = config_usuario
        st.success("✅ Configurações salvas!")
        st.balloons()

elif pagina == "Meu Plano":
    st.markdown("<h1>💳 Gerenciar Assinatura</h1>", unsafe_allow_html=True)
    status_icon = "✅ ATIVO" if plano_ativo else "⏳ PENDENTE DE APROVAÇÃO"
    expiracao_texto = st.session_state.usuario.get("data_expiracao", "Ilimitado / Gratuito")
    
    st.info(f"""
📋 **Plano Atual:** {user_plano}
📊 **Status:** {status_icon}
📅 **Expira em:** {expiracao_texto}
""")
    
    st.markdown("---")
    st.subheader("📋 Escolha seu Plano")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div style='background:linear-gradient(135deg,rgba(76,175,80,0.15),rgba(56,142,96,0.05));border:2px solid #4CAF50;border-radius:16px;padding:20px;text-align:center;'>
        <h3 style='color:#4CAF50;margin:0;'>🟢 Gratuito</h3>
        <div style='font-size:30px;font-weight:700;margin:10px 0;'>R$ 0<span style='font-size:14px;color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>3 moedas • 2 corretoras • Análise manual</p></div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""<div style='background:linear-gradient(135deg,rgba(255,152,0,0.2),rgba(245,127,23,0.08));border:3px solid #FF9800;border-radius:16px;padding:20px;text-align:center;'>
        <span style='background:#FF9800;color:white;padding:3px 10px;border-radius:15px;font-size:10px;font-weight:bold;'>MAIS POPULAR</span>
        <h3 style='color:#FF9800;margin:8px 0 0;'>🚀 Pro</h3>
        <div style='font-size:30px;font-weight:700;margin:10px 0;'>R$ 29,90<span style='font-size:14px;color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>8 moedas • 4 corretoras • Alertas automáticos</p></div>""", unsafe_allow_html=True)
        if user_plano == "Gratuito":
            if st.button("💳 Assinar Pro", type="primary", use_container_width=True):
                exibir_pagamento_pix("Pro", user_email)
    
    with col3:
        st.markdown("""<div style='background:linear-gradient(135deg,rgba(156,39,176,0.15),rgba(123,31,162,0.05));border:2px solid #9C27B0;border-radius:16px;padding:20px;text-align:center;'>
        <h3 style='color:#9C27B0;margin:0;'>👑 Premium</h3>
        <div style='font-size:30px;font-weight:700;margin:10px 0;'>R$ 79,90<span style='font-size:14px;color:#94a3b8;'>/mês</span></div>
        <p style='color:#e0e0e0;'>Ilimitado • 15s • Suporte VIP 24/7</p></div>""", unsafe_allow_html=True)
        if user_plano != "Premium":
            if st.button("👑 Assinar Premium", type="primary", use_container_width=True):
                exibir_pagamento_pix("Premium", user_email)

elif pagina == "Painel Admin" and user_email == ADMIN_EMAIL:
    st.markdown("<h1>🔐 Painel de Administração</h1>", unsafe_allow_html=True)
    
    usuarios = carregar_json(ARQUIVO_USUARIOS, {})
    comprovantes = carregar_json(ARQUIVO_COMPROVANTES, [])
    
    aba1, aba2 = st.tabs(["📋 Pagamentos Pendentes", "👥 Usuários"])
    
    with aba1:
        pendentes = [c for c in comprovantes if c.get("status") == "pendente"]
        if not pendentes:
            st.success("✅ Nenhum pagamento pendente!")
        else:
            st.info(f"📋 {len(pendentes)} pagamentos aguardando aprovação")
            for c in pendentes:
                st.markdown("---")
                st.write(f"👤 **Cliente:** {c['email']}")
                st.write(f"📋 **Plano:** {c['plano']} | 💰 **Valor:** R$ {c['valor']:.2f}")
                st.write(f"📅 **Data:** {c['data']}")
                st.write(f"📎 **Comprovante:** {c.get('comprovante_nome', 'Não enviado')}")
                col_ap, col_re = st.columns(2)
                with col_ap:
                    if st.button(f"✅ APROVAR — {c['id']}", key=f"apr_{c['id']}", type="primary"):
                        if aprovar_usuario(c["email"]):
                            st.success(f"✅ {c['email']} aprovado!")
                            st.rerun()
                with col_re:
                    if st.button(f"❌ REJEITAR — {c['id']}", key=f"rej_{c['id']}"):
                        for comp in comprovantes:
                            if comp["id"] == c["id"]: comp["status"] = "rejeitado"
                        salvar_json(ARQUIVO_COMPROVANTES, comprovantes)
                        st.info(f"❌ {c['email']} rejeitado")
                        st.rerun()
    
    with aba2:
        if not usuarios:
            st.info("ℹ️ Nenhum usuário cadastrado ainda.")
        else:
            st.info(f"👥 {len(usuarios)} usuários cadastrados")
            for email, dados in usuarios.items():
                st.markdown("---")
                st.write(f"👤 **{email}**")
                st.write(f"📋 Plano: {dados.get('plano', 'Gratuito')} | Status: {'✅ Ativo' if dados.get('plano_ativo') else '⏳ Pendente'}")
                if not dados.get("plano_ativo") and dados.get("plano") != "Gratuito":
                    if st.button(f"✅ Ativar conta — {email}", key=f"ativ_{email}"):
                        if aprovar_usuario(email):
                            st.success(f"✅ {email} ativado!")
                            st.rerun()

st.markdown("---")
st.markdown("<div style='text-align:center;color:#94a3b8;font-size:12px;'>🤖 Arbitragem AI © 2026 | Sistema de Análise e Arbitragem de Criptomoedas</div>", unsafe_allow_html=True)
