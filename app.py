import streamlit as st
from agent import run_agent

st.set_page_config(page_title='AutoStream Agent', layout='wide')
st.title('AutoStream AI Sales Agent')

if 'history' not in st.session_state:
    st.session_state.history = []
if 'agent_state' not in st.session_state:
    st.session_state.agent_state = {
        'lead_mode': False,
        'name': None,
        'email': None,
        'platform': None,
    }


for role, msg in st.session_state.history:
    with st.chat_message(role):
        st.write(msg)

prompt = st.chat_input('Ask about plans, pricing, or sign up...')

if prompt:
    st.session_state.history.append(('user', prompt))
    with st.chat_message('user'):
        st.write(prompt)

    reply = run_agent(prompt, st.session_state.agent_state)
    st.session_state.history.append(('assistant', reply))
    with st.chat_message('assistant'):
        st.write(reply)