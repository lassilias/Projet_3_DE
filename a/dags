from datetime import timedelta
from datetime import datetime
# L'objet DAG nous sert à instancier notre séquence de tâches.
from airflow import DAG

# On importe les Operators dont nous avons besoin.
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


# Les arguments qui suivent vont être attribués à chaque Operators.
# Il est bien évidemment possible de changer les arguments spécifiquement pour un Operators.
# Vous pouvez vous renseigner sur la Doc d'Airflow des différents paramètres que l'on peut définir.

default_args = {
    "owner": "elyase_and_hana",
    "depends_on_past": False,
    "start_date": datetime(2015, 6, 1),
    "email": ["airflow@airflow.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "mysql_conn_id": "my_sql_db"
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
}

dag = DAG("etl_LASSOULI_MOUJOU", default_args=default_args, schedule_interval=timedelta(1))

import requests
from io import StringIO
import pandas as pd

# Création du DAG

###########################################################extract and transform task ################################################################################
def extract_and_transform(ti):

    df=pd.read_csv('/root/airflow/results.csv')

    df['home_score'] = df['home_score'].fillna(3)
    df['away_score'] = df['away_score'].fillna(3)

    df['home_score'] = df['home_score'].astype('int')
    df['away_score'] = df['away_score'].astype('int')

    df.to_csv('/root/airflow/results.csv',index=False)

    df2 = pd.read_csv('/root/airflow/shootouts.csv')

    df2.to_csv('/root/airflow/shootouts.csv',index=False)


t1 = PythonOperator(
    task_id='extract_and_transform',
    python_callable=extract_and_transform,
    dag=dag
)
#########################################################create database MYSQL task###############################################################################

from airflow.providers.mysql.operators.mysql import MySqlOperator


t2 = MySqlOperator(
    task_id='create_db_mysql',
    sql=r"""SET GLOBAL local_infile=1;CREATE DATABASE IF NOT EXISTS INTERNATIONAL_RESULTS;""",
    dag=dag,
)
#################################################### transfer local files to server location ########################################################################
def dtype_mapping():
    return {'object' : 'TEXT',
        'int64' : 'INT',
        'float64' : 'FLOAT',
        'datetime64' : 'DATETIME',
        'bool' : 'TINYINT',
        'datetime64[ns]' : 'DATETIME',
        'category' : 'TEXT',
        'timedelta[ns]' : 'TEXT'}

def gen_tbl_cols_sql(df):
    dmap = dtype_mapping()
    sql = "pi_db_uid INT AUTO_INCREMENT PRIMARY KEY"
    df1 = df.rename(columns = {"" : "nocolname"})
    hdrs = df1.dtypes.index
    hdrs_list = [(hdr, str(df1[hdr].dtype)) for hdr in hdrs]
    for i, hl in enumerate(hdrs_list):
        sql += " ,{0} {1}".format(hl[0], dmap[hl[1]])
    return sql

def mapping_pandas_sql(ti):

    df=pd.read_csv('/root/airflow/results.csv')
    df['date'] = pd.to_datetime( df['date'] ).dt.date
    tbl_cols_sql = gen_tbl_cols_sql(df)
    print(tbl_cols_sql.replace(',',',\n'))

    df2=pd.read_csv('/root/airflow/shootouts.csv')
    df2['date'] = pd.to_datetime( df2['date'] ).dt.date
    tbl_cols_sql2 = gen_tbl_cols_sql(df2)

    ti.xcom_push(key='nom_col_sql', value=tbl_cols_sql.replace(',',',\n'))
    ti.xcom_push(key='nom_col_sql2', value=tbl_cols_sql2.replace(',',',\n'))


t3 = PythonOperator(
    task_id='mapping_pandas_sql',
    python_callable=mapping_pandas_sql,
    dag=dag,
    do_xcom_push=True
)

#########################################################create table in Database####################################################################

t4 = MySqlOperator(
    task_id='create_table_mysql_external_file',
    sql=r"""USE INTERNATIONAL_RESULTS;
    CREATE TABLE IF NOT EXISTS RESULTS(
    {{ task_instance.xcom_pull(key='nom_col_sql',task_ids='mapping_pandas_sql') }}
    );
    LOAD DATA LOCAL INFILE '/root/airflow/results.csv' INTO TABLE RESULTS
    FIELDS TERMINATED BY ','
    ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS
    (date, home_team, away_team, home_score, away_score,tournament, city, country, neutral)
    ;""",#.format(test=ti.xcom_pull(key='model_accuracy', task_ids=['training_model_A'])),
    dag=dag
)




t5 = MySqlOperator(
    task_id='create_table_mysql_external_file2',
    sql=r"""USE INTERNATIONAL_RESULTS;
    CREATE TABLE IF NOT EXISTS SHOOTOUTS(
    {{ task_instance.xcom_pull(key='nom_col_sql2',task_ids='mapping_pandas_sql') }}
    );
    LOAD DATA LOCAL INFILE '/root/airflow/shootouts.csv' INTO TABLE SHOOTOUTS
    FIELDS TERMINATED BY ','
    ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS
    (date, home_team, away_team, winner)
    ;""",#.format(test=ti.xcom_pull(key='model_accuracy', task_ids=['training_model_A'])),
    dag=dag
)


t6 = MySqlOperator(
    task_id='create_table_mysql_external_file3',
    sql=r"""USE INTERNATIONAL_RESULTS;
    CREATE TABLE IF NOT EXISTS CREDENTIALS(
    Username TEXT ,
    Password TEXT );
    LOAD DATA LOCAL INFILE '/root/airflow/credential.csv' INTO TABLE CREDENTIALS
    FIELDS TERMINATED BY ','
    ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 ROWS
    (Username,Password)
    ;""",#.format(test=ti.xcom_pull(key='model_accuracy', task_ids=['training_model_A'])),
    dag=dag
)


t1 >> t2 >> t3 >> t4 >> t5 >> t6


