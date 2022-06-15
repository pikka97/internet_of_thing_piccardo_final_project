# Middleware python Server fot GSM IOT device


## Description:
Python minimal web REST server
This python program exposes a minimal REST server, with only two response:    
* GET method to receive the data saved on the Sqlite server's database
* POST method to update the data to the server

In case of not debug execution it checks if the api-key is given and it equals to the given one.

Using sqlalchemy, an database ORM it generates the database table if it not exists, using the definition:

    Table(
      'iot_gsm_data', metadata_obj,
      Column('id', Integer, primary_key=True, autoincrement=True),
      Column('volt', Float),
      Column('ampere', Float),
      Column('datetime', DateTime),
      Column('gsm_signal', Integer)
  )

## Usage:
1. To use this server, first generate a python virtual environment using:
    
        python3 -m venv venv

2. Enable the just generated environment using:

        source venv/bin/activate

3. Install the packages using the given `requirements.txt` file:

        pip install -r requirements.txt

4. Set the `FLASK_APP` environment variable to the bash, in which is enable the virtual environment, using the bash command:

        export FLASK_APP=main.py

5. Exec the command `flask run` in the folder of the web server's sources, using the python virtual environment, exec:

        flask run

6. Now the server should be in execution, open on the browser the web page:
        
        http://127.0.0.1:5000