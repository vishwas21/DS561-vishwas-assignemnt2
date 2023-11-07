import sqlalchemy

import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./googleCredentials.json"

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
import socket, struct
import sqlalchemy

class MySqlServer():
    pool = None
    
    def connect_with_connector(self) -> sqlalchemy.engine.base.Engine:
        """
        Initializes a connection pool for a Cloud SQL instance of MySQL.
        
        Uses the Cloud SQL Python Connector package.
        """
        # Note: Saving credentials in environment variables is convenient, but not
        # secure - consider a more secure solution such as
        # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
        # keep secrets safe.

        instance_connection_name = "ds561-visb-assignment:us-central1:ds561-psql-server"
        db_user = "postgres"
        db_pass = "assignmentds561password"
        db_name = "ds561-db"

        ip_type = IPTypes.PRIVATE if os.environ.get("DB_PRIVATE_IP") else IPTypes.PUBLIC

        connector = Connector(ip_type)

        def getconn() -> pg8000.dbapi.Connection:
            conn: pg8000.abapi.Connection = connector.connect(
                instance_connection_name,
                "pg8000",
                user=db_user,
                password=db_pass,
                db=db_name,
            )
            return conn
        
        self.pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            # ...
        )
        return self.pool

    def create_table(self):
        create_stmt = sqlalchemy.text(
            """CREATE TABLE IF NOT EXISTS accesslogs (
            country VARCHAR(64),
            ip BIGINT,
            gender SMALLINT,
            age VARCHAR(16),
            income VARCHAR(32),
            timeofday TIMESTAMP);"""
            )
        with self.pool.connect() as db_conn:
            db_conn.execute(create_stmt)
            db_conn.commit()

    def insert_db(self, contents):
        insert_stmt = sqlalchemy.text(
            f"""INSERT INTO accesslogs (country, ip, gender, age, income, timeofday) VALUES ('{contents["country"]}', {contents["ip"]}, {contents["gender"]}, '{contents["age"]}', '{contents["income"]}', '{contents["timeofday"]}');""",
        )

        with self.pool.connect() as db_conn:
            db_conn.execute(insert_stmt)
            db_conn.commit()

    def retrieve_db(self):
        query_stmt = sqlalchemy.text("SELECT * from accesslogs")
        with self.pool.connect() as db_conn:
            result = db_conn.execute(query_stmt).fetchall()
            return result
    
    def execute_query(self, query_stmt):
        return pd.read_sql(query_stmt, self.pool)

    def ip2long(self, ip):
        packedIP = socket.inet_aton(ip)
        return struct.unpack('!L', packedIP)[0]
    
    def long2ip(self, long):
        return socket.inet_ntoa(struct.pack('!L', long))


def main():        
    sqlserver = MySqlServer()
    sqlserver.pool = sqlserver.connect_with_connector()

    data_frame = sqlserver.execute_query("SELECT country, ip FROM accesslogs")

    data_frame['ip'] = data_frame['ip'].astype(int).values.reshape(-1, 1)

    X = data_frame['ip']
    y = data_frame['country']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=40)

    country_model = RandomForestClassifier(n_estimators=90, random_state=40)
    country_model.fit(X_train, y_train)

    country_model_accuracy = country_model.score(X_test, y_test)
    print(f"Model accuracy: {country_model_accuracy*100:.2f}%")

if __name__ == "__main__":        
    main()