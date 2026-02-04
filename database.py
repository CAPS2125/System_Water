from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st

def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

def get_db():
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
