import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

import datetime

SqlAlchemyBase = dec.declarative_base()

__factory = None
__all_models = None


def global_init(db_file, all_models):
    global __factory, __all_models

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    __all_models = all_models
    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


class BaseDataFrame:
    id = sa.Column(sa.UUID, unique=True,
                           primary_key=True, default="00000000-0000-0000-0000-000000000000")
    config_id = sa.Column(sa.Integer, default=-1)
    date = sa.Column(sa.DateTime, default=datetime.datetime.now())
    hostname = sa.Column(sa.String, nullable=False)

    metric_root = sa.Column(sa.String, nullable=False)
    metric_main = sa.Column(sa.String, nullable=False)
    metric_details = sa.Column(sa.String, nullable=True)
