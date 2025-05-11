"""
Script de correction pour le problème d'affichage du graphique d'analyse de sensibilité.
Ce script modifie le fichier 'interface final.py' pour corriger le problème.
"""

import re
import os
import tkinter as tk
from tkinter import messagebox

def backup_file(filename):
    """Crée une sauvegarde du fichier original"""
    backup_name = filename + '.bak'
    try:
        with open(filename, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(backup_name, 'w', encoding='utf-8') as dst:
            dst.write(content)
        return True
    except Exception as e:
        print(f"Erreur lors de la création de la sauvegarde: {e}")
        return False

def fix_sensitivity_function():
    """Corrige la fonction run_sensitivity_analysis dans le fichier d'interface"""
    filename = "interface final.py"
    
    # Créer une sauvegarde d'abord
    if not backup_file(filename):
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Rechercher le bloc de code problématique
        problematic_code = """            # Plot the results
            self.sensitivity_figure.clear()
            
            # Créer deux subplots - un pour le critère principal, un pour le rapport C/N
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
            self.sensitivity_figure = fig"""
        
        # Nouveau code corrigé
        fixed_code = """            # Plot the results
            self.sensitivity_figure.clear()
            
            # Créer deux subplots dans la figure existante
            ax1 = self.sensitivity_figure.add_subplot(211)  # Premier subplot (2 rangées, 1 colonne, position 1)
            ax2 = self.sensitivity_figure.add_subplot(212, sharex=ax1)  # Deuxième subplot avec axe x partagé"""
        
        # Remplacer le code problématique
        new_content = content.replace(problematic_code, fixed_code)
        
        # Autre partie de code à corriger: supprimer la création d'un nouveau canvas
        canvas_code = """            # Mettre à jour le canvas
            canvas = FigureCanvasTkAgg(self.sensitivity_figure, self.sensitivity_graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.sensitivity_canvas = canvas"""
            
        fixed_canvas_code = """            # Mettre à jour le canvas existant
            self.sensitivity_canvas.draw()"""
            
        new_content = new_content.replace(canvas_code, fixed_canvas_code)
        
        # Enregistrer les modifications
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        return True
    except Exception as e:
        print(f"Erreur lors de la correction du fichier: {e}")
        return False

def show_result_message(success):
    """Affiche un message indiquant si la correction a réussi"""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    if success:
        messagebox.showinfo("Succès", "La correction a été appliquée avec succès.\n\nVous pouvez maintenant relancer l'application.")
    else:
        messagebox.showerror("Erreur", "Une erreur s'est produite lors de la correction.\n\nVeuillez consulter la console pour plus de détails.")
    
    root.destroy()

if __name__ == "__main__":
    print("Application de la correction pour le graphique d'analyse de sensibilité...")
    success = fix_sensitivity_function()
    show_result_message(success) 