from main import Run, User, Base, db_session, engine
import mysql.connector


def create_db():
    my_db = mysql.connector.connect(host="localhost", user="root", passwd="password")
    my_cursor = my_db.cursor()
    my_cursor.execute("CREATE DATABASE tables")
    print("creating database...")
    my_cursor.execute("SHOW DATABASES")
    for db in my_cursor:
        print(db)


def drop_all():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    print("clearing database...")


if __name__ == "__main__":
    # clear_users()
    drop_all()
    # create_db()
    print("done")
