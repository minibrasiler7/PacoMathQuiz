#forms.py
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FieldList, FormField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

class ConditionalRadioField(RadioField):
    def pre_validate(self, form):
        # Ne valide le champ que si le type d'exercice est 'vrai_faux'
        if form.exercise_type.data == 'vrai_faux':
            super(ConditionalRadioField, self).pre_validate(form)
        else:
            # Efface les erreurs potentielles
            self.errors = []
            # Définit data à None
            self.data = None

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Adresse Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de Passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmez le Mot de Passe', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')

class LoginForm(FlaskForm):
    email = StringField('Adresse Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de Passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se Connecter')


class ClassForm(FlaskForm):
    name = StringField('Nom de la classe', validators=[DataRequired()])
    submit = SubmitField('Créer la classe')

class StudentForm(Form):
    name = StringField('Nom de l\'élève', validators=[DataRequired()])



class ChoiceForm(FlaskForm):
    text = StringField('Choix')
    is_correct = BooleanField('Correct')

    class Meta:
        csrf = False  # Désactive la protection CSRF pour ce sous-formulaire

class ExerciseForm(FlaskForm):
    title = StringField('Titre de l\'exercice', validators=[DataRequired(), Length(max=150)])
    question = TextAreaField('Question', validators=[DataRequired()])
    exercise_type = SelectField('Type d\'exercice', choices=[
        ('qcm', 'QCM'),
        ('vrai_faux', 'Vrai/Faux'),
        ('reponse_courte', 'Réponse Courte')
    ], validators=[DataRequired()])
    choices = FieldList(FormField(ChoiceForm), min_entries=2, max_entries=4)
    vrai_faux_answer = ConditionalRadioField('Réponse Correcte', choices=[('Vrai', 'Vrai'), ('Faux', 'Faux')])
    correct_answers = FieldList(StringField('Réponse Correcte'), min_entries=1, max_entries=10)  # Utilisé pour vrai/faux ou réponse courte
    submit = SubmitField('Enregistrer l\'exercice')

    def validate(self, extra_validators=None):
        if not super(ExerciseForm, self).validate():
            return False

        if self.exercise_type.data == 'qcm':
            # Validation pour QCM
            total_choices = len(self.choices.entries)
            if total_choices < 2:
                self.choices.errors.append('Vous devez fournir au moins 2 choix.')
                return False
            if total_choices > 4:
                self.choices.errors.append('Vous ne pouvez pas avoir plus de 4 choix.')
                return False

            for choice_form in self.choices.entries:
                if not choice_form.text.data.strip():
                    choice_form.text.errors.append('Ce champ ne peut pas être vide.')
                    return False

        elif self.exercise_type.data == 'vrai_faux':
            # Validation pour Vrai/Faux
            if not self.vrai_faux_answer.data:
                self.vrai_faux_answer.errors.append('Vous devez sélectionner "Vrai" ou "Faux".')
                return False

        elif self.exercise_type.data == 'reponse_courte':
            # Validation pour Réponse Courte
            total_answers = len(self.correct_answers.entries)
            if total_answers < 1:
                self.correct_answers.errors.append('Vous devez fournir au moins une réponse.')
                return False
            for answer_form in self.correct_answers.entries:
                if not answer_form.data.strip():
                    answer_form.errors.append('Ce champ ne peut pas être vide.')
                    return False

        else:
            return False
        return True


class ExerciseGroupForm(FlaskForm):
    name = StringField('Nom du groupe', validators=[DataRequired()])
    submit = SubmitField('Enregistrer le groupe')


class CompetitionForm(FlaskForm):
    group_id = SelectField('Sélectionnez un Groupe d\'Exercices', coerce=int, validators=[DataRequired()])
    class_id = SelectField('Sélectionnez une Classe', coerce=int, validators=[DataRequired()])
    mode = RadioField('Mode de Compétition', choices=[('manuel', 'Validation manuelle'), ('automatique', 'Validation Automatique')], validators=[DataRequired()], coerce=str)
    submit = SubmitField('Démarrer la Compétition')


class EmptyForm(FlaskForm):
    submit = SubmitField('Supprimer')


class AssignExercisesForm(FlaskForm):
    submit = SubmitField('Enregistrer')

class ValidateParticipantsForm(FlaskForm):
    submit = SubmitField('Valider les élèves présents')

class CompetitionCodeForm(FlaskForm):
    code = IntegerField('Code de Compétition', validators=[DataRequired()])
    submit = SubmitField('Rejoindre')

class StartCompetitionForm(FlaskForm):
    submit = SubmitField('Démarrer la Compétition')

# forms.py

class MultiStudentForm(FlaskForm):
    students = FieldList(FormField(StudentForm), min_entries=1, max_entries=30)
    add_student = SubmitField('Ajouter un Élève')
    submit = SubmitField('Enregistrer Tous les Élèves')







