from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st

def get_engine():
    return create_engine(st.secrets["databaseurl"])

def get_db():
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
