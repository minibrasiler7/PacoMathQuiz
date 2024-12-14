# models.py

from datetime import datetime
from extensions import db, login_manager
from flask_login import UserMixin
from sqlalchemy import Text
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    classes = db.relationship('Class', backref='teacher', lazy=True)
    exercises = db.relationship('Exercise', backref='teacher', lazy=True)
    exercise_groups = db.relationship('ExerciseGroup', backref='teacher', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class_exercises = db.Table('class_exercises',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'), primary_key=True)
)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    students = db.relationship('Student', backref='class_', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    # Ajoutez la relation manquante ici
    competition_stats = db.relationship('CompetitionStudentStat', back_populates='student', cascade="all, delete-orphan")

    def __repr__(self):
        return f"Student('{self.name}', Class ID={self.class_id})"

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    question = db.Column(db.Text, nullable=False)
    exercise_type = db.Column(db.String(20), nullable=False)  # 'qcm', 'vrai_faux', 'reponse_courte'
    choices = db.relationship('Choice', backref='exercise', lazy=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    correct_answer = db.Column(Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Exercise('{self.title}', '{self.exercise_type}')"

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(150), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)

    def __repr__(self):
        return f"Choice('{self.text}', Correct: {self.is_correct})"

class ExerciseGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercises = db.relationship('Exercise', secondary='group_exercises', backref='groups')

    def __repr__(self):
        return f"ExerciseGroup('{self.name}', '{self.date_created}')"

# Table d'association pour la relation many-to-many entre ExerciseGroup et Exercise
group_exercises = db.Table('group_exercises',
    db.Column('group_id', db.Integer, db.ForeignKey('exercise_group.id'), primary_key=True),
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'), primary_key=True)
)

competition_participants = db.Table('competition_participants',
    db.Column('competition_id', db.Integer, db.ForeignKey('competition.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True)
)

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_started = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    group_id = db.Column(db.Integer, db.ForeignKey('exercise_group.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    mode = db.Column(db.String(20), nullable=False)  # 'manuel' ou 'automatique'
    code = db.Column(db.Integer, nullable=True)  # Code pour le mode 'automatique'
    competition_started = db.Column(db.Boolean, default=False)
    current_exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=True)

    # Nouveaux champs
    current_student_index = db.Column(db.Integer, default=0)
    used_exercise_ids = db.Column(db.Text, default='[]')  # JSON list of exercise IDs
    active_student_ids = db.Column(db.Text, default='[]')  # JSON list of active student IDs

    group = db.relationship('ExerciseGroup', backref='competitions')
    class_ = db.relationship('Class', backref='competitions')
    participants = db.relationship('Student', secondary=competition_participants, backref='competitions')
    student_stats = db.relationship('CompetitionStudentStat', back_populates='competition', cascade="all, delete-orphan")
    current_exercise = db.relationship('Exercise', backref='current_competition', lazy=True)
    last_player_chances = db.Column(db.Integer, default=1)
    def get_active_student_ids(self):
        """Retourne une liste des IDs des étudiants actuellement actifs dans la compétition."""
        if self.active_student_ids:
            try:
                return json.loads(self.active_student_ids)
            except json.JSONDecodeError:
                print(f"Erreur de décodage JSON pour active_student_ids: {self.active_student_ids}")
                return []
        return []

    def get_current_student_id(self):
        """Retourne l'ID de l'étudiant dont c'est le tour."""
        active_student_ids = self.get_active_student_ids()
        if active_student_ids and 0 <= self.current_student_index < len(active_student_ids):
            return active_student_ids[self.current_student_index]
        return None

    def __repr__(self):
        return f"Competition('{self.group.name}', Mode: '{self.mode}')"

class CompetitionStudentStat(db.Model):
    __tablename__ = 'competition_student_stats'
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    correct_answers = db.Column(db.Integer, default=0, nullable=False)

    competition = db.relationship('Competition', back_populates='student_stats')
    student = db.relationship('Student', back_populates='competition_stats')

    def __repr__(self):
        return f"CompetitionStudentStat(Competition ID={self.competition_id}, Student ID={self.student_id}, Correct Answers={self.correct_answers})"
