from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True)
    nombre_completo = Column(String)
    telefono = Column(String)
    correo = Column(String)
    direccion = Column(String)

    servicios = relationship("Servicio", back_populates="cliente")


class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(String, primary_key=True)
    cliente_id = Column(String, ForeignKey("clientes.id"))

    nombre_servicio = Column(String)
    tipo_servicio = Column(String)
    tarifa = Column(Float)
    lectura_anterior = Column(Integer)
    adeudo = Column(Float, default=0)

    ultimo_pago = Column(Date)
    proximo_pago = Column(Date)
    estado = Column(String)

    cliente = relationship("Cliente", back_populates="servicios")
    pagos = relationship("Pago", back_populates="servicio")


class Pago(Base):
    __tablename__ = "pagos"

    id = Column(String, primary_key=True)
    servicio_id = Column(String, ForeignKey("servicios.id"))
    fecha_pago = Column(Date)
    monto = Column(Float)
    meses_pagados = Column(Integer)
    metodo_pago = Column(String)

    servicio = relationship("Servicio", back_populates="pagos")