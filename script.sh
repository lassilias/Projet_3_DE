#!/bin/bash
wget https://raw.githubusercontent.com/martj42/international_results/master/results.csv
wget https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv
make build
docker volume create shared_volume
docker-compose up -d
until [ "`docker inspect -f {{.State.Running}} a_dataBase_1 `" == "true" ]; do
    sleep 0.1;
done;
until [ "`docker inspect -f {{.State.Running}} test_container_test`" == "true" ]; do
    sleep 0.1;
done;
./wait-for-it.sh a_dataBase_1:3333 -- echo "database is up and running"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU extract_and_transform 2021-01-01"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU create_db_mysql 2021-01-01"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU mapping_pandas_sql 2021-01-01"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU create_table_mysql_external_file 2021-01-01"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU create_table_mysql_external_file2 2021-01-01"
docker exec -it test_container_test  bash -c "airflow tasks test etl_LASSOULI_MOUJOU create_table_mysql_external_file3 2021-01-01"
docker exec -i a_dataBase_1 mysql -u root -psupersecret < dummy.sql
docker exec -it  test_container_test  bash -c "python3 main.py"

