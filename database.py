# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

class DatabaseHandler:
    """
    A class for handling database operations using SQLAlchemy.

    Attributes:
        engine (sqlalchemy.engine.base.Engine): The SQLAlchemy database engine.
        Session (sqlalchemy.orm.session.Session): A session class for database interactions.

    Methods:
        __init__(self, db_url): Initializes the DatabaseHandler with the given database URL.
        execute_query(self, query, params): Executes an SQL query with parameters and returns the result.
    """

    def __init__(self, db_url):
        """
        Initializes a new DatabaseHandler instance.

        Parameters:
            db_url (str): The URL for connecting to the PostgreSQL database.
        """
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def execute_query(self, query, params):
        """
        Executes an SQL query with parameters and returns the result.

        Parameters:
            query (str): The SQL query to execute.
            params (dict): A dictionary containing parameter values for the query.

        Returns:
            list: A list of rows resulting from the query.
        """
        with self.Session() as session:
            return session.execute(text(query), params).fetchall()
