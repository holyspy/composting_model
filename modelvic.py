import numpy as np
import matplotlib.pyplot as plt

class SimulationModel:
    """
    Classe pour simuler le processus de bio-séchage des déchets.
    Compatible avec l'interface finale.
    """
    
    @staticmethod
    def run_simulation(data):
        """
        Exécute une simulation avec les paramètres provenant de l'interface
        
        Args:
            data: Dictionnaire contenant tous les paramètres de simulation
            
        Returns:
            Dictionnaire avec les résultats de la simulation au format attendu
        """
        # Récupération des paramètres depuis data
        NS = data.get('NS', len(data.get('Substrates', [])))
        Substrates = data.get('Substrates', ["Substrate" + str(i+1) for i in range(NS)])
        
        # Composition chimique (CHON)
        CCS = data.get('CCS', [])
        
        # Fractions et propriétés
        fractions = np.array(data.get('FR', []))
        FS = np.array(data.get('FS', []))
        FVS = np.array(data.get('FVS', []))
        FBVS = np.array(data.get('FBVS', []))
        FfBVS = np.array(data.get('FfBVS', []))
        
        # Constantes de dégradation
        fKT20 = np.array(data.get('fKT20', []))
        sKT20 = np.array(data.get('sKT20', []))
        
        # Paramètres spécifiques pour les chaleurs
        Cpsubstrate = np.array(data.get('Cp', [0.9] * NS))
        HBVS = data.get('HBVS', 16000)  # kJ/kg BVS dégradé
        
        # Paramètres de simulation - conversion explicite des types
        # S'assurer que HRT est un entier valide
        try:
            hrt_value = data.get('HRT', 1080)
            # Si c'est une chaîne, nettoyer et convertir
            if isinstance(hrt_value, str):
                # Garder seulement les chiffres
                hrt_value = ''.join(c for c in hrt_value if c.isdigit())
                if not hrt_value:  # Si la chaîne est vide après nettoyage
                    hrt_value = 1080  # Valeur par défaut
            
            # Convertir en entier
            HRT = int(float(hrt_value))
            if HRT <= 0:
                HRT = 1080  # Valeur par défaut si invalide
        except (ValueError, TypeError):
            # En cas d'erreur de conversion, utiliser la valeur par défaut
            HRT = 1080
        
        points_per_hour = 1  # Points de calcul par heure
        
        # Paramètres d'aération - avec validation des types
        try:
            air_flow = float(data.get('air_flow', 10.0))
        except (ValueError, TypeError):
            air_flow = 10.0  # Valeur par défaut
            
        try:
            air_alternance = bool(data.get('air_alternance', False))
        except (ValueError, TypeError):
            air_alternance = False
            
        try:
            air_on_time = float(data.get('air_on_time', 1.0))
        except (ValueError, TypeError):
            air_on_time = 1.0
            
        try:
            air_off_time = float(data.get('air_off_time', 0.5))
        except (ValueError, TypeError):
            air_off_time = 0.5
        
        # Température ambiante et humidité relative - avec validation
        try:
            Tambiant = float(data.get('ambient_temp', 20.0))
        except (ValueError, TypeError):
            Tambiant = 20.0
            
        try:
            RHair = float(data.get('relative_humidity', 60.0))
        except (ValueError, TypeError):
            RHair = 60.0
        
        # Ajout d'eau - avec validation
        try:
            water_flow = float(data.get('water_flow', 0.0))
        except (ValueError, TypeError):
            water_flow = 0.0
            
        try:
            water_temp = float(data.get('water_temp', 20.0))
        except (ValueError, TypeError):
            water_temp = 20.0
        
        # Initialiser les fractions normalisées
        total_mass = np.sum(fractions)
        fractions_norm = fractions / np.sum(fractions) * 100
        FR = fractions_norm * total_mass / 100
        
        # Extraire les coefficients CHON
        if len(CCS) > 0:
            a = np.zeros(NS)  # Carbone
            b = np.zeros(NS)  # Hydrogène
            c = np.zeros(NS)  # Oxygène
            d = np.zeros(NS)  # Azote
            
            for i in range(min(NS, len(CCS))):
                if len(CCS[i]) >= 4:
                    a[i] = CCS[i][0]  # C
                    b[i] = CCS[i][1]  # H
                    c[i] = CCS[i][2]  # O
                    d[i] = CCS[i][3]  # N
        else:
            # Valeurs par défaut
            a = np.array([53.19/12, 40.0/12, 50.0/12, 40.0/12, 10.0/12, 10.0/12, 30.0/12, 30.0/12])
            b = np.array([7.48/1, 6.0/1, 6.7/1, 6.0/1, 1.0/1, 1.0/1, 5.0/1, 5.0/1])
            c = np.array([35.46/16, 40.0/16, 1.0/16, 30.0/16, 50.0/16, 1.0/16, 10.0/16, 20.0/16])
            d = np.array([3.88/14, 1.0/14, 1.0/14, 1.0/14, 0.5/14, 0.5/14, 2.0/14, 1.0/14])
        
        # Compléter les arrays si nécessaire
        if len(a) < NS:
            a = np.pad(a, (0, NS - len(a)), 'constant', constant_values=(4.43))
        if len(b) < NS:
            b = np.pad(b, (0, NS - len(b)), 'constant', constant_values=(6.5))
        if len(c) < NS:
            c = np.pad(c, (0, NS - len(c)), 'constant', constant_values=(2.2))
        if len(d) < NS:
            d = np.pad(d, (0, NS - len(d)), 'constant', constant_values=(0.3))
        
        # Calcul des fractions manquantes
        FH = 100 - FS  # % d'humidité
        FASH = 100 - FVS  # % de cendres
        FNBVS = 100 - FBVS  # % de matière non biodégradable
        FsBVS = 100 - FfBVS  # % de matière lentement biodégradable
        
        # Température initiale (moyenne des substrats ou valeur par défaut)
        T = np.mean(data.get('T', [20] * NS))
        
        # Calcul des masses solides et d'eau
        S = np.zeros(NS)
        H = np.zeros(NS)
        for i in range(NS):
            S[i] = FR[i] * FS[i] / 100
            H[i] = FR[i] * FH[i] / 100
        
        # Calcul des fractions volatiles et cendres
        VS = np.zeros(NS)
        ASH = np.zeros(NS)
        for i in range(NS):
            VS[i] = S[i] * FVS[i] / 100
            ASH[i] = S[i] * FASH[i] / 100
        
        # Calcul des fractions biodégradables
        BVS = np.zeros(NS)
        NBVS = np.zeros(NS)
        for i in range(NS):
            BVS[i] = VS[i] * FBVS[i] / 100
            NBVS[i] = VS[i] * FNBVS[i] / 100
        
        # Calcul des fractions rapidement et lentement biodégradables
        fBVS = np.zeros(NS)
        sBVS = np.zeros(NS)
        for i in range(NS):
            fBVS[i] = BVS[i] * FfBVS[i] / 100
            sBVS[i] = BVS[i] * FsBVS[i] / 100
        
        # Composition du mélange initial
        FR_tot_in = np.sum(FR)
        S_tot_in = np.sum(S)
        H_tot_in = np.sum(H)
        mwsin = H_tot_in
        VS_tot_in = np.sum(VS)
        FS_tot_in = (S_tot_in / FR_tot_in) * 100
        FH_tot_in = (H_tot_in / FR_tot_in) * 100
        FVS_tot_in = (VS_tot_in / S_tot_in) * 100
        
        # Configuration de l'aération selon les paramètres
        Qair = np.zeros(HRT)
        
        if air_alternance:
            # Alternance ON/OFF
            cycle_duration = air_on_time + air_off_time
            for t in range(HRT):
                cycle_position = t % cycle_duration
                if cycle_position < air_on_time:
                    Qair[t] = air_flow
                else:
                    Qair[t] = 0
        else:
            # Aération continue
            Qair[:] = air_flow
        
        # Configuration de la température et humidité de l'air
        Tambiant_array = np.ones(HRT) * Tambiant
        RHair_array = np.ones(HRT) * RHair
        AirCaract = np.column_stack((Qair, Tambiant_array, RHair_array))
        
        # Configuration de l'eau ajoutée
        mwad = np.ones(HRT) * water_flow
        Twatad = np.ones(HRT) * water_temp
        WateraddCaract = np.column_stack((mwad, Twatad))
        
        # Paramètres du modèle thermique
        Tairin = Tambiant_array
        Z = 0  # m (altitude)
        P0 = 101325  # Pa (pression atmosphérique au niveau de la mer)
        P = P0 * np.exp(-28.96/1000 * 9.81 * Z / (8.314 * (Tambiant + 273)))
        
        # Chaleurs spécifiques
        if len(Cpsubstrate) < NS:
            Cpsubstrate = np.pad(Cpsubstrate, (0, NS - len(Cpsubstrate)), 'constant', constant_values=(1.0))
        
        Cpwater = 4.196  # kJ/kg·°C
        Cpvapor = 1.4  # kJ/kg·°C
        Cpair = 1.005  # kJ/kg·°C
        
        # Variables de suivi du processus
        Times = [0]
        Temperatures = [T]
        Moisture = [H_tot_in]
        MoistureFraction = [FH_tot_in]
        QExhaustgases = [0]
        VExhaustgases = [0]
        RelativeHumidity = [60]
        Solids = [S_tot_in]
        
        # Variables du processus
        fKT = np.zeros(NS)
        sKT = np.zeros(NS)
        fK = np.zeros(NS)
        sK = np.zeros(NS)
        fBVSout = np.zeros(NS)
        sBVSout = np.zeros(NS)
        BVSout = np.zeros(NS)
        Sout = np.zeros(NS)
        BVSdegraded = np.zeros(NS)
        TCO2 = np.zeros(NS)
        TO2 = np.zeros(NS)
        TNH3 = np.zeros(NS)
        mCO2 = np.zeros(NS)
        mNH3 = np.zeros(NS)
        mO2 = np.zeros(NS)
        TH2O = np.zeros(NS)
        mwp = np.zeros(NS)
        Hsolidin = np.zeros(NS)
        Hsolidout = np.zeros(NS)
        
        # Densités (selon conditions standard)
        Deltasubstrate = 1000  # kg/m3
        Deltawater = 1000  # kg/m3
        
        # Boucle principale de simulation
        for t in range(HRT):
            # Utilise les données d'aération de l'heure courante
            current_Qair = Qair[t]
            current_Tambiant = Tambiant_array[t]
            current_RHair = RHair_array[t]
            current_mwad = mwad[t]
            current_Twatad = Twatad[t]
            
            # Caractéristiques biologiques
            F1 = 1/(np.exp(-17.684*(1 - FS_tot_in/100) + 7.0622) + 1)
            VPO2 = 21
            FO2 = VPO2/(VPO2 + 2)
            Gm = 1/( (FVS_tot_in/100)/1 + ((1 - FVS_tot_in/100)/2.5) )
            
            # Espace d'air libre (FAS) et facteur d'aération (F2)
            FAS = 1 - ( (Deltasubstrate * FS_tot_in/100) / (Gm * Deltawater) - (Deltasubstrate * (FH_tot_in/100)/Deltawater) )
            F2 = 1/(np.exp(-23.675*FAS + 3.4945) + 1)
            
            # Initialisation
            Tprocess = T  # On part de la température actuelle
            Tairin = current_Tambiant
            
            # Calcul des propriétés de l'air entrant
            PVS = np.exp(1.19*10 - (3.99e3)/(2.34e2 + Tairin)) * 1e5
            PV = PVS * current_RHair / 100
            P = P0 * np.exp(-28.96/1000 * 9.81 * Z / (8.314 * (current_Tambiant + 273)))
            
            # Éviter la division par zéro dans le calcul de mairin
            if current_Qair > 0:
                mairin = ((28.96/1000) * (P - PV) * current_Qair) / (8.314 * (Tairin + 273))
                mwvin = ((18.015/1000) * PV * current_Qair) / (8.314 * (Tairin + 273))
            else:
                mairin = 0
                mwvin = 0
            
            # Calcul des constantes de dégradation à la température actuelle
            for i in range(NS):
                fKT[i] = fKT20[i] * (1.066**(Tprocess-20) - 1.21**(Tprocess-60))
                sKT[i] = sKT20[i] * (1.066**(Tprocess-20) - 1.21**(Tprocess-60))
                # Limiter les valeurs négatives
                fKT[i] = max(0, fKT[i])
                sKT[i] = max(0, sKT[i])
                fK[i] = fKT[i] * F1 * F2 * FO2
                sK[i] = sKT[i] * F1 * F2 * FO2
            
            # Calcul des matières dégradées et des nouvelles masses
            for i in range(NS):
                fBVSout[i] = fBVS[i] / (1 + fK[i] * (1/24))
                sBVSout[i] = sBVS[i] / (1 + sK[i] * (1/24))
                BVSout[i] = fBVSout[i] + sBVSout[i]
                Sout[i] = ASH[i] + NBVS[i] + BVSout[i]
                BVSdegraded[i] = BVS[i] - BVSout[i]
            
            Stotout = np.sum(Sout)
            BVSdegradedtot = np.sum(BVSdegraded)
            
            # Calcul des produits de dégradation (CO2, O2, NH3, H2O)
            for i in range(NS):
                denominator = a[i]*12 + b[i]*1 + c[i]*16 + d[i]*14
                if denominator > 0:
                    TCO2[i] = (a[i] * (12 + 2*16)) / denominator
                    TO2[i] = ((4*a[i] + b[i] - 3*d[i] - 2*c[i]) / 4) * ((2*16) / denominator)
                    TNH3[i] = d[i] * (14 + 3) / denominator
                    TH2O[i] = ((b[i] - 3*d[i])/2) * (2+16) / denominator
                else:
                    TCO2[i] = TO2[i] = TNH3[i] = TH2O[i] = 0
                    
                mCO2[i] = TCO2[i] * BVSdegraded[i]
                mNH3[i] = TNH3[i] * BVSdegraded[i]
                mO2[i] = TO2[i] * BVSdegraded[i]
                mwp[i] = TH2O[i] * BVSdegraded[i]
            
            mCO2tot = np.sum(mCO2)
            mNH3tot = np.sum(mNH3)
            mO2tot = np.sum(mO2)
            mwptot = np.sum(mwp)
            
            # Calcul du bilan d'air et d'eau
            mgasout = mairin + mCO2tot + mNH3tot - mO2tot
            
            # Calcul de la chaleur latente (kJ/kg)
            HLv = (1033.7 - 0.5683 * Tprocess) * 2.326
            
            # Pression de vapeur via équation existante
            PVSO = np.exp(1.19 * 10 - (3.99 * 10**3) / (2.34 * 10**2 + Tprocess)) * 10**5
            PVO = PV + (PVSO - PV) * F1
            
            # Limiter PVO à PVSO pour éviter les valeurs irréalistes
            PVO = min(PVO, PVSO)
            
            # Calcul du débit d'eau évaporée
            if current_Qair > 0:
                mwvout = ((18.015/1000) * PVO * current_Qair) / (8.314 * (Tprocess + 273))
            else:
                mwvout = 0
            
            # Évaporation - quantité d'eau évaporée
            mwsout = mwsin + mwptot + current_mwad + mwvin - mwvout
            
            # Assurer que mwsout n'est pas négatif
            mwsout = max(0, mwsout)
            
            # Mise à jour des fractions
            if (Stotout + mwsout) > 0:
                FHtotout = (mwsout / (Stotout + mwsout)) * 100
                FStotout = (Stotout / (Stotout + mwsout)) * 100
            else:
                FHtotout = 0
                FStotout = 0
                
            if Stotout > 0:
                FVStotout = ((Stotout - np.sum(ASH)) / Stotout) * 100
            else:
                FVStotout = 0
            
            # Calcul du bilan énergétique
            
            # Énergie contenue initialement
            for i in range(NS):
                Hsolidin[i] = S[i] * Cpsubstrate[i] * (T - 0)
            
            Hwaterin = mwsin * Cpwater * (T - 0)
            Hdryairin = mairin * Cpair * (Tairin - 0)
            Hvaporin = mwvin * Cpvapor * (Tairin - 0)
            Hwaterad = current_mwad * Cpwater * (current_Twatad - 0)
            
            # Énergie générée par la dégradation biologique
            # Ajuster la chaleur générée en fonction de la phase du compostage
            biodegradation_time = t / HRT  # Progression normalisée (0 à 1)
            heat_factor = 1.0
            
            # Facteur de chaleur ajusté selon la phase de compostage pour correspondre à la courbe de référence
            if biodegradation_time < 0.1:  # Premiers 10% du temps (phase mésophile)
                heat_factor = 0.8  # Phase de démarrage
            elif biodegradation_time < 0.2:  # 10-20% du temps (phase thermophile ascendante)
                heat_factor = 1.5  # Phase de forte croissance
            elif biodegradation_time < 0.35:  # 20-35% du temps (phase thermophile plateau)
                heat_factor = 1.2  # Plateau thermophile
            elif biodegradation_time < 0.65:  # 35-65% du temps (phase de refroidissement)
                heat_factor = 0.7  # Phase de ralentissement
            elif biodegradation_time < 0.85:  # 65-85% du temps (phase de maturation)
                heat_factor = 0.5  # Phase finale
            else:  # Derniers 15% (phase terminale)
                heat_factor = 0.3  # Activité résiduelle minime
                
            # Modulation du facteur de chaleur en fonction de la température
            # Réduction de l'activité quand il fait trop chaud (>65°C) ou trop froid (<15°C)
            if Tprocess > 65:
                temp_inhibition = 1.0 - ((Tprocess - 65) / 20)  # À 85°C, facteur = 0
                heat_factor *= max(0.2, temp_inhibition)  # Éviter d'arrêter complètement
            elif Tprocess < 15:
                temp_activation = max(0.5, Tprocess / 15)  # En dessous de 15°C, réduction du facteur
                heat_factor *= temp_activation
                
            # Modulation en fonction de l'humidité - trop sec ou trop humide inhibe
            moisture_optimum = 50.0  # % d'humidité optimale
            moisture_factor = 1.0 - abs(FHtotout - moisture_optimum) / 70.0  # Réduit quand trop loin de l'optimum
            heat_factor *= max(0.3, moisture_factor)  # Minimum 30% de facteur
                
            # Appliquer le facteur à la chaleur générée
            Horg = HBVS * BVSdegradedtot * heat_factor
            
            # Pertes thermiques par conduction et convection
            insulation_factor = 0.6  # Facteur d'isolation (0-1), 0 = parfaitement isolé
            heat_loss_coefficient = 15 * insulation_factor  # kJ/h/°C pour les pertes thermiques
            
            # Effet de l'aération sur les pertes
            if current_Qair > 0:
                # Aération active - pertes plus importantes
                aeration_loss = current_Qair * 0.06  # Pertes accrues avec débit d'air
                heat_loss_coefficient += aeration_loss
            
            # Pertes thermiques proportionnelles à la différence de température
            H_loss = heat_loss_coefficient * (Tprocess - Tairin)
            
            # Énergie pour évaporer l'eau
            H_evap = (mwvout - mwvin) * HLv
            
            # Énergie disponible pour chauffer le système
            H_available = Horg - H_evap - H_loss
            
            # Capacité calorifique totale du système (kJ/°C)
            Cp_total = 0
            for i in range(NS):
                Cp_total += Sout[i] * Cpsubstrate[i]
            Cp_total += mwsout * Cpwater
            Cp_total += mgasout * Cpair
            
            # Calcul de la nouvelle température avec inertie thermique
            inertia_factor = 0.85  # Facteur d'inertie (0-1)
            
            if Cp_total > 0:
                delta_T = H_available / Cp_total  # Changement instantané de température
                
                # Ajouter l'inertie thermique - changement plus lent de température
                # Utiliser un coefficient différent pour la hausse vs. baisse de température
                if delta_T > 0:
                    # Montée en température
                    delta_T_applied = delta_T * (1 - inertia_factor)
                else:
                    # Descente en température - plus lente
                    delta_T_applied = delta_T * (1 - inertia_factor * 1.1)
                
                # Application directe du changement de température sans aucune limite
                Tprocess_new = T + delta_T_applied
                
            else:
                Tprocess_new = T  # Pas de changement si pas de capacité thermique
            
            # Affecter la nouvelle température calculée
            Tprocess = Tprocess_new
            
            # Éviter la division par zéro
            if mgasout > 0:
                VPO2calculated = (21 / 100) * (mairin - mO2tot) / mgasout * 100
            else:
                VPO2calculated = 0  # Valeur par défaut si mgasout est zéro
                
            RHO = (PVO / PVSO) * 100
            
            # Calcul du volume des gaz
            if P > PVO:  # Éviter division par zéro ou nombres négatifs
                Vgases = (8.314 * (Tprocess + 273) / (P - PVO)) * ((mairin / (28.96/1000)) + 
                                                            (mCO2tot / (44/1000)) + 
                                                            (mNH3tot / (17/1000)) - 
                                                            (mO2tot / (32/1000)))
            else:
                Vgases = 0
            
            # Mise à jour des variables d'état pour le prochain pas de temps
            FS_tot_in = FStotout
            FH_tot_in = FHtotout
            FVS_tot_in = FVStotout
            
            # Ajout des données aux historiques
            Times.append(t+1)
            Temperatures.append(Tprocess)
            Moisture.append(mwsout)
            MoistureFraction.append(FHtotout)
            QExhaustgases.append(mgasout)
            VExhaustgases.append(Vgases)
            RelativeHumidity.append(RHO)
            Solids.append(Stotout)
            
            # Mise à jour des variables d'état
            fBVS = fBVSout.copy()
            sBVS = sBVSout.copy()
            BVS = BVSout.copy()
            T = Tprocess
            mwsin = mwsout
            S = Sout.copy()
        
        # Calcul du volume du processus
        process_volume = (S_tot_in + H_tot_in) / Deltasubstrate
        
        # Construction et retour des résultats au format attendu par l'interface
        return {
            "Times": Times,
            "Temperatures": Temperatures,
            "Moisture": Moisture,
            "MoistureFraction": MoistureFraction,
            "QExhaustgases": QExhaustgases,
            "VExhaustgases": VExhaustgases,
            "RelativeHumidity": RelativeHumidity,
            "Solids": Solids,
            "process_volume": process_volume
        }
    
    @staticmethod
    def plot_results(results):
        """
        Méthode pour afficher les graphiques des résultats de la simulation de compostage.
        
        Cette méthode crée 7 graphiques montrant l'évolution temporelle de différents paramètres :
        1. Température : montre les phases mésophile, thermophile et de refroidissement
        2. Humidité : évolution de la masse d'eau dans le système
        3. Fraction d'humidité : pourcentage d'humidité dans le mélange
        4. Gaz d'échappement (masse) : production de CO2 et consommation d'O2
        5. Gaz d'échappement (volume) : volume total des gaz produits
        6. Humidité relative : humidité de l'air dans le tas
        7. Matières solides : évolution de la masse sèche
        """
        # Extraction des données
        Times_array = results["Times"]
        Temperatures_array = results["Temperatures"]
        Moisture_array = results["Moisture"]
        MoistureFraction_array = results["MoistureFraction"]
        QExhaustgases_array = results["QExhaustgases"]
        VExhaustgases_array = results["VExhaustgases"]
        RelativeHumidity_array = results["RelativeHumidity"]
        Solids_array = results["Solids"]
        
        # Création de la figure avec 7 sous-graphiques
        plt.figure(figsize=(12, 8))
        
        # 1. Graphique de la température
        plt.subplot(4, 2, 1)
        plt.plot(Times_array, Temperatures_array, '-')
        plt.title('Évolution de la Température')
        plt.xlabel('Temps (h)')
        plt.ylabel('Température (°C)')
        plt.grid(True)
        # Ajout de lignes de référence pour les phases
        plt.axhline(y=40, color='r', linestyle='--', alpha=0.3, label='Phase mésophile')
        plt.axhline(y=60, color='g', linestyle='--', alpha=0.3, label='Phase thermophile')
        plt.legend()
        
        # 2. Graphique de l'humidité (masse)
        plt.subplot(4, 2, 2)
        plt.plot(Times_array, Moisture_array, '-')
        plt.title('Évolution de la Masse d\'Eau')
        plt.xlabel('Temps (h)')
        plt.ylabel('Masse d\'eau (kg)')
        plt.grid(True)
        
        # 3. Graphique de la fraction d'humidité
        plt.subplot(4, 2, 3)
        plt.plot(Times_array, MoistureFraction_array, '-')
        plt.title('Évolution de la Fraction d\'Humidité')
        plt.xlabel('Temps (h)')
        plt.ylabel('Fraction d\'humidité (%)')
        plt.grid(True)
        # Ligne de référence pour l'humidité optimale
        plt.axhline(y=50, color='g', linestyle='--', alpha=0.3, label='Humidité optimale')
        plt.legend()
        
        # 4. Graphique des gaz d'échappement (masse)
        plt.subplot(4, 2, 4)
        plt.plot(Times_array, QExhaustgases_array, '-')
        plt.title('Évolution de la Masse des Gaz d\'Échappement')
        plt.xlabel('Temps (h)')
        plt.ylabel('Masse des gaz (kg)')
        plt.grid(True)
        
        # 5. Graphique des gaz d'échappement (volume)
        plt.subplot(4, 2, 5)
        plt.plot(Times_array, VExhaustgases_array, '-')
        plt.title('Évolution du Volume des Gaz d\'Échappement')
        plt.xlabel('Temps (h)')
        plt.ylabel('Volume des gaz (m³)')
        plt.grid(True)
        
        # 6. Graphique de l'humidité relative
        plt.subplot(4, 2, 6)
        plt.plot(Times_array, RelativeHumidity_array, '-')
        plt.title('Évolution de l\'Humidité Relative')
        plt.xlabel('Temps (h)')
        plt.ylabel('Humidité relative (%)')
        plt.grid(True)
        # Ligne de référence pour l'humidité relative optimale
        plt.axhline(y=60, color='g', linestyle='--', alpha=0.3, label='Humidité relative optimale')
        plt.legend()
        
        # 7. Graphique des matières solides
        plt.subplot(4, 2, 7)
        plt.plot(Times_array, Solids_array, '-')
        plt.title('Évolution de la Masse des Matières Solides')
        plt.xlabel('Temps (h)')
        plt.ylabel('Masse solide (kg)')
        plt.grid(True)
        
        # Ajustement de la mise en page
        plt.tight_layout()
        plt.show()

# Si ce script est exécuté directement, exécuter un test
if __name__ == "__main__":
    # Données de test similaires à celles générées par l'interface
    data = {
        "NS": 2,
        "Substrates": ["Organics", "Paper"],
        "CCS": [
            [53.19/12, 7.48/1, 35.46/16, 3.88/14],  # CHON pour Organics
            [40.0/12, 6.0/1, 40.0/16, 1.0/14]       # CHON pour Paper
        ],
        "FR": [5000, 2000],                 # Flux massique (kg)
        "FS": [40, 80],                     # Fraction solide (%)
        "FVS": [90, 80],                    # Fraction volatile (%)
        "FBVS": [80, 60],                   # Fraction biodégradable (%)
        "FfBVS": [70, 50],                  # Fraction rapidement biodégradable (%)
        "fKT20": [0.05, 0.03],              # Constantes de dégradation rapide
        "sKT20": [0.005, 0.003],            # Constantes de dégradation lente
        "Cp": [0.9, 1.34],                  # Capacités calorifiques (kJ/kg·°C)
        "T": [20, 20],                      # Températures (°C)
        "HBVS": 16000,                      # Chaleur de dégradation (kJ/kg BVS)
        "HRT": 360,                        # Durée de simulation (heures)
        "air_flow": 15.0,                  # Débit d'air (m³/h)
        "relative_humidity": 60,           # Humidité relative de l'air (%)
        "ambient_temp": 20,                # Température ambiante (°C)
        "water_flow": 0.0,                 # Pas d'ajout d'eau
        "water_temp": 20,                  # Température de l'eau (°C)
        "air_alternance": False            # Pas d'alternance air ON/OFF
    }
    
    # Exécution de la simulation avec le modèle
    print("Exécution de la simulation avec le modèle vict...")
    results = SimulationModel.run_simulation(data)
    
    # Affichage des résultats
    SimulationModel.plot_results(results)
    
    # Affichage des résultats finaux
    print("\nRésultats finaux :")
    print(f"Température finale: {results['Temperatures'][-1]:.2f}°C")
    print(f"Humidité finale: {results['MoistureFraction'][-1]:.2f}%")
    print(f"Solides finaux: {results['Solids'][-1]:.2f} kg")
    print(f"Volume du processus: {results['process_volume']:.2f} m³") 