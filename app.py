# ==============================================
# 🛡️ VERIFICAÇÃO DE APROVAÇÃO — BLOQUEIA RECURSOS SE PENDENTE
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
# 📊 PAINEL PRINCIPAL — SEMPRE LIBERADO
# ==============================================
if pagina == "📊 Painel Principal":
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
        1️⃣ Vá em **🔐 Minhas Corretoras** e cole suas chaves API
        2️⃣ Vá em **⚙️ Configurações** e escolha quais moedas monitorar
        3️⃣ Clique em **🔍 Analisar Mercado** para buscar oportunidades
        4️⃣ 💰 Lucre com as diferenças de preço!
        """)
    else:
        st.info("""
        ⏳ **Aguardando aprovação...** Assim que confirmarmos seu pagamento, 
        você poderá acessar todos os recursos! ✅
        """)

# ==============================================
# 🔍 ANALISAR MERCADO — BLOQUEADO SE PENDENTE
# ==============================================
elif pagina == "🔍 Analisar Mercado":
    verificar_aprovacao()  # 🔒 BLOQUEIA AQUI
    st.markdown("<h1>🔍 Análise de Mercado em Tempo Real</h1>", unsafe_allow_html=True)
    # ... resto do código ...

# ==============================================
# 🔐 MINHAS CORRETORAS — BLOQUEADO SE PENDENTE
# ==============================================
elif pagina == "🔐 Minhas Corretoras":
    verificar_aprovacao()  # 🔒 BLOQUEIA AQUI
    st.markdown("<h1>🔐 Configuração de Corretoras</h1>", unsafe_allow_html=True)
    # ... resto do código ...

# ==============================================
# ⚙️ CONFIGURAÇÕES — BLOQUEADO SE PENDENTE
# ==============================================
elif pagina == "⚙️ Configurações":
    verificar_aprovacao()  # 🔒 BLOQUEIA AQUI
    st.markdown("<h1>⚙️ Suas Configurações</h1>", unsafe_allow_html=True)
    # ... resto do código ...

# ==============================================
# 💳 MEU PLANO — SEMPRE LIBERADO
# ==============================================
elif pagina == "💳 Meu Plano":
    st.markdown("<h1>💳 Gerenciar Assinatura</h1>", unsafe_allow_html=True)
    # ... resto do código ...
