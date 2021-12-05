# Projet 3 DE

This project consists in instantiating a database from the dataset: https://github.com/martj42/international_results

This dataset includes 42,899 results of international football matches starting from the very first official match in 1872 up to 2021.

A Fastapi api was deployed to query the database.

script.sh do these things in order:

- downloading the source files 
- building the container my_image:latest containing ubuntu image where Airflow( used as ETL tool) and Fastapi api will turn
- docker-compose up this last container with mysql:8.0
