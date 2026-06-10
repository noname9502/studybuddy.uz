from app import create_app
from app.extensions import db
import os

app = create_app()

if __name__ == '__main__':
    # Seed database if it doesn't exist
    db_path = 'instance/studybuddy.db'
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            from seed import seed
            seed()
    
    app.run(debug=True)
