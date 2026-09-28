# gym management zcode

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set a private `SECRET_KEY` and PostgreSQL credentials.
4. Create the PostgreSQL database named by `DATABASE_NAME`.
5. Apply migrations with `python manage.py migrate`.
6. Start the development server with `python manage.py runserver`.

The application reads `.env` when present. Never commit `.env` or production credentials.

