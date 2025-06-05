from app import create_app

# import app.models.database as database
# database.init_db()

app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
