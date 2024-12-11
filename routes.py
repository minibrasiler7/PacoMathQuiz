# routes.py
import json
from app import app, db, bcrypt
from forms import RegistrationForm, LoginForm, ExerciseGroupForm, CompetitionForm, EmptyForm, AssignExercisesForm, \
    ValidateParticipantsForm, CompetitionCodeForm
from flask_login import login_user, current_user, logout_user, login_required
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from forms import ClassForm, StudentForm
from models import User, Exercise, Choice, Class, Student, ExerciseGroup, Competition, CompetitionStudentStat
from forms import ExerciseForm
import random
from flask import session
from forms import StartCompetitionForm
from random import randint
from forms import MultiStudentForm



@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Accueil')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hachage du mot de passe
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Création de l'utilisateur
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        # Ajout à la base de données
        db.session.add(user)
        db.session.commit()
        flash('Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Inscription', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        # Vérification de l'utilisateur
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Connexion de l'utilisateur
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Vous êtes maintenant connecté.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Échec de la connexion. Veuillez vérifier votre email et mot de passe.', 'danger')
    return render_template('login.html', title='Connexion', form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('home'))


@app.route("/classes")
@login_required
def classes():
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('classes.html', classes=classes)

@app.route("/class/new", methods=['GET', 'POST'])
@login_required
def new_class():
    form = ClassForm()
    if form.validate_on_submit():
        new_class = Class(name=form.name.data, teacher=current_user)
        db.session.add(new_class)
        db.session.commit()
        flash('La classe a été créée avec succès.', 'success')
        return redirect(url_for('classes'))
    return render_template('create_class.html', title='Nouvelle Classe', form=form)

@app.route("/class/<int:class_id>")
@login_required
def class_detail(class_id):
    class_instance = Class.query.get_or_404(class_id)
    if class_instance.teacher != current_user:
        abort(403)
    students = Student.query.filter_by(class_id=class_instance.id).all()
    return render_template('class_detail.html', class_instance=class_instance, students=students)

@app.route("/class/<int:class_id>/update", methods=['GET', 'POST'])
@login_required
def update_class(class_id):
    class_instance = Class.query.get_or_404(class_id)
    if class_instance.teacher != current_user:
        abort(403)
    form = ClassForm()
    if form.validate_on_submit():
        class_instance.name = form.name.data
        db.session.commit()
        flash('La classe a été mise à jour.', 'success')
        return redirect(url_for('classes'))
    elif request.method == 'GET':
        form.name.data = class_instance.name
    return render_template('create_class.html', title='Modifier la Classe', form=form)

@app.route("/class/<int:class_id>/delete", methods=['POST'])
@login_required
def delete_class(class_id):
    class_instance = Class.query.get_or_404(class_id)
    if class_instance.teacher != current_user:
        abort(403)
    db.session.delete(class_instance)
    db.session.commit()
    flash('La classe a été supprimée.', 'success')
    return redirect(url_for('classes'))

# routes.py

@app.route("/class/<int:class_id>/student/new", methods=['GET', 'POST'])
@login_required
def new_students(class_id):
    class_instance = Class.query.get_or_404(class_id)
    if class_instance.teacher != current_user:
        abort(403)

    form = MultiStudentForm()

    if form.validate_on_submit():
        for student_form in form.students.entries:
            student_name = student_form.form.name.data.strip()
            if student_name:  # Vérifie que le nom n'est pas vide
                student = Student(name=student_name, class_id=class_instance.id)
                db.session.add(student)
        db.session.commit()
        flash('Les élèves ont été ajoutés avec succès.', 'success')
        return redirect(url_for('class_detail', class_id=class_id))

    return render_template('create_student.html', title='Nouvel Élève', form=form, class_instance=class_instance)


@app.route("/student/<int:student_id>/delete", methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    class_instance = Class.query.get(student.class_id)
    if class_instance.teacher != current_user:
        abort(403)
    db.session.delete(student)
    db.session.commit()
    flash('L\'élève a été supprimé.', 'success')
    return redirect(url_for('class_detail', class_id=class_instance.id))

@app.route("/exercises")
@login_required
def exercises():
    exercises = Exercise.query.filter_by(teacher_id=current_user.id).all()
    return render_template('exercises.html', exercises=exercises)

@app.route("/exercise/new", methods=['GET', 'POST'])
@login_required
def new_exercise():
    form = ExerciseForm()
    if form.validate_on_submit():
        exercise = Exercise(
            title=form.title.data,
            question=form.question.data,
            exercise_type=form.exercise_type.data,
            teacher=current_user
        )
        if form.exercise_type.data == 'qcm':
            for choice_form in form.choices.entries:
                choice = Choice(
                    text=choice_form.text.data,
                    is_correct=choice_form.is_correct.data,
                    exercise=exercise
                )
                db.session.add(choice)

        elif form.exercise_type.data == "vrai_faux":
            exercise.correct_answer = form.vrai_faux_answer.data
        elif form.exercise_type.data == 'reponse_courte':
            answers = [answer.data.strip() for answer in form.correct_answers.entries]
            exercise.correct_answer = json.dumps(answers)  # Convertir en JSON
        else:
            exercise.correct_answer = form.correct_answer.data
        db.session.add(exercise)
        db.session.commit()
        flash('L\'exercice a été créé avec succès.', 'success')
        return redirect(url_for('exercises'))
    else:
        print(form.errors)  # Pour le débogage
    return render_template('create_exercise.html', title='Nouvel Exercice', form=form)

@app.route("/exercise/<int:exercise_id>")
@login_required
def exercise_detail(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    if exercise.teacher != current_user:
        abort(403)
    return render_template('exercise_detail.html', exercise=exercise)

@app.route("/exercise/<int:exercise_id>/update", methods=['GET', 'POST'])
@login_required
def update_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    if exercise.teacher != current_user:
        abort(403)
    form = ExerciseForm()
    if form.validate_on_submit():
        exercise.title = form.title.data
        exercise.question = form.question.data
        exercise.exercise_type = form.exercise_type.data
        # Mise à jour des choix pour le QCM
        if exercise.exercise_type == 'qcm':
            # Supprimer les anciens choix
            Choice.query.filter_by(exercise_id=exercise.id).delete()
            for choice_form in form.choices.entries:
                choice = Choice(text=choice_form.form.text.data, is_correct=choice_form.form.is_correct.data, exercise=exercise)
                db.session.add(choice)
            exercise.correct_answer = None
        else:
            exercise.correct_answer = form.correct_answer.data
            Choice.query.filter_by(exercise_id=exercise.id).delete()
        db.session.commit()
        flash('L\'exercice a été mis à jour.', 'success')
        return redirect(url_for('exercises'))
    elif request.method == 'GET':
        form.title.data = exercise.title
        form.question.data = exercise.question
        form.exercise_type.data = exercise.exercise_type
        if exercise.exercise_type == 'qcm':
            # Pré-remplir les choix existants
            choices = exercise.choices
            for i, choice in enumerate(choices):
                if i < len(form.choices.entries):
                    form.choices.entries[i].form.text.data = choice.text
                    form.choices.entries[i].form.is_correct.data = choice.is_correct
                else:
                    break
        else:
            form.correct_answer.data = exercise.correct_answer
    return render_template('create_exercise.html', title='Modifier l\'Exercice', form=form)

@app.route("/exercise/<int:exercise_id>/delete", methods=['POST'])
@login_required
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    if exercise.teacher != current_user:
        abort(403)
    db.session.delete(exercise)
    db.session.commit()
    flash('L\'exercice a été supprimé.', 'success')
    return redirect(url_for('exercises'))



@app.route("/exercise_groups")
@login_required
def exercise_groups():
    groups = ExerciseGroup.query.filter_by(teacher_id=current_user.id).all()
    form = EmptyForm()
    return render_template('exercise_groups.html', groups=groups, form=form)

@app.route("/exercise_group/new", methods=['GET', 'POST'])
@login_required
def new_exercise_group():
    form = ExerciseGroupForm()
    if form.validate_on_submit():
        group = ExerciseGroup(name=form.name.data, teacher=current_user)
        db.session.add(group)
        db.session.commit()
        flash('Le groupe d\'exercices a été créé avec succès.', 'success')
        return redirect(url_for('exercise_groups'))
    return render_template('create_exercise_group.html', title='Nouveau Groupe d\'Exercices', form=form)

@app.route("/exercise_group/<int:group_id>")
@login_required
def exercise_group_detail(group_id):
    group = ExerciseGroup.query.get_or_404(group_id)
    if group.teacher != current_user:
        abort(403)
    return render_template('exercise_group_detail.html', group=group)

@app.route("/exercise_group/<int:group_id>/update", methods=['GET', 'POST'])
@login_required
def update_exercise_group(group_id):
    group = ExerciseGroup.query.get_or_404(group_id)
    if group.teacher != current_user:
        abort(403)
    form = ExerciseGroupForm()
    if form.validate_on_submit():
        group.name = form.name.data
        db.session.commit()
        flash('Le groupe d\'exercices a été mis à jour.', 'success')
        return redirect(url_for('exercise_group_detail', group_id=group.id))
    elif request.method == 'GET':
        form.name.data = group.name
    return render_template('create_exercise_group.html', title='Modifier le Groupe d\'Exercices', form=form)

@app.route("/exercise_group/<int:group_id>/delete", methods=['POST'])
@login_required
def delete_exercise_group(group_id):
    group = ExerciseGroup.query.get_or_404(group_id)
    if group.teacher != current_user:
        abort(403)
    db.session.delete(group)
    db.session.commit()
    flash('Le groupe d\'exercices a été supprimé.', 'success')
    return redirect(url_for('exercise_groups'))

@app.route("/exercise_group/<int:group_id>/assign_exercises", methods=['GET', 'POST'])
@login_required
def assign_exercises_to_group(group_id):
    group = ExerciseGroup.query.get_or_404(group_id)
    if group.teacher != current_user:
        abort(403)
    form = AssignExercisesForm()
    if form.validate_on_submit():
        selected_exercises = request.form.getlist('exercise_ids')
        group.exercises = Exercise.query.filter(Exercise.id.in_(selected_exercises)).all()
        db.session.commit()
        flash('Les exercices ont été assignés au groupe.', 'success')
        return redirect(url_for('exercise_group_detail', group_id=group_id))
    else:
        exercises = Exercise.query.filter_by(teacher_id=current_user.id).all()
        return render_template('assign_exercises_to_group.html', group=group, exercises=exercises, form=form)


@app.route("/competition/new", methods=['GET', 'POST'])
@login_required
def new_competition():
    form = CompetitionForm()
    # Peupler les choix du formulaire
    form.group_id.choices = [(group.id, group.name) for group in ExerciseGroup.query.filter_by(teacher_id=current_user.id).all()]
    form.class_id.choices = [(classe.id, classe.name) for classe in Class.query.filter_by(teacher_id=current_user.id).all()]
    if form.validate_on_submit():
        group_id = form.group_id.data
        class_id = form.class_id.data
        mode = form.mode.data

        group = ExerciseGroup.query.get_or_404(group_id)
        classe = Class.query.get_or_404(class_id)

        print("DEBUG: mode =", mode)  # Ligne de débogage

        if mode == 'automatique':
            # Générer un code aléatoire entre 100000 et 999999
            code = randint(100000, 999999)
        else:
            code = None

        # Créer une nouvelle compétition
        competition = Competition(group=group, class_=classe, mode=mode, code=code)
        db.session.add(competition)
        db.session.commit()
        flash('La compétition a été démarrée avec succès.', 'success')
        return redirect(url_for('competition_detail', competition_id=competition.id))
    return render_template('new_competition.html', form=form)

@app.route("/competition/<int:competition_id>", methods=['GET', 'POST'])
@login_required
def competition_detail(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    if competition.group.teacher != current_user:
        abort(403)

    classe = competition.class_
    students = classe.students  # Liste des élèves de la classe

    if competition.mode == 'manuel':
        form = ValidateParticipantsForm()
        if form.validate_on_submit():
            # Récupérer les élèves sélectionnés
            selected_student_ids = request.form.getlist('student_ids')
            competition.participants = Student.query.filter(Student.id.in_(selected_student_ids)).all()
            print("DEBUG: competition.participants =", [s.name for s in competition.participants])
            print("DEBUG: selected_student_ids =", selected_student_ids)
            db.session.commit()
            flash('Les élèves présents ont été enregistrés.', 'success')
            # Rediriger vers la page de démarrage de la compétition
            return redirect(url_for('start_competition', competition_id=competition.id))
        return render_template('competition_detail.html', competition=competition, students=students, form=form)
    else:  # Mode 'automatique'
        form = StartCompetitionForm()
        if form.validate_on_submit():
            if competition.participants:
                flash('La compétition est prête à démarrer.', 'success')
                return redirect(url_for('start_competition', competition_id=competition.id))
            else:
                flash('Aucun élève n\'a rejoint la compétition.', 'warning')
        return render_template('competition_detail.html', competition=competition, students=students, form=form)


@app.route("/competition/<int:competition_id>/start", methods=['GET', 'POST'])
@login_required
def start_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)

    if competition.active_student_ids:
        competition.competition_started = True
        db.session.commit()
        active_students_list = json.loads(competition.active_student_ids)
    else:
        active_students_list = []

    if not active_students_list:
        active_students = [student.id for student in competition.participants]
        competition.active_student_ids = json.dumps(active_students)
        competition.current_student_index = 0
        competition.competition_started = True  # Marquer comme démarré
        db.session.commit()
        flash(f'Élèves actifs initialisés : {active_students}', 'info')

    # Si le mode est automatique, rediriger vers la page de l'enseignant (teacher_view_competition)
    # Sinon, rediriger vers run_competition
    if competition.mode == 'automatique':
        return redirect(url_for('teacher_view_competition', competition_id=competition.id))
    else:
        return redirect(url_for('run_competition', competition_id=competition.id))



@app.route("/competition/join", methods=['GET', 'POST'])
def join_competition():
    form = CompetitionCodeForm()

    if form.validate_on_submit():
        code = form.code.data
        competition = Competition.query.filter_by(code=code).first()
        if competition:
            return redirect(url_for('select_student', competition_id=competition.id))
        else:
            flash('Code de compétition invalide.', 'danger')
    return render_template('join_competition.html', form=form)

@app.route("/competition/<int:competition_id>/select_student", methods=['GET', 'POST'])
def select_student(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    if competition.mode != 'automatique':
        flash('Cette compétition n\'est pas en mode automatique.', 'danger')
        return redirect(url_for('join_competition'))

    classe = competition.class_
    students = classe.students

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student = Student.query.get(student_id)

        if student and student.class_id == classe.id:
            # Vérifier si l'élève est déjà inscrit à la compétition
            if student in competition.participants:
                flash('Vous êtes déjà inscrit à cette compétition.', 'info')
            else:
                competition.participants.append(student)
                db.session.commit()
                flash(f'Vous avez rejoint la compétition. Participants actuels : {[s.name for s in competition.participants]}', 'success')
            return redirect(url_for('competition_wait', competition_id=competition.id, student_id=student.id))
        else:
            flash('Sélection invalide.', 'danger')

    return render_template('select_student.html', competition=competition, students=students)

@app.route("/competition/<int:competition_id>/wait/<int:student_id>")
def competition_wait(competition_id, student_id):
    competition = Competition.query.get_or_404(competition_id)
    student = Student.query.get_or_404(student_id)
    session['student_id'] = student.id  # On garde cette ligne pour identifier l'élève
    # On remplace 'competition_wait.html' par 'run_competition_auto_wait.html'
    # Et on passe l'ID de l'élève au template pour que le JS puisse le comparer à current_student_id
    return render_template('run_competition_auto_wait.html', competition=competition, student=student, student_id=student.id, competition_started=competition.competition_started)


def check_answer(exercise, student_answer):
    print("DEBUG: check_answer - exercise_type =", exercise.exercise_type)
    print("DEBUG: check_answer - student_answer =", student_answer)

    if exercise.exercise_type == 'qcm':
        correct_choice = next((choice for choice in exercise.choices if choice.is_correct), None)
        print("DEBUG: check_answer - correct_choice =", correct_choice)
        if correct_choice:
            print("DEBUG: check_answer - correct_choice.id =", correct_choice.id)
            print("DEBUG: check_answer - comparaison =", str(correct_choice.id) == student_answer)
        return str(correct_choice.id) == student_answer if correct_choice else False
    elif exercise.exercise_type == 'vrai_faux':
        print("DEBUG: check_answer - correct_answer =", exercise.correct_answer)
        print("DEBUG: comparaison =", exercise.correct_answer.lower() == student_answer.lower())
        return exercise.correct_answer.lower() == student_answer.lower()
    elif exercise.exercise_type == 'reponse_courte':
        correct_answers = json.loads(exercise.correct_answer)
        print("DEBUG: check_answer - correct_answers =", correct_answers)
        print("DEBUG: check_answer - comparaison =", student_answer.strip().lower() in [ans.strip().lower() for ans in correct_answers])
        return student_answer.strip().lower() in [ans.strip().lower() for ans in correct_answers]
    else:
        return False

def get_or_create_stat(competition_id, student_id):
    stat = CompetitionStudentStat.query.filter_by(competition_id=competition_id, student_id=student_id).first()
    if not stat:
        stat = CompetitionStudentStat(competition_id=competition_id, student_id=student_id, correct_answers=0)
        db.session.add(stat)
        db.session.commit()
    return stat


@app.route("/competition/<int:competition_id>/run", methods=['GET', 'POST'])
def run_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    participants = competition.participants  # Liste des participants

    # Charger active_student_ids
    active_student_ids = json.loads(competition.active_student_ids) if competition.active_student_ids else []

    # Vérification de l'état de la compétition
    if not active_student_ids:
        if not participants:
            # Pas de participants => la compétition n'a pas commencé
            flash("La compétition n'a pas encore démarré ou aucun élève actif.", 'warning')
            return redirect(url_for('competition_detail', competition_id=competition.id))
        else:
            # Participants présents mais plus personne d'actif => Tous éliminés
            flash('Tous les élèves ont été éliminés. La compétition est terminée.', 'info')
            return redirect(url_for('competition_results', competition_id=competition.id))

    # Charger used_exercise_ids
    try:
        used_exercise_ids = json.loads(competition.used_exercise_ids)
    except json.JSONDecodeError:
        flash('Erreur de chargement des données de la compétition.', 'danger')
        return redirect(url_for('competition_detail', competition_id=competition.id))

    flash(f'Élèves actifs : {active_student_ids}', 'info')
    flash(f'Exercices utilisés : {used_exercise_ids}', 'info')

    # Vérifier l'index
    current_index = competition.current_student_index
    if current_index >= len(active_student_ids):
        # Réinitialiser l'index si nécessaire
        competition.current_student_index = 0
        current_index = 0
        db.session.commit()

    # Élève actuel
    current_student_id = active_student_ids[current_index]
    current_student = Student.query.get(current_student_id)

    print("DEBUG: Élève actuel ID =", current_student_id, "Nom =", current_student.name)
    print("DEBUG: Liste complète des élèves actifs =", active_student_ids)
    print("DEBUG: Index élève actuel =", current_index)

    # Sélectionner un exercice
    available_exercises = [ex for ex in competition.group.exercises if ex.id not in used_exercise_ids]
    if not available_exercises:
        # Plus de questions disponibles
        if competition.group.exercises:
            used_exercise_ids = []
            available_exercises = competition.group.exercises.copy()
        else:
            # Plus aucun exercice dans le groupe
            flash('Aucune question disponible dans le groupe.', 'danger')
            return redirect(url_for('competition_results', competition_id=competition.id))

    exercise = random.choice(available_exercises)
    competition.current_exercise_id = exercise.id
    db.session.commit()

    print("DEBUG: Exercice sélectionné =", exercise.title, "(ID:", exercise.id, ")")
    used_exercise_ids.append(exercise.id)
    competition.used_exercise_ids = json.dumps(used_exercise_ids)
    db.session.commit()

    # Gestion des modes
    if competition.mode == 'manuel':
        # Mode manuel
        if request.method == 'POST':
            result = request.form.get('result')
            if result == 'correct':
                flash(f"L'élève {current_student.name} continue.", 'success')
                # Incrémenter le compteur de réponses correctes
                stat = get_or_create_stat(competition.id, current_student_id)
                stat.correct_answers += 1
                db.session.commit()
            elif result == 'incorrect':
                # Éliminer l'élève
                active_student_ids.remove(current_student_id)
                competition.active_student_ids = json.dumps(active_student_ids)
                flash(f"L'élève {current_student.name} a été éliminé.", 'danger')

                # Vérifier si tous éliminés
                if not active_student_ids:
                    flash('Tous les élèves ont été éliminés. La compétition est terminée.', 'info')
                    db.session.commit()
                    return redirect(url_for('competition_results', competition_id=competition.id))
            else:
                flash('Résultat invalide.', 'danger')

            # Élève suivant
            new_index = (current_index + 1) % len(active_student_ids) if active_student_ids else 0
            competition.current_student_index = new_index
            db.session.commit()

            print("DEBUG: Après la réponse en mode manuel")
            print("DEBUG: active_student_ids =", active_student_ids)
            print("DEBUG: current_student_index =", competition.current_student_index)

            return redirect(url_for('run_competition', competition_id=competition.id))

        # Préparer l'affichage
        active_students = Student.query.filter(Student.id.in_(active_student_ids)).all()
        students_dict = {s.id: s.name for s in active_students}
        return render_template('run_competition_manual.html',
                               competition=competition,
                               student=current_student,
                               exercise=exercise,
                               active_student_ids=active_student_ids,
                               students_dict=students_dict)

    else:
        # Mode automatique
        student_id = session.get('student_id')
        if not student_id:
            flash('Vous devez rejoindre la compétition d\'abord.', 'danger')
            return redirect(url_for('join_competition'))

        if str(student_id) == str(current_student_id):
            if request.method == 'POST':
                submitted_exercise_id = request.form.get('exercise_id')
                submitted_exercise = Exercise.query.get(submitted_exercise_id)
                student_answer = request.form.get('answer')
                correct = check_answer(submitted_exercise, student_answer)

                if correct:
                    flash('Bonne réponse !', 'success')
                    # Incrémenter le compteur de réponses correctes
                    stat = get_or_create_stat(competition.id, current_student_id)
                    stat.correct_answers += 1
                    new_index = (current_index + 1) % len(active_student_ids) if active_student_ids else 0
                    competition.current_student_index = new_index
                else:
                    # Éliminer l'élève
                    active_student_ids.remove(current_student_id)
                    competition.active_student_ids = json.dumps(active_student_ids)
                    flash(f"Mauvaise réponse. L'élève {current_student.name} est éliminé.", 'danger')

                    # Vérifier si tous éliminés
                    if not active_student_ids:
                        flash('Tous les élèves ont été éliminés. La compétition est terminée.', 'info')
                        db.session.commit()
                        return redirect(url_for('competition_results', competition_id=competition.id))

                    # Rester sur le même index pour le prochain élève
                    competition.current_student_index = current_index

                db.session.commit()

                print("DEBUG: Après la réponse en mode automatique")
                print("DEBUG: active_student_ids =", active_student_ids)
                print("DEBUG: current_student_index =", competition.current_student_index)

                return render_template('run_competition_auto_wait.html', competition=competition, student_id=student_id)

            # GET : Afficher la question
            return render_template('run_competition_auto_current.html',
                                   competition=competition,
                                   student=current_student,
                                   exercise=exercise)
        else:
            # Ce n'est pas le tour de cet élève
            return render_template('run_competition_auto_wait.html', competition=competition)


@app.route("/competition/<int:competition_id>/results")
def competition_results(competition_id):
    competition = Competition.query.get_or_404(competition_id)

    # Charger active_student_ids et participants
    active_student_ids = json.loads(competition.active_student_ids) if competition.active_student_ids else []
    eliminated_student_ids = [s.id for s in competition.participants if s.id not in active_student_ids]

    # Récupérer les statistiques des élèves
    stats = CompetitionStudentStat.query.filter_by(competition_id=competition.id).all()
    # Créer un dictionnaire pour accéder rapidement aux statistiques par student_id
    stats_dict = {stat.student_id: stat.correct_answers for stat in stats}

    # Récupérer les élèves et ajouter leur nombre de réponses justes
    active_students = Student.query.filter(Student.id.in_(active_student_ids)).all()
    eliminated_students = Student.query.filter(Student.id.in_(eliminated_student_ids)).all()

    # Trier les élèves actifs par nombre de réponses justes décroissant
    active_students_sorted = sorted(active_students, key=lambda s: stats_dict.get(s.id, 0), reverse=True)
    eliminated_students = sorted(eliminated_students, key=lambda s: stats_dict.get(s.id, 0), reverse=True)


    return render_template('competition_results.html',
                           competition=competition,
                           active_students=active_students_sorted,
                           eliminated_students=eliminated_students,
                           stats_dict=stats_dict)

@app.route("/competition/<int:competition_id>/status")
def competition_status(competition_id):
    competition = Competition.query.get_or_404(competition_id)
    active_students_list = json.loads(competition.active_student_ids) if competition.active_student_ids else []
    current_student_id = None
    if active_students_list and 0 <= competition.current_student_index < len(active_students_list):
        current_student_id = active_students_list[competition.current_student_index]

    # Ajouter competition_started
    competition_started = getattr(competition, 'competition_started', False)

    data = {
        "current_student_id": current_student_id,
        "active_student_ids": active_students_list,
        "competition_started": competition_started
    }
    return jsonify(data)



@app.route("/competition/<int:competition_id>/teacher_view")
@login_required
def teacher_view_competition(competition_id):
    competition = Competition.query.get_or_404(competition_id)

    # Vérifier que l'utilisateur courant est l'enseignant
    if competition.group.teacher != current_user:
        abort(403)

    active_student_ids = json.loads(competition.active_student_ids) if competition.active_student_ids else []

    # S'il n'y a plus d'élèves actifs, rediriger vers les résultats
    if not active_student_ids:
        return redirect(url_for('competition_results', competition_id=competition.id))

    current_index = competition.current_student_index
    # Si l'index actuel est hors limites, le réinitialiser à 0
    if current_index >= len(active_student_ids):
        competition.current_student_index = 0
        current_index = 0
        db.session.commit()

    # Maintenant, current_index est forcément valide et on peut accéder à l'élève courant
    current_student_id = active_student_ids[current_index]
    current_student = Student.query.get(current_student_id)

    # Charger la question actuelle si elle est stockée
    current_exercise = None
    if competition.current_exercise_id:
        current_exercise = Exercise.query.get(competition.current_exercise_id)

    # Participants de la compétition
    participants = competition.participants

    return render_template('competition_teacher_view.html',
                           competition=competition,
                           current_student=current_student,
                           current_exercise=current_exercise,
                           active_student_ids=active_student_ids,
                           participants=participants)


@app.route("/competition/<int:competition_id>/teacher_status")
@login_required
def teacher_status(competition_id):
    competition = Competition.query.get_or_404(competition_id)

    # Vérifier que c’est bien l’enseignant
    if competition.group.teacher != current_user:
        abort(403)

    active_student_ids = json.loads(competition.active_student_ids) if competition.active_student_ids else []
    current_student_id = None
    current_exercise_id = competition.current_exercise_id  # Assurez-vous d'avoir ce champ dans Competition

    if active_student_ids:
        current_index = competition.current_student_index
        if 0 <= current_index < len(active_student_ids):
            current_student_id = active_student_ids[current_index]

    # Retourner les infos au format JSON
    data = {
        "current_student_id": current_student_id,
        "current_exercise_id": current_exercise_id,
        "active_student_ids": active_student_ids
    }
    return jsonify(data)




