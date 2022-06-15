from flask import Flask, request, jsonify, Response


from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table, Column, Integer, Float, DateTime, insert, select
import pymysql
pymysql.install_as_MySQLdb()



API_KEY = ''
DB_URL = "sqlite:///testing.db"

db_engine = create_engine(DB_URL, echo=True, future=True)

def init_table_db(db_engine):
  metadata_obj = MetaData()
  data_table = Table(
      'iot_gsm_data', metadata_obj,
      Column('id', Integer, primary_key=True, autoincrement=True),
      Column('volt', Float),
      Column('ampere', Float),
      Column('datetime', DateTime),
      Column('gsm_signal', Integer)
  )
  #Create the table only if it doesn't exist
  metadata_obj.create_all(db_engine)
  return data_table

DEBUG = True


DATETIME_FORMAT = '%d/%m/%y,%H:%M:%S'
UN_AUTH_RESPONSE = Response(response="Unauthorized", status=401)

app = Flask(__name__)
data_table = init_table_db(db_engine)


def is_authenticated(request):
  api_key = request.headers.get('api_key', None)
  return api_key != None and api_key == API_KEY




@app.route('/', methods=['GET', 'POST'])
def home():
    if not DEBUG and not is_authenticated(): return UN_AUTH_RESPONSE

    if request.method == 'GET':
        with db_engine.connect() as conn:
          stmt = select(data_table).order_by(data_table.columns.id.desc())
          data = conn.execute(stmt).first()

        print('db data is:', data)

        str_date = data[3].strftime(DATETIME_FORMAT)
        return jsonify({
         "amper" : data[2],
         "data" : str_date,
         "signal" : data[4],
         "volt" : data[1]
      })

    if request.method == 'POST':
      print('json received: ' + str(request.json))
      data = request.json['msg']
      for d in data:
        volt, ampere, gsm_signal, timestamp = d['volt'], d['amper'], d['signal'], d['data']
        parsed_datetime = datetime.strptime(timestamp, DATETIME_FORMAT)
        insert_data_stmt = insert(data_table).values(volt=volt, ampere=ampere, datetime=parsed_datetime, gsm_signal=gsm_signal)
        with db_engine.connect() as conn:
            result = conn.execute(insert_data_stmt)
            print('the result of the insert is:' + str(result))
            conn.commit()
      return Response(response='', status=204)