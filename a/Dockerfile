FROM ubuntu:20.04
RUN apt update && apt-get install nano ca-certificates libpsl5 libssl1.1 openssl publicsuffix wget && apt install python3-pip libmysqlclient-dev -y && pip3 install apache-airflow && pip3 install apache-airflow-providers-mysql
RUN pip3 install pandas && pip3 install requests && pip3 install pydantic && pip3 install fastapi && pip3 install sqlalchemy && pip3 install uvicorn
RUN pip3 install python-jose[cryptography] && pip3 install install passlib[bcrypt] && pip3 install python-multipart
RUN airflow db init 
RUN airflow users  create --role Admin --username admin --email admin --firstname admin --lastname admin --password admin
WORKDIR ./airflow 
COPY  dags/LASSOULI_dag.py /usr/local/lib/python3.8/dist-packages/airflow/example_dags/
RUN airflow connections add 'my_sql_db' \
    --conn-uri 'mysql://root:supersecret@a_dataBase_1:3306/?local_infile=true'
COPY results.csv /root/airflow/
COPY shootouts.csv /root/airflow/
COPY credential.csv /root/airflow/
ADD main.py .
CMD airflow scheduler -D
CMD airflow webserver -D 
EXPOSE 8080
EXPOSE 8000
