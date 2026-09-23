import streamlit as st
import json
import os
from datetime import datetime
from urllib.parse import quote
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    "senha_admin": "admin123"
}

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_DADOS = "dados.json"

PLANOS = {
    "Gratuito": {
        "preco": 0.0,
        "moedas": 3,
        "atualizacao_segundos": 120,
        "historico": False,
        "alertas_email": False,
        "relatorios": False
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 50,
        "atualizacao_segundos": 60,
        "historico": True,
        "alertas_email": True,
        "relatorios": False
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 9999,
        "atualizacao_segundos": 15,
        "historico": True,
        "alertas_email": True,
        "relatorios": True
    }
}

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
# FUNCAO DE NOTIFICACAO ADMIN
# ==============================================
def notificar_admin(email, plano, valor, id_pag, caminho_imagem=""):
    texto = f"""NOVO PAGAMENTO PENDENTE!

Cliente: {email}
Plano: {plano}
Valor: R$ {valor:.2f}
ID: {id_pag}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Comprovante: {'Salvo no sistema' if caminho_imagem else 'Sem imagem'}

Acesse o PAINEL DE ADMINISTRACAO para verificar e aprovar!"""
    
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
    
    if CONFIG.get("email_remetente") and CONFIG.get("senha_app_email"):
        assunto = f"PAGAMENTO PENDENTE — {email} | {plano}"
        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;max-width:600px;margin:0;padding:20px;background:#f9fafb;">
        <div style="background:white;border-radius:12px;padding:25px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color:#f59e0b;margin-top:0;">Novo Pagamento Pendente</h2>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
        <tr><td style="padding:10px 0;color:#666;">Cliente:</td><td style="font-weight:bold;">{email}</td></tr>
        <tr><td style="padding:10px 0;color:#666;">Plano:</td><td style="font-weight:bold;">{plano}</td></tr>
        <tr><td style="padding:10px 0;color:#666;">Valor:</td><td style="font-weight:bold;font-size:18px;">R$ {valor:.2f}</td></tr>
        <tr><td style="padding:10px 0;color:#666;">ID Pagamento:</td><td>{id_pag}</td></tr>
        <tr><td style="padding:10px 0;color:#666;">Data/Hora:</td><td>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
        </table>
        <p>Acesse o sistema para aprovar ou rejeitar este pagamento.</p>
        <p style="color:#999;font-size:12px;margin-top:30px;">Arbitragem AI © 2026</p>
        </div>
        </body>
        </html>
        """
        enviar_email(CONFIG["email_suporte"], assunto, html)
    
    return link_whats

# ==============================================
# INICIALIZACAO
# ==============================================
st.set_page_config(page_title="Arbitragem AI", layout="wide")

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "admin_logado" not in st.session_state:
    st.session_state["admin_logado"] = False

usuarios = carregar_json(ARQUIVO_USUARIOS, {})

# ==============================================
# TELA DE LOGIN / CADASTRO
# ==============================================
def tela_login():
    st.title("Arbitragem AI")
    st.subheader("Análise de oportunidades entre corretoras")
    st.warning("Apenas análise. Não é recomendação de investimento.")
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
                    st.warning("Aguardando aprovacao do pagamento. Verifique mais tarde.")
            else:
                st.error("E-mail ou senha incorretos!")
    
    with aba_cadastrar:
        novo_email = st.text_input("Seu E-mail", key="cad_email")
        nova_senha = st.text_input("Criar Senha", type="password", key="cad_senha")
        confirma_senha = st.text_input("Repetir Senha", type="password", key="cad_confirma")
        
        if st.button("CRIAR CONTA", type="primary"):
            if novo_email in usuarios:
                st.error("Este e-mail ja esta cadastrado!")
            elif nova_senha != confirma_senha:
                st.error("As senhas nao coincidem!")
            elif len(nova_senha) < 4:
                st.error("Senha muito curta! Minimo 4 caracteres.")
            else:
                usuarios[novo_email] = {
                    "senha": nova_senha,
                    "plano": "Gratuito",
                    "plano_escolhido": "Gratuito",
                    "plano_ativo": True,
                    "status_pagamento": "aprovado",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.session_state["usuario"] = novo_email
                st.session_state["logado"] = True
                st.success("Conta criada! Bem-vindo(a)!")
                st.rerun()
    
    with aba_recuperar:
        st.info("Funcao de recuperacao — digite seu e-mail cadastrado.")
        email_recup = st.text_input("Seu E-mail", key="recup_email")
        if st.button("ENVIAR CODIGO", type="primary"):
            if email_recup in usuarios:
                st.success("Se solicitado, um codigo seria enviado para seu e-mail.")
            else:
                st.error("E-mail nao encontrado!")
    
    st.markdown("---")
    if st.button("PAINEL DE ADMINISTRACAO"):
        st.session_state["pagina"] = "Painel de Administracao"
        st.rerun()

# ==============================================
# TELA DE ESCOLHA DE PLANO
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
        st.write("✅ Atualizacao a cada 2 min")
        st.write("❌ Historico")
        st.write("❌ Alertas por e-mail")
        if st.button("Escolher Gratuito", type="primary"):
            usuarios[st.session_state["usuario"]]["plano"] = "Gratuito"
            usuarios[st.session_state["usuario"]]["plano_escolhido"] = "Gratuito"
            usuarios[st.session_state["usuario"]]["plano_ativo"] = True
            usuarios[st.session_state["usuario"]]["status_pagamento"] = "aprovado"
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.success("Plano ativado!")
            st.rerun()
    
    with col2:
        st.subheader("Pro")
        st.markdown("**R$ 49,90/mes**")
        st.write("✅ Scanner completo")
        st.write("✅ 50 moedas")
        st.write("✅ Atualizacao a cada 1 min")
        st.write("✅ Historico 24h")
        st.write("✅ Alertas por e-mail")
        st.write("❌ Relatorios")
        if st.button("Escolher Pro", type="primary"):
            usuarios[st.session_state["usuario"]]["plano_escolhido"] = "Pro"
            usuarios[st.session_state["usuario"]]["valor_pago"] = 49.90
            usuarios[st.session_state["usuario"]]["status_pagamento"] = "pendente"
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()
    
    with col3:
        st.subheader("Premium")
        st.markdown("**R$ 99,90/mes**")
        st.write("✅ Tudo do Pro")
        st.write("✅ Moedas ilimitadas")
        st.write("✅ Atualizacao a cada 15s")
        st.write("✅ Historico completo")
        st.write("✅ Alertas por e-mail")
        st.write("✅ Relatorios + Download")
        if st.button("Escolher Premium", type="primary"):
            usuarios[st.session_state["usuario"]]["plano_escolhido"] = "Premium"
            usuarios[st.session_state["usuario"]]["valor_pago"] = 99.90
            usuarios[st.session_state["usuario"]]["status_pagamento"] = "pendente"
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()

# ==============================================
# TELA DE PAGAMENTO
# ==============================================
def tela_pagamento():
    st.header("Pagamento via PIX")
    usuario = st.session_state["usuario"]
    dados = usuarios[usuario]
    plano = dados.get("plano_escolhido", "Pro")
    valor = PLANOS[plano]["preco"]
    
    st.subheader(f"Plano: {plano} — R$ {valor:.2f}")
    st.markdown("---")
    
    st.info(f"""
    **Dados do PIX:**
    - Recebedor: {CONFIG['pix_nome_recebedor']}
    - Chave PIX: `{CONFIG['pix_chave']}`
    - Valor: R$ {valor:.2f}
    """)
    
    comprovante = st.file_uploader("Anexar Comprovante de Pagamento", type=["jpg", "jpeg", "png"])
    
    if st.button("JA PAGUEI — ENVIAR COMPROVANTE", type="primary"):
        id_pag = f"PAG{datetime.now().strftime('%Y%m%d%H%M%S')}"
        caminho_img = ""
        
        if comprovante:
            pasta = "comprovantes"
            os.makedirs(pasta, exist_ok=True)
            caminho_img = os.path.join(pasta, f"{id_pag}_{comprovante.name}")
            with open(caminho_img, "wb") as f:
                f.write(comprovante.getbuffer())
        
        usuarios[usuario]["id_pagamento"] = id_pag
        usuarios[usuario]["data_pagamento"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        usuarios[usuario]["caminho_comprovante"] = caminho_img
        salvar_json(ARQUIVO_USUARIOS, usuarios)
        
        link_whats = notificar_admin(usuario, plano, valor, id_pag, caminho_img)
        st.success("Comprovante enviado! Aguardando aprovacao.")
        st.markdown(f"[Clique aqui para avisar no WhatsApp]({link_whats})")
        st.markdown("---")
        if st.button("Voltar aos Planos"):
            st.session_state["pagina"] = "Planos"
            st.rerun()

# ==============================================
# PAINEL PRINCIPAL DO USUARIO
# ==============================================
def painel_principal():
    usuario = st.session_state["usuario"]
    dados = usuarios[usuario]
    plano = dados.get("plano", "Gratuito")
    st.sidebar.write(f"Usuario: {usuario}")
    st.sidebar.write(f"Plano: {plano}")
    st.sidebar.markdown("---")
    
    pagina = st.sidebar.radio("Navegacao", [
        "Painel Principal",
        "Scanner de Arbitragem",
        "Calculadora de Lucro",
        "Alterar Plano",
        "Sair"
    ])
    
    if pagina == "Sair":
        st.session_state.clear()
        st.rerun()
    
    elif pagina == "Painel Principal":
        st.header("Bem-vindo(a) ao Arbitragem AI")
        st.success(f"Plano {plano} ativo!")
        st.info("Use o Scanner para encontrar oportunidades de arbitragem entre corretoras.")
        st.markdown("---")
        st.subheader("Precos de Mercado")
        st.metric("BTC", "$ 63.420,50", "+0,32%")
        st.metric("ETH", "$ 3.218,90", "-0,15%")
        st.metric("SOL", "$ 142,85", "+1,05%")
    
    elif pagina == "Scanner de Arbitragem":
        st.header("Scanner de Arbitragem")
        lucro_min = st.slider("Lucro Minimo (%)", 0.1, 5.0, 0.5, 0.1)
        st.info("Comparando: Binance, Bybit, KuCoin, OKX, Gate.io")
        st.markdown("---")
        
        st.subheader("Oportunidades Detectadas")
        st.info("Nenhuma oportunidade no momento — monitorando...")
        st.write("Quando houver diferenca de preco entre corretoras, aparecera aqui.")
    
    elif pagina == "Calculadora de Lucro":
        st.header("Calculadora de Lucro")
        col1, col2 = st.columns(2)
        with col1:
            preco_compra = st.number_input("Preco de Compra ($)", 0.0, 100000.0, 100.0)
            preco_venda = st.number_input("Preco de Venda ($)", 0.0, 100000.0, 102.0)
            valor_investido = st.number_input("Valor Investido ($)", 0.0, 100000.0, 1000.0)
        with col2:
            qtd = valor_investido / preco_compra if preco_compra > 0 else 0
            valor_venda = qtd * preco_venda
            lucro_bruto = valor_venda - valor_investido
            taxas = valor_investido * 0.001
            lucro_liquido = lucro_bruto - taxas
            st.metric("Quantidade de Moedas", f"{qtd:.4f}")
            st.metric("Valor na Venda", f"$ {valor_venda:.2f}")
            st.metric("Lucro Bruto", f"$ {lucro_bruto:.2f}")
            st.metric("Lucro Liquido", f"$ {lucro_liquido:.2f}", f"{(lucro_liquido/valor_investido*100):.2f}%")
    
    elif pagina == "Alterar Plano":
        tela_planos()

# ==============================================
# PAINEL DE ADMINISTRACAO
# ==============================================
def painel_administracao():
    if st.session_state.get("admin_logado") != True:
        senha_admin = st.text_input("Senha de Administrador", type="password")
        if st.button("ENTRAR", type="primary"):
            if senha_admin == CONFIG["senha_admin"]:
                st.session_state["admin_logado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        st.stop()
    
    st.header("PAINEL DE ADMINISTRACAO")
    st.markdown("---")
    
    aba_admin1, aba_admin2, aba_admin3 = st.tabs(["Pagamentos", "Sistema", "E-mail"])
    
    with aba_admin1:
        st.subheader("Pagamentos Pendentes")
        if "notificacoes" in st.session_state and st.session_state["notificacoes"]:
            for notif in st.session_state["notificacoes"][:5]:
                icone = "Lida" if notif["lida"] else "NOVO"
                st.info(f"{icone} {notif['hora']} — {notif['email']} | {notif['plano']} | R$ {notif['valor']:.2f}")
        st.markdown("---")
        
        usuarios = carregar_json(ARQUIVO_USUARIOS, {})
        pendentes = {
            email: dados 
            for email, dados in usuarios.items()
            if dados.get("status_pagamento") == "pendente" and not dados.get("plano_ativo", False)
        }
        
        if pendentes:
            st.subheader(f"{len(pendentes)} Aguardando VERIFICACAO")
            st.markdown("---")
            for email, dados in pendentes.items():
                with st.expander(f"{email} — {dados.get('plano_escolhido', '—')}"):
                    st.write(f"Valor: R$ {dados.get('valor_pago', 0):.2f}")
                    st.write(f"ID Pagamento: {dados.get('id_pagamento', '—')}")
                    st.write(f"Data: {dados.get('data_pagamento', '—')}")
                    
                    caminho_img = dados.get("caminho_comprovante", "")
                    if caminho_img and os.path.exists(caminho_img):
                        st.markdown("### COMPROVANTE ENVIADO:")
                        st.image(caminho_img, caption=f"Comprovante — {email}", width=400)
                        st.success("Imagem carregada — Verifique a originalidade!")
                    else:
                        st.warning("Nenhuma imagem anexada!")
                    
                    col_aprov, col_rej = st.columns(2)
                    with col_aprov:
                        if st.button(f"APROVAR E LIBERAR", key=f"apr_{email}", type="primary"):
                            usuarios[email]["status_pagamento"] = "aprovado"
                            usuarios[email]["plano"] = dados.get("plano_escolhido", "Pro")
                            usuarios[email]["plano_ativo"] = True
                            salvar_json(ARQUIVO_USUARIOS, usuarios)
                            
                            if CONFIG.get("email_remetente") and CONFIG.get("senha_app_email"):
                                assunto = "Pagamento APROVADO — Acesso Liberado!"
                                html = f"""
                                <html>
                                <body style="font-family:Arial,sans-serif;max-width:600px;margin:0;padding:20px;background:#f9fafb;">
                                <div style="background:white;border-radius:12px;padding:25px;">
                                <h2 style="color:#22c55e;">Seu plano foi liberado!</h2>
                                <p>Ola, {email},</p>
                                <p>Seu pagamento foi confirmado e o plano {dados.get('plano_escolhido', '—')} esta ativo!</p>
                                <p>Acesse o aplicativo e comece a usar agora mesmo.</p>
                                <p style="color:#999;font-size:12px;margin-top:30px;">Arbitragem AI © 2026</p>
                                </div>
                                </body>
                                </html>
                                """
                                enviado, _ = enviar_email(email, assunto, html)
                                if enviado:
                                    st.info("E-mail enviado ao cliente!")
                            
                            st.success(f"{email} — PLANO LIBERADO!")
                            st.balloons()
                            st.rerun()
                    with col_rej:
                        if st.button(f"REJEITAR", key=f"rej_{email}"):
                            usuarios[email]["status_pagamento"] = "rejeitado"
                            salvar_json(ARQUIVO_USUARIOS, usuarios)
                            st.warning(f"{email} — REJEITADO!")
                            st.rerun()
        else:
            st.info("Nenhum pagamento pendente.")
        
        st.markdown("---")
        st.subheader("Todos os Clientes")
        if not usuarios:
            st.info("Ainda nao ha clientes.")
        else:
            for email, dados in usuarios.items():
                icone = {"aprovado":"OK", "pendente":"PENDENTE", "rejeitado":"REJEITADO"}.get(dados.get("status_pagamento","aprovado"), "—")
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
                        if st.button(f"Aplicar", key=f"apl_{email}"):
                            usuarios[email]["plano"] = novo_plano
                            if novo_plano == "Gratuito":
                                usuarios[email]["status_pagamento"] = "aprovado"
                                usuarios[email]["plano_ativo"] = True
                            salvar_json(ARQUIVO_USUARIOS, usuarios)
                            st.success(f"Plano alterado para {novo_plano}!")
                            st.rerun()
                    with col2:
                        st.write(f"Cadastro: {dados.get('data_cadastro', '—')}")
                        st.write(f"Status: {status}")
                        st.write(f"Ativo: {'SIM' if dados.get('plano_ativo', False) else 'NAO'}")
                        if dados.get("caminho_comprovante") and os.path.exists(dados.get("caminho_comprovante")):
                            st.image(dados.get("caminho_comprovante"), width=200, caption="Comprovante")
                    with col3:
                        if st.button("EXCLUIR", key=f"del_{email}"):
                            if f"conf_del_{email}" not in st.session_state:
                                st.session_state[f"conf_del_{email}"] = True
                                st.warning(f"Clique NOVAMENTE para excluir {email}")
                            else:
                                if dados.get("caminho_comprovante") and os.path.exists(dados.get("caminho_comprovante")):
                                    os.remove(dados.get("caminho_comprovante"))
                                del usuarios[email]
                                salvar_json(ARQUIVO_USUARIOS, usuarios)
                                st.success(f"{email} — EXCLUIDO!")
                                if f"conf_del_{email}" in st.session_state:
                                    del st.session_state[f"conf_del_{email}"]
                                st.rerun()
    
    with aba_admin2:
        st.subheader("Dados do Sistema")
        novo_nome = st.text_input("Nome do recebedor do PIX", value=CONFIG["pix_nome_recebedor"])
        nova_chave = st.text_input("Chave PIX", value=CONFIG["pix_chave"])
        novo_email_sup = st.text_input("E-mail de suporte", value=CONFIG["email_suporte"])
        nova_chave_cmc = st.text_input("API Key CoinMarketCap (opcional)", value=CONFIG.get("coinmarketcap_api_key", ""), type="password")
        novo_whatsapp = st.text_input("WhatsApp do Administrador", value=CONFIG["whatsapp_admin"])
        nova_senha_admin = st.text_input("Senha do Painel Admin", value=CONFIG["senha_admin"])
        
        if st.button("SALVAR DADOS DO SISTEMA", type="primary"):
            CONFIG["pix_nome_recebedor"] = novo_nome
            CONFIG["pix_chave"] = nova_chave
            CONFIG["email_suporte"] = novo_email_sup
            CONFIG["coinmarketcap_api_key"] = nova_chave_cmc
            CONFIG["whatsapp_admin"] = novo_whatsapp
            CONFIG["senha_admin"] = nova_senha_admin
            st.success("Dados salvos! Atualize a pagina.")
    
    with aba_admin3:
        st.subheader("Configuracoes de E-mail")
        st.info("Preencha abaixo para receber notificacoes e avisar os clientes por e-mail.")
        
        email_rem = st.text_input("E-mail Remetente", value=CONFIG.get("email_remetente", ""))
        senha_app = st.text_input("Senha de Aplicativo", value=CONFIG.get("senha_app_email", ""), type="password",
                                  help="Para Gmail: ative verificacao em 2 etapas -> gere 'Senha de App'")
        smtp_serv = st.text_input("Servidor SMTP", value=CONFIG.get("smtp_servidor", "smtp.gmail.com"))
        smtp_port = st.number_input("Porta SMTP", value=CONFIG.get("smtp_porta", 587))
        
        if st.button("SALVAR CONFIGURACOES DE E-MAIL", type="primary"):
            CONFIG["email_remetente"] = email_rem
            CONFIG["senha_app_email"] = senha_app
            CONFIG["smtp_servidor"] = smtp_serv
            CONFIG["smtp_porta"] = int(smtp_port)
            st.success("Configuracoes de e-mail salvas!")
        
        st.markdown("---")
        st.subheader("Testar Envio")
        email_teste = st.text_input("E-mail para teste", placeholder="seuemail@exemplo.com")
        if st.button("ENVIAR E-MAIL DE TESTE"):
            if not CONFIG.get("email_remetente") or not CONFIG.get("senha_app_email"):
                st.error("Preencha e salve as configuracoes acima primeiro!")
            else:
                assunto = "Teste — Arbitragem AI"
                html = """
                <html>
                <body style="font-family:Arial,sans-serif;padding:20px;">
                <h2 style="color:#22c55e;">Funcionou!</h2>
                <p>O e-mail esta configurado corretamente.</p>
                <p>Arbitragem AI © 2026</p>
                </body>
                </html>
                """
                enviado, msg = enviar_email(email_teste, assunto, html)
                if enviado:
                    st.success("E-mail enviado com sucesso! Verifique a caixa de entrada.")
                else:
                    st.error(f"Erro: {msg}")
    
    if st.sidebar.button("SAIR DO ADMIN"):
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
    usuario = st.session_state["usuario"]
    dados = usuarios.get(usuario, {})
    if st.session_state["pagina"] == "Planos":
        tela_planos()
    elif st.session_state["pagina"] == "Pagamento":
        tela_pagamento()
    else:
        painel_principal()
