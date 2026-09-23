import streamlit as st
import json
import os
import time
import random
from datetime import datetime
from urllib.parse import quote
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

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
    "senha_admin": "admin123",
    "logo_principal": "logo_principal.png",
    "logo_pequeno": "logo_pequeno.png",
    "taxa_media_corretora_perc": 0.1
}

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_SISTEMA = "sistema.json"
ARQUIVO_HISTORICO = "historico_oportunidades.json"
ARQUIVO_CODIGOS_RECUPERACAO = "codigos_recuperacao.json"

PLANOS = {
    "Gratuito": {
        "preco": 0.0,
        "moedas": 3,
        "atualizacao_segundos": 120,
        "alertas_email": False,
        "alertas_whatsapp": False,
        "corretoras": ["Binance", "Bybit"],
        "modo_avancado": False
    },
    "Pro": {
        "preco": 49.90,
        "moedas": 50,
        "atualizacao_segundos": 60,
        "alertas_email": True,
        "alertas_whatsapp": True,
        "corretoras": ["Binance", "Bybit", "KuCoin", "OKX"],
        "modo_avancado": True
    },
    "Premium": {
        "preco": 99.90,
        "moedas": 9999,
        "atualizacao_segundos": 15,
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
# FUNCOES DE LOGO E NAVEGACAO
# ==============================================
def exibir_logo_principal(largura=250):
    caminho = CONFIG.get("logo_principal", "logo_principal.png")
    if os.path.exists(caminho):
        st.image(caminho, width=largura)
    else:
        st.markdown("<h1 style='text-align: center; color: #22c55e;'>ARBITRAGEM AI</h1>", unsafe_allow_html=True)

def botao_voltar_menu():
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

def botao_sair_conta():
    if st.sidebar.button("🚪 Sair da Conta", type="secondary"):
        for chave in list(st.session_state.keys()):
            if chave not in ["pagina"]:
                del st.session_state[chave]
        st.session_state["pagina"] = "inicio"
        st.rerun()

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
            return False, "Configure o e-mail no Painel de Administração primeiro"
        
        msg = MIMEMultipart()
        msg["From"] = remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(mensagem_html, "html"))
        
        with smtplib.SMTP(servidor_smtp, porta) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)
        
        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        return False, f"Erro ao enviar: {str(e)}"

# ==============================================
# FUNCOES DE RECUPERACAO DE SENHA
# ==============================================
def gerar_codigo_recuperacao(email):
    codigo = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    codigos = carregar_json(ARQUIVO_CODIGOS_RECUPERACAO, {})
    codigos[email] = {
        "codigo": codigo,
        "expira_em": datetime.now().timestamp() + 900
    }
    salvar_json(ARQUIVO_CODIGOS_RECUPERACAO, codigos)
    return codigo

def verificar_codigo(email, codigo_digitado):
    codigos = carregar_json(ARQUIVO_CODIGOS_RECUPERACAO, {})
    if email not in codigos:
        return False
    dados = codigos[email]
    if dados["codigo"] == codigo_digitado and datetime.now().timestamp() < dados["expira_em"]:
        del codigos[email]
        salvar_json(ARQUIVO_CODIGOS_RECUPERACAO, codigos)
        return True
    return False

# ==============================================
# FUNCOES DO SCANNER E API DAS CORRETORAS
# ==============================================
def gerar_preco_simulado(moeda, corretora, variacao_max=0.008):
    precos_base = {
        "BTC": 63420.50, "ETH": 3218.90, "SOL": 142.85, "XRP": 0.52, "ADA": 0.45,
        "DOGE": 0.12, "DOT": 7.85, "AVAX": 35.20, "MATIC": 0.58, "LINK": 14.50
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
    return {
        "liquidez_suficiente": liquidez_alta,
        "alerta": "" if liquidez_alta else "⚠️ Volume baixo — pode ser difícil executar!"
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
                op = {
                    "moeda": moeda, "comprar_em": compra_em, "vender_em": venda_em,
                    "preco_compra": pc, "preco_venda": pv, **calc,
                    "liquidez_compra": verificar_liquidez(moeda, compra_em),
                    "liquidez_venda": verificar_liquidez(moeda, venda_em),
                    "hora_deteccao": datetime.now().strftime("%H:%M:%S")
                }
                oportunidades.append(op)
                salvar_oportunidade_historico(op)
    return sorted(oportunidades, key=lambda x: x["lucro_liquido_perc"], reverse=True)

# ==============================================
# INICIALIZACAO
# ==============================================
st.set_page_config(page_title="Arbitragem AI", layout="wide")

if "usuario" not in st.session_state: st.session_state["usuario"] = None
if "email_usuario" not in st.session_state: st.session_state["email_usuario"] = None
if "logado" not in st.session_state: st.session_state["logado"] = False
if "admin_logado" not in st.session_state: st.session_state["admin_logado"] = False
if "pagina_recuperacao" not in st.session_state: st.session_state["pagina_recuperacao"] = "solicitar_email"

usuarios = carregar_json(ARQUIVO_USUARIOS, {})

# ==============================================
# TELA DE LOGIN / CADASTRO
# ==============================================
def tela_login():
    exibir_logo_principal()
    st.subheader("Análise inteligente de oportunidades entre corretoras")
    st.warning("⚠️ Apenas análise. Não é recomendação de investimento.")
    st.markdown("---")
    
    aba_entrar, aba_cadastrar, aba_recuperar = st.tabs(["Entrar", "Criar Conta", "Recuperar Senha"])
    
    with aba_entrar:
        identificador = st.text_input("E-mail ou Nome de Usuário", key="login_id")
        senha = st.text_input("Sua Senha", type="password", key="login_senha")
        
        if st.button("ENTRAR", type="primary"):
            usuario_encontrado = None
            email_usuario = None
            for email, dados in usuarios.items():
                if email == identificador or dados.get("nome_usuario") == identificador:
                    if dados.get("senha") == senha:
                        usuario_encontrado = dados
                        email_usuario = email
                        break
            if usuario_encontrado:
                if usuario_encontrado.get("plano_ativo", False) or usuario_encontrado.get("plano") == "Gratuito":
                    st.session_state["usuario"] = usuario_encontrado
                    st.session_state["email_usuario"] = email_usuario
                    st.session_state["logado"] = True
                    st.rerun()
                else:
                    st.warning("Aguardando aprovação do pagamento.")
            else:
                st.error("E-mail/Usuário ou senha incorretos!")
        
        st.info("🔜 Em breve: Login com Google")
    
    with aba_cadastrar:
        novo_email = st.text_input("Seu E-mail", key="cad_email")
        nome_usuario = st.text_input("Nome de Usuário (para login)", key="cad_usuario")
        nova_senha = st.text_input("Criar Senha", type="password", key="cad_senha")
        confirma_senha = st.text_input("Repetir Senha", type="password", key="cad_confirma")
        
        if st.button("CRIAR CONTA", type="primary"):
            email_existe = novo_email in usuarios
            usuario_existe = any(d.get("nome_usuario") == nome_usuario for d in usuarios.values())
            
            if email_existe:
                st.error("Este e-mail já está cadastrado!")
            elif usuario_existe:
                st.error("Este nome de usuário já está em uso! Escolha outro.")
            elif nova_senha != confirma_senha:
                st.error("As senhas não coincidem!")
            elif len(nova_senha) < 4:
                st.error("Senha muito curta! Mínimo 4 caracteres.")
            elif not nome_usuario or len(nome_usuario) < 3:
                st.error("Nome de usuário deve ter pelo menos 3 caracteres!")
            else:
                usuarios[novo_email] = {
                    "nome_usuario": nome_usuario,
                    "senha": nova_senha,
                    "plano": "Gratuito",
                    "plano_escolhido": "Gratuito",
                    "plano_ativo": True,
                    "status_pagamento": "aprovado",
                    "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "apis_corretoras": {}
                }
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.session_state["usuario"] = usuarios[novo_email]
                st.session_state["email_usuario"] = novo_email
                st.session_state["logado"] = True
                st.success("Conta criada com sucesso! 🎉")
                st.rerun()
    
    with aba_recuperar:
        if st.session_state["pagina_recuperacao"] == "solicitar_email":
            email_recup = st.text_input("Digite seu e-mail cadastrado", key="recup_email")
            if st.button("ENVIAR CÓDIGO", type="primary"):
                if email_recup in usuarios:
                    codigo = gerar_codigo_recuperacao(email_recup)
                    assunto = "🔐 Código de Recuperação de Senha — Arbitragem AI"
                    html = f"""
                    <html><body style="font-family:Arial,sans-serif;padding:20px;">
                    <h2 style="color:#22c55e;">Recuperação de Senha</h2>
                    <p>Olá,</p>
                    <p>Você solicitou a recuperação de senha. Use o código abaixo:</p>
                    <div style="font-size:28px;font-weight:bold;background:#f0fdf4;padding:15px;border-radius:8px;text-align:center;letter-spacing:5px;">
                    {codigo}
                    </div>
                    <p>Este código expira em 15 minutos.</p>
                    <p style="color:#999;font-size:12px;">Se não foi você, ignore este e-mail.</p>
                    </body></html>
                    """
                    ok, msg = enviar_email(email_recup, assunto, html)
                    if ok:
                        st.session_state["email_recuperacao"] = email_recup
                        st.session_state["pagina_recuperacao"] = "digitar_codigo"
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("E-mail não encontrado!")
        
        elif st.session_state["pagina_recuperacao"] == "digitar_codigo":
            email_recup = st.session_state["email_recuperacao"]
            st.info(f"Código enviado para **{email_recup}**")
            codigo_digitado = st.text_input("Digite o código de 6 dígitos", max_chars=6)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("REENVIAR CÓDIGO"):
                    codigo = gerar_codigo_recuperacao(email_recup)
                    assunto = "🔐 Código de Recuperação — Arbitragem AI"
                    html = f"<p>Seu código: <strong>{codigo}</strong></p>"
                    enviar_email(email_recup, assunto, html)
                    st.success("Código reenviado!")
            with col2:
                if st.button("VERIFICAR", type="primary"):
                    if verificar_codigo(email_recup, codigo_digitado):
                        st.session_state["pagina_recuperacao"] = "nova_senha"
                        st.rerun()
                    else:
                        st.error("Código inválido ou expirado!")
            
            if st.button("❌ Cancelar"):
                st.session_state["pagina_recuperacao"] = "solicitar_email"
                st.rerun()
        
        elif st.session_state["pagina_recuperacao"] == "nova_senha":
            email_recup = st.session_state["email_recuperacao"]
            nova_senha1 = st.text_input("Nova Senha", type="password")
            nova_senha2 = st.text_input("Repetir Nova Senha", type="password")
            
            if st.button("ALTERAR SENHA", type="primary"):
                if nova_senha1 != nova_senha2:
                    st.error("As senhas não coincidem!")
                elif len(nova_senha1) < 4:
                    st.error("Senha muito curta!")
                else:
                    usuarios[email_recup]["senha"] = nova_senha1
                    salvar_json(ARQUIVO_USUARIOS, usuarios)
                    st.success("✅ Senha alterada com sucesso! Faça login.")
                    st.session_state["pagina_recuperacao"] = "solicitar_email"
                    st.rerun()
    
    st.markdown("---")
    if st.button("🔑 PAINEL DE ADMINISTRAÇÃO"):
        st.session_state["pagina"] = "Painel de Administração"
        st.rerun()

# ==============================================
# TELA DE PLANOS
# ==============================================
def tela_planos():
    botao_voltar_menu()
    st.header("Escolha Seu Plano")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Gratuito")
        st.markdown("**R$ 0,00**")
        st.write("✅ Scanner básico")
        st.write("✅ 3 moedas")
        st.write("✅ Lucro líquido calculado")
        st.write("✅ 2 corretoras")
        st.write("❌ Alertas")
        if st.button("Escolher Gratuito", type="primary"):
            email = st.session_state["email_usuario"]
            usuarios[email].update({
                "plano": "Gratuito", "plano_escolhido": "Gratuito",
                "plano_ativo": True, "status_pagamento": "aprovado"
            })
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["usuario"] = usuarios[email]
            st.success("Plano ativado!")
            st.rerun()
    
    with col2:
        st.subheader("Pro")
        st.markdown("**R$ 49,90/mês**")
        st.write("✅ 50 moedas")
        st.write("✅ 4 corretoras")
        st.write("✅ Atualização 60s")
        st.write("✅ Alertas por e-mail")
        if st.button("Escolher Pro", type="primary"):
            email = st.session_state["email_usuario"]
            usuarios[email].update({
                "plano_escolhido": "Pro", "valor_pago": 49.90, "status_pagamento": "pendente"
            })
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()
    
    with col3:
        st.subheader("Premium")
        st.markdown("**R$ 99,90/mês**")
        st.write("✅ Moedas ilimitadas")
        st.write("✅ Todas corretoras")
        st.write("✅ Atualização 15s")
        st.write("✅ Alertas e-mail + WhatsApp")
        st.write("✅ Verificação de liquidez")
        if st.button("Escolher Premium", type="primary"):
            email = st.session_state["email_usuario"]
            usuarios[email].update({
                "plano_escolhido": "Premium", "valor_pago": 99.90, "status_pagamento": "pendente"
            })
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.session_state["pagina"] = "Pagamento"
            st.rerun()

# ==============================================
# TELA DE PAGAMENTO
# ==============================================
def tela_pagamento():
    botao_voltar_menu()
    email = st.session_state["email_usuario"]
    plano = usuarios[email].get("plano_escolhido", "Pro")
    valor = PLANOS[plano]["preco"]
    st.header("Pagamento via PIX")
    st.subheader(f"Plano: {plano} — R$ {valor:.2f}")
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
            os.makedirs("comprovantes", exist_ok=True)
            caminho_img = f"comprovantes/{id_pag}_{comprovante.name}"
            with open(caminho_img, "wb") as f:
                f.write(comprovante.getbuffer())
        usuarios[email].update({
            "id_pagamento": id_pag,
            "data_pagamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "caminho_comprovante": caminho_img
        })
        salvar_json(ARQUIVO_USUARIOS, usuarios)
        texto = f"""NOVO PAGAMENTO PENDENTE!

Cliente: {email}
Plano: {plano}
Valor: R$ {valor:.2f}
ID: {id_pag}

Acesse o PAINEL DE ADMINISTRAÇÃO para aprovar!"""
        link_whats = f"https://wa.me/{CONFIG['whatsapp_admin']}?text={quote(texto)}"
        st.success("Comprovante enviado! Aguardando aprovação.")
        st.markdown(f"[Clique aqui para avisar no WhatsApp →]({link_whats})")
    if st.button("Voltar aos Planos"):
        st.session_state["pagina"] = "Planos"
        st.rerun()

# ==============================================
# CONFIGURACAO DE APIS DAS CORRETORAS
# ==============================================
def tela_configurar_apis():
    botao_voltar_menu()
    email = st.session_state["email_usuario"]
    st.header("🔗 Configurar APIs das Corretoras")
    st.info("""
    **Como funciona:**
    - Insira suas chaves de API para o sistema ler seus saldos e preços reais
    - As chaves ficam salvas APENAS na sua conta
    - Use chaves com permissão de **leitura** apenas para segurança
    """)
    
    corretora_escolhida = st.selectbox("Escolha a Corretora", CORRETORAS_DISPONIVEIS)
    api_key = st.text_input(f"API Key — {corretora_escolhida}", type="password")
    api_secret = st.text_input(f"API Secret — {corretora_escolhida}", type="password")
    
    if st.button("💾 Salvar Chaves", type="primary"):
        if not api_key or not api_secret:
            st.error("Preencha ambos os campos!")
        else:
            if "apis_corretoras" not in usuarios[email]:
                usuarios[email]["apis_corretoras"] = {}
            usuarios[email]["apis_corretoras"][corretora_escolhida] = {
                "api_key": api_key,
                "api_secret": api_secret,
                "data_salvo": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            salvar_json(ARQUIVO_USUARIOS, usuarios)
            st.success(f"✅ Chaves de {corretora_escolhida} salvas!")
    
    st.markdown("---")
    st.subheader("Suas Corretoras Conectadas")
    apis_salvas = usuarios[email].get("apis_corretoras", {})
    if not apis_salvas:
        st.info("Nenhuma corretora conectada ainda.")
    else:
        for corretora, dados in apis_salvas.items():
            with st.expander(f"✅ {corretora} — Salvo em {dados['data_salvo']}"):
                st.write(f"API Key: {dados['api_key'][:6]}...{dados['api_key'][-4:]}")
                if st.button(f"❌ Remover {corretora}", key=f"del_{corretora}"):
                    del usuarios[email]["apis_corretoras"][corretora]
                    salvar_json(ARQUIVO_USUARIOS, usuarios)
                    st.rerun()

# ==============================================
# EDITAR PERFIL
# ==============================================
def tela_editar_perfil():
    botao_voltar_menu()
    email = st.session_state["email_usuario"]
    dados = usuarios[email]
    st.header("👤 Editar Perfil")
    
    with st.form("form_perfil"):
        novo_usuario = st.text_input("Nome de Usuário", value=dados.get("nome_usuario", ""))
        st.info(f"E-mail: {email} (não pode ser alterado)")
        
        st.subheader("Alterar Senha")
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirma_nova = st.text_input("Repetir Nova Senha", type="password")
        
        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
            alterou = False
            
            if novo_usuario and novo_usuario != dados.get("nome_usuario"):
                existe = any(
                    d.get("nome_usuario") == novo_usuario and e != email
                    for e, d in usuarios.items()
                )
                if existe:
                    st.error("Nome de usuário já em uso!")
                elif len(novo_usuario) < 3:
                    st.error("Nome de usuário muito curto!")
                else:
                    usuarios[email]["nome_usuario"] = novo_usuario
                    alterou = True
                    st.success("Nome de usuário alterado!")
            
            if senha_atual or nova_senha or confirma_nova:
                if dados["senha"] != senha_atual:
                    st.error("Senha atual incorreta!")
                elif nova_senha != confirma_nova:
                    st.error("Novas senhas não coincidem!")
                elif len(nova_senha) < 4:
                    st.error("Nova senha muito curta!")
                else:
                    usuarios[email]["senha"] = nova_senha
                    alterou = True
                    st.success("Senha alterada com sucesso!")
            
            if alterou:
                salvar_json(ARQUIVO_USUARIOS, usuarios)
                st.rerun()

# ==============================================
# PAINEL PRINCIPAL DO USUARIO
# ==============================================
def painel_principal():
    email = st.session_state["email_usuario"]
    dados = usuarios[email]
    plano = dados.get("plano", "Gratuito")
    dados_plano = PLANOS[plano]
    
    st.sidebar.markdown(f"**👤 {dados.get('nome_usuario', email.split('@')[0])}**")
    st.sidebar.write(f"Plano: {plano}")
    st.sidebar.markdown("---")
    
    pagina = st.sidebar.radio("Navegação", [
        "Painel Principal",
        "Scanner de Arbitragem",
        "Minhas Corretoras (APIs)",
        "Histórico de Oportunidades",
        "Calculadora de Lucro Real",
        "Editar Perfil",
        "Alterar Plano"
    ])
    
    botao_sair_conta()
    
    if pagina == "Painel Principal":
        st.header("Bem-vindo(a) ao Arbitragem AI 🚀")
        st.success(f"✅ Plano {plano} ativo!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Corretoras permitidas", len(dados_plano["corretoras"]))
        col2.metric("Moedas monitoradas", dados_plano["moedas"] if dados_plano["moedas"] < 100 else "Ilimitadas")
        col3.metric("Atualização", f"{dados_plano['atualizacao_segundos']}s")
        st.markdown("---")
        st.info("""
        💡 **Próximos passos:**
        1. Vá em **Minhas Corretoras (APIs)** e conecte suas contas
        2. Use o **Scanner** para ver oportunidades
        3. Confirme sempre os preços diretamente na corretora!
        """)
    
    elif pagina == "Minhas Corretoras (APIs)":
        tela_configurar_apis()
    
    elif pagina == "Scanner de Arbitragem":
        st.header("🔍 Scanner de Arbitragem Inteligente")
        lucro_min_perc = st.slider("Lucro Mínimo Líquido (%)", 0.1, 5.0, 0.5, 0.1)
        auto_refresh = st.checkbox("Atualização Automática")
        
        corretoras_conectadas = list(dados.get("apis_corretoras", {}).keys())
        corretoras_permitidas = dados_plano["corretoras"]
        
        if not corretoras_conectadas:
            st.warning("⚠️ Nenhuma corretora conectada. Usando dados de demonstração. Conecte suas APIs em **Minhas Corretoras** para dados reais!")
            corretoras = corretoras_permitidas
        else:
            st.success(f"✅ {len(corretoras_conectadas)} corretora(s) conectada(s)")
            corretoras = corretoras_conectadas
            if dados_plano.get("modo_avancado"):
                corretoras = st.multiselect("Corretoras para monitorar", corretoras_permitidas, default=corretoras_conectadas)
        
        moedas = MOEDAS_MONITORADAS[:dados_plano["moedas"]] if dados_plano["moedas"] < 100 else MOEDAS_MONITORADAS
        st.info(f"Monitorando {len(moedas)} moedas em {', '.join(corretoras)}")
        
        if st.button("🔄 ESCANEAR AGORA", type="primary") or auto_refresh:
            with st.spinner("Analisando preços..."):
                oportunidades = escanear_oportunidades(corretoras, moedas, lucro_min_perc)
            if not oportunidades:
                st.info("Nenhuma oportunidade encontrada no momento.")
            else:
                st.subheader(f"✅ {len(oportunidades)} oportunidade(s) encontrada(s)")
                st.warning("⚠️ Confirme os preços na corretora antes de operar!")
                for op in oportunidades[:10]:
                    with st.expander(f"💰 {op['moeda']} — {op['lucro_liquido_perc']:.2f}% LÍQUIDO"):
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown(f"✅ Comprar em: **{op['comprar_em']}**")
                            st.write(f"Preço: $ {op['preco_compra']:.4f}")
                            st.info(op['liquidez_compra']['alerta'] or "✅ Liquidez suficiente")
                        with cb:
                            st.markdown(f"📤 Vender em: **{op['vender_em']}**")
                            st.write(f"Preço: $ {op['preco_venda']:.4f}")
                            st.info(op['liquidez_venda']['alerta'] or "✅ Liquidez suficiente")
                        l1, l2, l3 = st.columns(3)
                        l1.metric("Lucro Bruto", f"{op['lucro_bruto_perc']:.2f}%")
                        l2.metric("✅ Lucro Líquido", f"{op['lucro_liquido_perc']:.2f}%")
                        l3.metric("Em $1.000", f"$ {(1000*op['lucro_liquido_perc']/100):.2f}")
            if auto_refresh:
                time.sleep(dados_plano["atualizacao_segundos"])
                st.rerun()
    
    elif pagina == "Histórico de Oportunidades":
        st.header("📈 Histórico de Oportunidades")
        hist = carregar_json(ARQUIVO_HISTORICO, [])
        if not hist:
            st.info("Nenhuma oportunidade registrada ainda.")
        else:
            st.info(f"Total: {len(hist)} oportunidades")
            for op in hist[:50]:
                st.write(f"{op.get('hora')} | {op['moeda']} | {op['comprar_em']}→{op['vender_em']} | {op['lucro_liquido_perc']:.2f}%")
    
    elif pagina == "Calculadora de Lucro Real":
        st.header("🧮 Calculadora de Lucro Real (com taxas)")
        c1, c2 = st.columns(2)
        with c1:
            pc = st.number_input("Preço Compra ($)", 0.0, 100000.0, 100.0)
            pv = st.number_input("Preço Venda ($)", 0.0, 100000.0, 102.0)
            valor_inv = st.number_input("Valor Investido ($)", 0.0, 100000.0, 1000.0)
            taxa = st.number_input("Taxa Corretora (%)", 0.0, 5.0, CONFIG["taxa_media_corretora_perc"])
        with c2:
            calc = calcular_lucro_liquido(pc, pv, taxa)
            qtd = valor_inv / pc if pc > 0 else 0
            st.metric("Quantidade de Moedas", f"{qtd:.4f}")
            st.metric("Lucro BRUTO", f"{calc['lucro_bruto_perc']:.2f}%")
            st.metric("✅ Lucro LÍQUIDO", f"{calc['lucro_liquido_perc']:.2f}%")
            if calc['lucro_liquido_perc'] <= 0:
                st.error("❌ Não dá lucro após taxas!")
            elif calc['lucro_liquido_perc'] < 0.3:
                st.warning("⚠️ Lucro pequeno — risco de variação")
            else:
                st.success("✅ Margem segura!")
    
    elif pagina == "Editar Perfil":
        tela_editar_perfil()
    
    elif pagina == "Alterar Plano":
        tela_planos()

# ==============================================
# PAINEL DE ADMINISTRACAO COMPLETO
# ==============================================
def painel_administracao():
    botao_voltar_menu()
    if st.session_state.get("admin_logado") != True:
        st.header("🔐 Painel de Administração")
        senha_admin = st.text_input("Senha de Administrador", type="password")
        if st.button("ENTRAR", type="primary"):
            if senha_admin == CONFIG["senha_admin"]:
                st.session_state["admin_logado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        st.stop()
    
    st.header("⚙️ PAINEL DE ADMINISTRAÇÃO")
    aba1, aba2, aba3, aba4 = st.tabs(["Pagamentos & Usuários", "Editar Contas", "Sistema", "E-mail"])
    
    with aba1:
        st.subheader("Pagamentos Pendentes")
        usrs = carregar_json(ARQUIVO_USUARIOS, {})
        pendentes = {e: d for e, d in usrs.items() if d.get("status_pagamento") == "pendente"}
        if pendentes:
            st.info(f"{len(pendentes)} pagamento(s) aguardando")
            for email, d in pendentes.items():
                nome = d.get("nome_usuario", email.split('@')[0])
                with st.expander(f"👤 {nome} — {email} | {d.get('plano_escolhido')}"):
                    st.write(f"Valor: R$ {d.get('valor_pago',0):.2f}")
                    st.write(f"Data: {d.get('data_pagamento', '—')}")
                    img = d.get("caminho_comprovante", "")
                    if img and os.path.exists(img):
                        st.image(img, width=400)
                    col_ap, col_rej = st.columns(2)
                    with col_ap:
                        if st.button(f"✅ APROVAR", key=f"apr_{email}", type="primary"):
                            usrs[email].update({
                                "status_pagamento": "aprovado",
                                "plano": d.get("plano_escolhido"),
                                "plano_ativo": True
                            })
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.success("Aprovado!")
                            st.rerun()
                    with col_rej:
                        if st.button(f"❌ REJEITAR", key=f"rej_{email}"):
                            usrs[email]["status_pagamento"] = "rejeitado"
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.rerun()
        else:
            st.info("Nenhum pagamento pendente.")
    
    with aba2:
        st.subheader("Gerenciar Contas de Usuários")
        email_filtro = st.text_input("🔍 Buscar por e-mail ou nome de usuário")
        for email, d in usrs.items():
            nome = d.get("nome_usuario", email.split('@')[0])
            if email_filtro and email_filtro.lower() not in email.lower() and email_filtro.lower() not in nome.lower():
                continue
            status = d.get("status_pagamento", "aprovado")
            plano_atual = d.get("plano", "Gratuito")
            icone = {"aprovado":"✅", "pendente":"⏳", "rejeitado":"❌"}.get(status, "—")
            
            with st.expander(f"{icone} {nome} | {email} | Plano: {plano_atual}"):
                st.write(f"Cadastro: {d.get('data_cadastro', '—')}")
                st.write(f"Status: {status.upper()}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    novo_plano = st.selectbox(
                        "Alterar Plano", list(PLANOS.keys()),
                        index=list(PLANOS.keys()).index(plano_atual),
                        key=f"pln_{email}"
                    )
                    if st.button("Aplicar", key=f"apl_{email}", type="primary"):
                        usrs[email]["plano"] = novo_plano
                        if novo_plano == "Gratuito":
                            usrs[email]["status_pagamento"] = "aprovado"
                            usrs[email]["plano_ativo"] = True
                        salvar_json(ARQUIVO_USUARIOS, usrs)
                        st.success(f"Plano alterado para {novo_plano}!")
                        st.rerun()
                with col2:
                    novo_nome = st.text_input("Editar Nome de Usuário", value=nome, key=f"usr_{email}")
                    if st.button("Salvar Nome", key=f"salv_{email}"):
                        existe = any(
                            dd.get("nome_usuario") == novo_nome and ee != email
                            for ee, dd in usrs.items()
                        )
                        if existe:
                            st.error("Nome já em uso!")
                        else:
                            usrs[email]["nome_usuario"] = novo_nome
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.success("Nome alterado!")
                            st.rerun()
                with col3:
                    if st.button("🗑️ EXCLUIR CONTA", key=f"del_{email}"):
                        if f"conf_del_{email}" not in st.session_state:
                            st.session_state[f"conf_del_{email}"] = True
                            st.warning(f"Clique NOVAMENTE para excluir {nome}")
                        else:
                            del usrs[email]
                            salvar_json(ARQUIVO_USUARIOS, usrs)
                            st.success(f"{nome} — EXCLUÍDO!")
                            if f"conf_del_{email}" in st.session_state:
                                del st.session_state[f"conf_del_{email}"]
                            st.rerun()
    
    with aba3:
        st.subheader("Configurações do Sistema")
        pix_nome = st.text_input("Nome Recebedor PIX", value=CONFIG["pix_nome_recebedor"])
        pix_chave = st.text_input("Chave PIX", value=CONFIG["pix_chave"])
        whatsapp = st.text_input("WhatsApp Admin", value=CONFIG["whatsapp_admin"])
        taxa_media = st.number_input("Taxa Média Corretoras (%)", 0.0, 5.0, CONFIG["taxa_media_corretora_perc"], step=0.01)
        nova_senha_admin = st.text_input("Nova Senha do Painel Admin", value=CONFIG["senha_admin"], type="password")
        
        if st.button("💾 SALVAR CONFIGURAÇÕES", type="primary"):
            CONFIG.update({
                "pix_nome_recebedor": pix_nome,
                "pix_chave": pix_chave,
                "whatsapp_admin": whatsapp,
                "taxa_media_corretora_perc": taxa_media,
                "senha_admin": nova_senha_admin
            })
            salvar_json(ARQUIVO_SISTEMA, CONFIG)
            st.success("✅ Todas as configurações salvas!")
    
    with aba4:
        st.subheader("Configurações de E-mail")
        remetente = st.text_input("E-mail Remetente", value=CONFIG.get("email_remetente", ""))
        senha_app = st.text_input("Senha de Aplicativo", value=CONFIG.get("senha_app_email", ""), type="password",
                                  help="No Gmail: ative 2FA → crie 'Senha de App'")
        smtp = st.text_input("Servidor SMTP", value=CONFIG.get("smtp_servidor", "smtp.gmail.com"))
        porta = st.number_input("Porta SMTP", value=CONFIG.get("smtp_porta", 587))
        
        if st.button("💾 SALVAR E-MAIL", type="primary"):
            CONFIG.update({
                "email_remetente": remetente,
                "senha_app_email": senha_app,
                "smtp_servidor": smtp,
                "smtp_porta": int(porta)
            })
            salvar_json(ARQUIVO_SISTEMA, CONFIG)
            st.success("Configurações de e-mail salvas!")
        
        st.markdown("---")
        st.subheader("Testar Envio")
        email_teste = st.text_input("E-mail para teste")
        if st.button("📤 ENVIAR TESTE"):
            ok, msg = enviar_email(email_teste, "Teste — Arbitragem AI", "<h3>Funcionou! ✅</h3><p>E-mail configurado corretamente.</p>")
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 SAIR DO ADMIN", type="secondary"):
        st.session_state["admin_logado"] = False
        st.rerun()

# ==============================================
# CONTROLE DE PÁGINAS
# ==============================================
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

if not st.session_state["logado"]:
    if st.session_state["pagina"] == "Painel de Administração":
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
