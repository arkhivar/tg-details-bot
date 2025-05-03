import os
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Setup Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "telegram_bot_secret")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy with a custom model class
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Define database models
class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    members_count = db.Column(db.Integer, nullable=True)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'members_count': self.members_count,
            'added_date': self.added_date.strftime('%Y-%m-%d %H:%M:%S') if self.added_date else None,
            'last_activity': self.last_activity.strftime('%Y-%m-%d %H:%M:%S') if self.last_activity else None
        }

# Create database tables
with app.app_context():
    db.create_all()

# Web routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chats')
def get_chats():
    chats = Chat.query.order_by(Chat.last_activity.desc()).all()
    return jsonify([chat.to_dict() for chat in chats])

@app.route('/api/stats')
def get_stats():
    total_chats = Chat.query.count()
    groups = Chat.query.filter(Chat.type.in_(['group', 'supergroup'])).count()
    channels = Chat.query.filter_by(type='channel').count()
    private_chats = Chat.query.filter_by(type='private').count()
    
    return jsonify({
        'total': total_chats,
        'groups': groups,
        'supergroups': Chat.query.filter_by(type='supergroup').count(),
        'channels': channels,
        'private': private_chats
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)