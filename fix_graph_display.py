"""
Script de correction pour le problème d'affichage des graphiques dans l'analyse de sensibilité.
Ce script modifie le fichier 'interface final.py' pour ajuster la taille des graphiques et les marges.
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

def fix_graph_display():
    """Corrige l'affichage des graphiques dans l'analyse de sensibilité"""
    filename = "interface final.py"
    
    # Créer une sauvegarde d'abord
    if not backup_file(filename):
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 1. Remplacer le code qui définit la taille de la figure
        size_pattern = r"# Augmenter la taille de la figure\s+self\.sensitivity_figure\.set_size_inches\(10, 9\)"
        new_size_code = "# Définir une taille adaptée à la fenêtre\n            self.sensitivity_figure.set_size_inches(8, 6)"
        content = re.sub(size_pattern, new_size_code, content)
        
        # 2. Modifier les proportions des subplots pour optimiser l'espace
        height_pattern = r"height_ratios=\[3, 2\]"
        new_height_code = "height_ratios=[2, 1]"  # Réduire encore plus la taille du graphique inférieur
        content = re.sub(height_pattern, new_height_code, content)
        
        # 3. Supprimer les ajustements redondants à la fin du fichier
        end_adjustments = r"# Ajuster la taille de la figure pour s'adapter à la fenêtre.*?self\.sensitivity_figure\.set_size_inches\(.*?\).*?\n"
        content = re.sub(end_adjustments, "", content, flags=re.DOTALL)
        
        # 4. Améliorer le tight_layout pour réduire les marges
        layout_pattern = r"plt\.tight_layout\(rect=\[0, 0, 1, 0\.95\]\)"
        new_layout_code = "plt.tight_layout(rect=[0, 0, 1, 0.92], pad=0.4, h_pad=0.5, w_pad=0.5)"
        content = re.sub(layout_pattern, new_layout_code, content)
        
        # 5. Modifier la taille des annotations pour qu'elles soient plus compactes
        annotations_pattern = r"bbox=dict\(boxstyle=\"round,pad=0\.3\""
        new_annotations_code = "bbox=dict(boxstyle=\"round,pad=0.2\""
        content = re.sub(annotations_pattern, new_annotations_code, content)
        
        # 6. Modifier la légende pour qu'elle soit plus compacte
        legend_pattern = r"self\.sensitivity_figure\.legend\(\s+handles=.*?,\s+loc='upper center',\s+bbox_to_anchor=\(0\.5, 0\.98\),\s+ncol=2,\s+fancybox=True,\s+shadow=True\s+\)"
        new_legend_code = "self.sensitivity_figure.legend(\n                handles=[blue_patch, red_patch, green_patch, orange_patch],\n                loc='upper center', \n                bbox_to_anchor=(0.5, 0.97),\n                ncol=4,\n                fontsize=8,\n                fancybox=True, \n                shadow=True\n            )"
        content = re.sub(legend_pattern, new_legend_code, content, flags=re.DOTALL)
        
        # Enregistrer les modifications
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
            
        return True
    except Exception as e:
        print(f"Erreur lors de la correction du fichier: {e}")
        return False

def show_result_message(success):
    """Affiche un message indiquant si la correction a réussi"""
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    
    if success:
        messagebox.showinfo("Succès", "La correction de l'affichage des graphiques a été appliquée avec succès.\n\nVous pouvez maintenant relancer l'application.")
    else:
        messagebox.showerror("Erreur", "Une erreur s'est produite lors de la correction.\n\nVeuillez consulter la console pour plus de détails.")
    
    root.destroy()

if __name__ == "__main__":
    print("Application des corrections pour l'affichage des graphiques...")
    success = fix_graph_display()
    show_result_message(success) 