import sqlalchemy as sa
from .db import Base
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func

class FAQ(Base):
    __tablename__ = 'faq'
    id = sa.Column(sa.Integer, primary_key=True)
    question = sa.Column(sa.Text, nullable=False)
    answer_template = sa.Column(sa.Text, nullable=False)
    tags = sa.Column(sa.Text)
    embeddings = sa.Column(JSON, nullable=True)
    created_at = sa.Column(sa.DateTime, server_default=func.now())

class Feedback(Base):
    __tablename__ = 'feedback'
    id = sa.Column(sa.Integer, primary_key=True)
    input_text = sa.Column(sa.Text)
    useful = sa.Column(sa.Boolean)
    comment = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime, server_default=func.now())

class EvaluateRequest(Base):
    generated: str
    reference: str

