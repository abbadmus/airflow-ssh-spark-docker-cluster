from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
# from airflow.providers.ssh.hooks.ssh import SSHHook


from datetime import datetime, timedelta
import requests


default_args = {
    "owner": "airflow",
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "admin@localhost.com",
    "reties": 1,
    "retry_delay": timedelta(minutes=5)
}


def download_rate():
    res = requests.get(
        "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo")
    with open("./dags/data/res.json", "w") as sd:
        sd.write(res.text)


spark_submit_command = """cd / && \
    spark/bin/spark-submit --deploy-mode client \
    --master spark://9d493855fcb2:7077 --verbose \
    --supervise /opt/spark-apps/out.jar /opt/spark-data/movies.json \
    /opt/spark-data/goodComedies 
    """
# sshHook = SSHHook(remote_host='172.22.0.8', username='root', password="docker") or ssh_conn_id


with DAG(dag_id="forex_data_pipeline",
         start_date=datetime(2021, 1, 1),
         schedule_interval="@daily",
         default_args=default_args, catchup=False) as dag:

    is_forex_rate_available = HttpSensor(
        task_id="is_forex_rate_available",
        http_conn_id="forex_api",
        endpoint="query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey=demo",
        response_check=lambda response: "Meta Data" in response.text,
        poke_interval=5,
        timeout=20
    )

    is_file_available = FileSensor(
        task_id="is_file_available",
        fs_conn_id="file_location",
        filepath="query.json",
        poke_interval=5,
        timeout=20
    )

    download_stock_rate = PythonOperator(
        task_id="download_stock_rate",
        python_callable=download_rate
    )

    run_spark_job = SparkSubmitOperator(
        task_id="run_spark_job",
        conn_id="spark_connection",
        application=r"./dags/data/out.jar",
        application_args=[r"./dags/data/movies.json",
                          r"./dags/data/goodmovies"],
        verbose=False,
    )

    ssh_spark_submit = SSHOperator(
        task_id="ssh_spark_submit",
        ssh_conn_id="ssh_connetion",
        # ssh_hook=sshHook,
        command=spark_submit_command
    )

    # is_forex_rate_available.set_downstream(ssh_spark_submit)

    is_forex_rate_available >> download_stock_rate >> is_file_available >> ssh_spark_submit


# ./bin/spark-submit --deploy-mode client --master spark://2def3ad28ade:7077 --verbose --supervise /opt/spark-apps/out.jar /opt/spark-data/movies.json /opt/spark-data/goodComedies
# airflow tasks test forex_data_pipeline ssh_spark_submit
