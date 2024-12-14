import subprocess
import time
import requests
from playwright.sync_api import sync_playwright

def wait_for_server(host="http://127.0.0.1:5000", timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(host)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    raise Exception("Le serveur Flask n'est pas prêt après 60s.")

def main():
    # Lancer le serveur Flask
    server_process = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        # Attendre que le serveur soit prêt
        wait_for_server()
        print("Serveur prêt !")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            # Onglet enseignant
            teacher_page = context.new_page()
            teacher_page.goto("http://127.0.0.1:5000/login")
            # Vérifier qu'on arrive bien sur la page login (par exemple, vérifier un élément présent dans login.html)
            teacher_page.wait_for_selector("form")  # Supposant qu'il y a un formulaire sur la page login

            # Remplir le formulaire de login enseignant
            # Adaptez les sélecteurs en fonction de votre template login.html
            teacher_page.fill("input[name='email']", "loicstrauch@proton.me")
            teacher_page.fill("input[name='password']", "Mondoudou7")
            teacher_page.click("input[type='submit']")

            teacher_page.wait_for_load_state("networkidle")

            # Vérifier qu'on est connecté : peut-être en checkant un élément sur la page d'accueil
            teacher_page.wait_for_selector("text=Bienvenue sur PacoMathQuiz") # Titre présent dans home.html

            # Aller à la page de création de compétition
            teacher_page.goto("http://127.0.0.1:5000/competition/new")
            teacher_page.wait_for_load_state("networkidle")
            # Sélectionner un groupe et une classe (assurez-vous d'avoir au moins un groupe et une classe créés)
            teacher_page.select_option("select[name='group_id']", "1")  # Supposez que le groupe avec l'id 1 existe
            teacher_page.select_option("select[name='class_id']", "1")  # Supposez que la classe avec l'id 1 existe
            teacher_page.click("input[value='automatique']")
            teacher_page.click("text=Démarrer la Compétition")
            teacher_page.wait_for_load_state("networkidle")

            # Récupérer le code de la compétition
            # Adapter le sélecteur : dans competition_detail.html, vous affichez le code comment ?
            # Supposons qu'il y ait un élément <h3>Code de Connexion : <strong>{{ competition.code }}</strong></h3>
            code_text = teacher_page.inner_text("h3:has-text('Code de Connexion')")
            code = code_text.split(":")[-1].strip()
            print(f"Code de la compétition: {code}")

            # Créer trois onglets élève
            students_contexts = []
            students_pages = []
            for i in range(3):
                ctx = browser.new_context()  # Nouveau contexte privé
                students_contexts.append(ctx)
                pg = ctx.new_page()
                students_pages.append(pg)
                pg.goto("http://127.0.0.1:5000/competition/join")
                pg.wait_for_selector("input[name='code']")
                pg.fill("input[name='code']", code)
                pg.click("input[value='Rejoindre']")
                pg.wait_for_load_state("networkidle")
                # Sélection de l'élève i+1
                pg.select_option("select[name='student_id']", str(i+1))
                pg.click("button:has-text('Rejoindre La Compétition')")
                pg.wait_for_load_state("networkidle")
                pg.wait_for_selector("text=Patientez")

            # Continuer avec le reste de la logique...
            print("Tout est prêt. Les élèves sont inscrits. La compétition est lancée.")
            # Une fois que tous les élèves sont sur la page d'attente
            print("Les élèves sont prêts. Lancer la compétition côté enseignant.")

            # Supposons que la competition_id soit connue ou qu'on l'ait récupérée auparavant.
            # Vous avez déjà le code de la compétition. Si vous avez la competition_id, utilisez-la:

            # Ici, on est sur competition_detail.html en mode automatique.
            # Vérifier qu'un formulaire est présent
            teacher_page.wait_for_selector("form")

            # Cliquer sur le bouton de soumission du formulaire
            # Puisque c'est un SubmitField WTForms, c'est probablement un input[type='submit']
            teacher_page.click("input[type='submit']")
            teacher_page.wait_for_load_state("networkidle")

            print("Compétition démarrée !")


            time.sleep(200)  # Laisser du temps pour observer
            browser.close()

    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
