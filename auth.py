"""
pytrain/auth.py
Autenticação, sessão e perfil de usuário via Supabase.
"""

import streamlit as st
import time
from datetime import datetime


# ── Cookies helpers ────────────────────────────────────────────────────────────

def cookie_get(cookies, key: str) -> str:
    try:
        val = cookies[key]
        return val if val else ""
    except Exception:
        return ""


def cookie_set(cookies, key: str, val: str):
    try:
        cookies[key] = val
        cookies.save()
    except Exception:
        pass


# ── Login / Logout ─────────────────────────────────────────────────────────────

def fazer_login(supabase, cookies, email: str, senha: str) -> bool:
    """Autentica com email/senha, salva tokens na session e no cookie."""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id":    res.user.id,
            "email": res.user.email,
            "nome":  res.user.user_metadata.get("nome", email.split("@")[0]),
        }
        cookie_set(cookies, "rt", res.session.refresh_token)
        return True
    except Exception:
        st.error("Email ou senha incorretos.")
        return False


def restaurar_sessao(supabase, cookies) -> bool:
    """Tenta restaurar sessão a partir do refresh token salvo em cookie."""
    if st.session_state.get("sessao_restaurada"):
        return False
    st.session_state.sessao_restaurada = True

    rt = cookie_get(cookies, "rt")
    if not rt:
        return False
    try:
        res = supabase.auth.refresh_session(rt)
        if not res or not res.session or not res.user:
            cookie_set(cookies, "rt", "")
            return False
        st.session_state.access_token  = res.session.access_token
        st.session_state.refresh_token = res.session.refresh_token
        st.session_state.usuario = {
            "id":    res.user.id,
            "email": res.user.email,
            "nome":  res.user.user_metadata.get("nome", res.user.email.split("@")[0]),
        }
        cookie_set(cookies, "rt", res.session.refresh_token)
        return True
    except Exception:
        cookie_set(cookies, "rt", "")
        return False


def fazer_logout(supabase, cookies, defaults: dict):
    """Limpa cookie, encerra sessão Supabase e reseta session_state."""
    cookie_set(cookies, "rt", "")
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k, v in defaults.items():
        st.session_state[k] = v
    st.rerun()


# ── Perfil ─────────────────────────────────────────────────────────────────────

def verificar_perfil(supabase, uid: str) -> bool:
    """Retorna True se o perfil do usuário tem telefone e cidade preenchidos."""
    try:
        res = supabase.table("perfis").select("telefone,cidade").eq("user_id", uid).execute()
        return bool(res.data and res.data[0].get("telefone") and res.data[0].get("cidade"))
    except Exception:
        return False