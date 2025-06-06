import numpy as np
import matplotlib.pyplot as plt

class SimulationModel:
    """
    Classe pour simuler le processus de bio-sÃ©chage des dÃ©chets.
    Compatible avec l'interface finale.
    """
    
    @staticmethod
    def run_simulation(data):
        """
        ExÃ©cute une simulation avec les paramÃ¨tres provenant de l'interface
        
        Args:
            data: Dictionnaire contenant tous les paramÃ¨tres de simulation
            
        Returns:
            Dictionnaire avec les rÃ©sultats de la simulation au format attendu
        """
        # RÃ©cupÃ©ration des paramÃ¨tres depuis data
        NS = data.get('NS', len(data.get('Substrates', [])))
        Substrates = data.get('Substrates', ["Substrate" + str(i+1) for i in range(NS)])
        
        # Composition chimique (CHON)
        CCS = data.get('CCS', [])
        
        # Fractions et propriÃ©tÃ©s
        fractions = np.array(data.get('FR', []))
        FS = np.array(data.get('FS', []))
        FVS = np.array(data.get('FVS', []))
        FBVS = np.array(data.get('FBVS', []))
        FfBVS = np.array(data.get('FfBVS', []))
        
        # Constantes de dÃ©gradation
        fKT20 = np.array(data.get('fKT20', []))
        sKT20 = np.array(data.get('sKT20', []))
        
        # ParamÃ¨tres spÃ©cifiques pour les chaleurs
        Cpsubstrate = np.array(data.get('Cp', [0.9] * NS))
        HBVS = data.get('HBVS', 16000)  # kJ/kg BVS dÃ©gradÃ©
        
        # ParamÃ¨tres de simulation - conversion explicite des types
        # S'assurer que HRT est un entier valide
        try:
            hrt_value = data.get('HRT', 1080)
            # Si c'est une chaÃ®ne, nettoyer et convertir
            if isinstance(hrt_value, str):
                # Garder seulement les chiffres
                hrt_value = ''.join(c for c in hrt_value if c.isdigit())
                if not hrt_value:  # Si la chaÃ®ne est vide aprÃ¨s nettoyage
                    hrt_value = 1080  # Valeur par dÃ©faut
            
            # Convertir en entier
            HRT = int(float(hrt_value))
            if HRT <= 0:
                HRT = 1080  # Valeur par dÃ©faut si invalide
        except (ValueError, TypeError):
            # En cas d'erreur de conversion, utiliser la valeur par dÃ©faut
            HRT = 1080
        
        points_per_hour = 1  # Points de calcul par heure
        
        # ParamÃ¨tres d'aÃ©ration - avec validation des types
        try:
            air_flow = float(data.get('air_flow', 10.0))
        except (ValueError, TypeError):
            air_flow = 10.0  # Valeur par dÃ©faut
            
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
        
        # TempÃ©rature ambiante et humiditÃ© relative - avec validation
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
        
        # Initialiser les fractions normalisÃ©es
        total_mass = np.sum(fractions)
        fractions_norm = fractions / np.sum(fractions) * 100
        FR = fractions_norm * total_mass / 100
        
        # Extraire les coefficients CHON
        if len(CCS) > 0:
            a = np.zeros(NS)  # Carbone
            b = np.zeros(NS)  # HydrogÃ¨ne
            c = np.zeros(NS)  # OxygÃ¨ne
            d = np.zeros(NS)  # Azote
            
            for i in range(min(NS, len(CCS))):
                if len(CCS[i]) >= 4:
                    a[i] = CCS[i][0]  # C
                    b[i] = CCS[i][1]  # H
                    c[i] = CCS[i][2]  # O
                    d[i] = CCS[i][3]  # N
        else:
            # Valeurs par dÃ©faut
            a = np.array([53.19/12, 40.0/12, 50.0/12, 40.0/12, 10.0/12, 10.0/12, 30.0/12, 30.0/12])
            b = np.array([7.48/1, 6.0/1, 6.7/1, 6.0/1, 1.0/1, 1.0/1, 5.0/1, 5.0/1])
            c = np.array([35.46/16, 40.0/16, 1.0/16, 30.0/16, 50.0/16, 1.0/16, 10.0/16, 20.0/16])
            d = np.array([3.88/14, 1.0/14, 1.0/14, 1.0/14, 0.5/14, 0.5/14, 2.0/14, 1.0/14])
        
        # ComplÃ©ter les arrays si nÃ©cessaire
        if len(a) < NS:
            a = np.pad(a, (0, NS - len(a)), 'constant', constant_values=(4.43))
        if len(b) < NS:
            b = np.pad(b, (0, NS - len(b)), 'constant', constant_values=(6.5))
        if len(c) < NS:
            c = np.pad(c, (0, NS - len(c)), 'constant', constant_values=(2.2))
        if len(d) < NS:
            d = np.pad(d, (0, NS - len(d)), 'constant', constant_values=(0.3))
        
        # Calcul des fractions manquantes
        FH = 100 - FS  # % d'humiditÃ©
        FASH = 100 - FVS  # % de cendres
        FNBVS = 100 - FBVS  # % de matiÃ¨re non biodÃ©gradable
        FsBVS = 100 - FfBVS  # % de matiÃ¨re lentement biodÃ©gradable
        
        # TempÃ©rature initiale (moyenne des substrats ou valeur par dÃ©faut)
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
        
        # Calcul des fractions biodÃ©gradables
        BVS = np.zeros(NS)
        NBVS = np.zeros(NS)
        for i in range(NS):
            BVS[i] = VS[i] * FBVS[i] / 100
            NBVS[i] = VS[i] * FNBVS[i] / 100
        
        # Calcul des fractions rapidement et lentement biodÃ©gradables
        fBVS = np.zeros(NS)
        sBVS = np.zeros(NS)
        for i in range(NS):
            fBVS[i] = BVS[i] * FfBVS[i] / 100
            sBVS[i] = BVS[i] * FsBVS[i] / 100
        
        # Composition du mÃ©lange initial
        FR_tot_in = np.sum(FR)
        S_tot_in = np.sum(S)
        H_tot_in = np.sum(H)
        mwsin = H_tot_in
        VS_tot_in = np.sum(VS)
        FS_tot_in = (S_tot_in / FR_tot_in) * 100
        FH_tot_in = (H_tot_in / FR_tot_in) * 100
        FVS_tot_in = (VS_tot_in / S_tot_in) * 100
        
        # Configuration de l'aÃ©ration selon les paramÃ¨tres
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
            # AÃ©ration continue
            Qair[:] = air_flow
        
        # Configuration de la tempÃ©rature et humiditÃ© de l'air
        Tambiant_array = np.ones(HRT) * Tambiant
        RHair_array = np.ones(HRT) * RHair
        AirCaract = np.column_stack((Qair, Tambiant_array, RHair_array))
        
        # Configuration de l'eau ajoutÃ©e
        mwad = np.ones(HRT) * water_flow
        Twatad = np.ones(HRT) * water_temp
        WateraddCaract = np.column_stack((mwad, Twatad))
        
        # ParamÃ¨tres du modÃ¨le thermique
        Tairin = Tambiant_array
        Z = 0  # m (altitude)
        P0 = 101325  # Pa (pression atmosphÃ©rique au niveau de la mer)
        P = P0 * np.exp(-28.96/1000 * 9.81 * Z / (8.314 * (Tambiant + 273)))
        
        # Chaleurs spÃ©cifiques
        if len(Cpsubstrate) < NS:
            Cpsubstrate = np.pad(Cpsubstrate, (0, NS - len(Cpsubstrate)), 'constant', constant_values=(1.0))
        
        Cpwater = 4.196  # kJ/kgÂ·Â°C
        Cpvapor = 1.4  # kJ/kgÂ·Â°C
        Cpair = 1.005  # kJ/kgÂ·Â°C
        
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
        
        # DensitÃ©s (selon conditions standard)
        Deltasubstrate = 1000  # kg/m3
        Deltawater = 1000  # kg/m3
        
        # Boucle principale de simulation
        for t in range(HRT):
            # Utilise les donnÃ©es d'aÃ©ration de l'heure courante
            current_Qair = Qair[t]
            current_Tambiant = Tambiant_array[t]
            current_RHair = RHair_array[t]
            current_mwad = mwad[t]
            current_Twatad = Twatad[t]
            
            # CaractÃ©ristiques biologiques
            F1 = 1/(np.exp(-17.684*(1 - FS_tot_in/100) + 7.0622) + 1)
            VPO2 = 21
            FO2 = VPO2/(VPO2 + 2)
            Gm = 1/( (FVS_tot_in/100)/1 + ((1 - FVS_tot_in/100)/2.5) )
            
            # Espace d'air libre (FAS) et facteur d'aÃ©ration (F2)
            FAS = 1 - ( (Deltasubstrate * FS_tot_in/100) / (Gm * Deltawater) - (Deltasubstrate * (FH_tot_in/100)/Deltawater) )
            F2 = 1/(np.exp(-23.675*FAS + 3.4945) + 1)
            
            # Initialisation
            Tprocess = T  # On part de la tempÃ©rature actuelle
            Tairin = current_Tambiant
            
            # Calcul des propriÃ©tÃ©s de l'air entrant
            PVS = np.exp(1.19*10 - (3.99e3)/(2.34e2 + Tairin)) * 1e5
            PV = PVS * current_RHair / 100
            P = P0 * np.exp(-28.96/1000 * 9.81 * Z / (8.314 * (current_Tambiant + 273)))
            
            # Ã‰viter la division par zÃ©ro dans le calcul de mairin
            if current_Qair > 0:
                mairin = ((28.96/1000) * (P - PV) * current_Qair) / (8.314 * (Tairin + 273))
                mwvin = ((18.015/1000) * PV * current_Qair) / (8.314 * (Tairin + 273))
            else:
                mairin = 0
                mwvin = 0
            
            # Calcul des constantes de dÃ©gradation Ã  la tempÃ©rature actuelle
            for i in range(NS):
                fKT[i] = fKT20[i] * (1.066**(Tprocess-20) - 1.21**(Tprocess-60))
                sKT[i] = sKT20[i] * (1.066**(Tprocess-20) - 1.21**(Tprocess-60))
                # Limiter les valeurs nÃ©gatives
                fKT[i] = max(0, fKT[i])
                sKT[i] = max(0, sKT[i])
                fK[i] = fKT[i] * F1 * F2 * FO2
                sK[i] = sKT[i] * F1 * F2 * FO2
            
            # Calcul des matiÃ¨res dÃ©gradÃ©es et des nouvelles masses
            for i in range(NS):
                fBVSout[i] = fBVS[i] / (1 + fK[i] * (1/24))
                sBVSout[i] = sBVS[i] / (1 + sK[i] * (1/24))
                BVSout[i] = fBVSout[i] + sBVSout[i]
                Sout[i] = ASH[i] + NBVS[i] + BVSout[i]
                BVSdegraded[i] = BVS[i] - BVSout[i]
            
            Stotout = np.sum(Sout)
            BVSdegradedtot = np.sum(BVSdegraded)
            
            # Calcul des produits de dÃ©gradation (CO2, O2, NH3, H2O)
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
            
            # Pression de vapeur via Ã©quation existante
            PVSO = np.exp(1.19 * 10 - (3.99 * 10**3) / (2.34 * 10**2 + Tprocess)) * 10**5
            PVO = PV + (PVSO - PV) * F1
            
            # Limiter PVO Ã  PVSO pour Ã©viter les valeurs irrÃ©alistes
            PVO = min(PVO, PVSO)
            
            # Calcul du dÃ©bit d'eau Ã©vaporÃ©e
            if current_Qair > 0:
                mwvout = ((18.015/1000) * PVO * current_Qair) / (8.314 * (Tprocess + 273))
            else:
                mwvout = 0
            
            # Ã‰vaporation - quantitÃ© d'eau Ã©vaporÃ©e
            mwsout = mwsin + mwptot + current_mwad + mwvin - mwvout
            
            # Assurer que mwsout n'est pas nÃ©gatif
            mwsout = max(0, mwsout)
            
            # Mise Ã  jour des fractions
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
            
            # Calcul du bilan Ã©nergÃ©tique
            
            # Ã‰nergie contenue initialement
            for i in range(NS):
                Hsolidin[i] = S[i] * Cpsubstrate[i] * (T - 0)
            
            Hwaterin = mwsin * Cpwater * (T - 0)
            Hdryairin = mairin * Cpair * (Tairin - 0)
            Hvaporin = mwvin * Cpvapor * (Tairin - 0)
            Hwaterad = current_mwad * Cpwater * (current_Twatad - 0)
            
            # Ã‰nergie gÃ©nÃ©rÃ©e par la dÃ©gradation biologique
            # Ajuster la chaleur gÃ©nÃ©rÃ©e en fonction de la phase du compostage
            biodegradation_time = t / HRT  # Progression normalisÃ©e (0 Ã  1)
            heat_factor = 1.0
            
            # Facteur de chaleur ajustÃ© selon la phase de compostage pour correspondre Ã  la courbe de rÃ©fÃ©rence
            if biodegradation_time < 0.1:  # Premiers 10% du temps (phase mÃ©sophile)
                heat_factor = 0.8  # Phase de dÃ©marrage
            elif biodegradation_time < 0.2:  # 10-20% du temps (phase thermophile ascendante)
                heat_factor = 1.5  # Phase de forte croissance
            elif biodegradation_time < 0.35:  # 20-35% du temps (phase thermophile plateau)
                heat_factor = 1.2  # Plateau thermophile
            elif biodegradation_time < 0.65:  # 35-65% du temps (phase de refroidissement)
                heat_factor = 0.7  # Phase de ralentissement
            elif biodegradation_time < 0.85:  # 65-85% du temps (phase de maturation)
                heat_factor = 0.5  # Phase finale
            else:  # Derniers 15% (phase terminale)
                heat_factor = 0.3  # ActivitÃ© rÃ©siduelle minime
                
            # Modulation du facteur de chaleur en fonction de la tempÃ©rature
            # RÃ©duction de l'activitÃ© quand il fait trop chaud (>65Â°C) ou trop froid (<15Â°C)
            if Tprocess > 65:
                temp_inhibition = 1.0 - ((Tprocess - 65) / 20)  # Ã€ 85Â°C, facteur = 0
                heat_factor *= max(0.2, temp_inhibition)  # Ã‰viter d'arrÃªter complÃ¨tement
            elif Tprocess < 15:
                temp_activation = max(0.5, Tprocess / 15)  # En dessous de 15Â°C, rÃ©duction du facteur
                heat_factor *= temp_activation
                
            # Modulation en fonction de l'humiditÃ© - trop sec ou trop humide inhibe
            moisture_optimum = 50.0  # % d'humiditÃ© optimale
            moisture_factor = 1.0 - abs(FHtotout - moisture_optimum) / 70.0  # RÃ©duit quand trop loin de l'optimum
            heat_factor *= max(0.3, moisture_factor)  # Minimum 30% de facteur
                
            # Appliquer le facteur Ã  la chaleur gÃ©nÃ©rÃ©e
            Horg = HBVS * BVSdegradedtot * heat_factor
            
            # Pertes thermiques par conduction et convection
            insulation_factor = 0.6  # Facteur d'isolation (0-1), 0 = parfaitement isolÃ©
            heat_loss_coefficient = 15 * insulation_factor  # kJ/h/Â°C pour les pertes thermiques
            
            # Effet de l'aÃ©ration sur les pertes
            if current_Qair > 0:
                # AÃ©ration active - pertes plus importantes
                aeration_loss = current_Qair * 0.06  # Pertes accrues avec dÃ©bit d'air
                heat_loss_coefficient += aeration_loss
            
            # Pertes thermiques proportionnelles Ã  la diffÃ©rence de tempÃ©rature
            H_loss = heat_loss_coefficient * (Tprocess - Tairin)
            
            # Ã‰nergie pour Ã©vaporer l'eau
            H_evap = (mwvout - mwvin) * HLv
            
            # Ã‰nergie disponible pour chauffer le systÃ¨me
            H_available = Horg - H_evap - H_loss
            
            # CapacitÃ© calorifique totale du systÃ¨me (kJ/Â°C)
            Cp_total = 0
            for i in range(NS):
                Cp_total += Sout[i] * Cpsubstrate[i]
            Cp_total += mwsout * Cpwater
            Cp_total += mgasout * Cpair
            
            # Calcul de la nouvelle tempÃ©rature avec inertie thermique
            inertia_factor = 0.85  # Facteur d'inertie (0-1)
            
            if Cp_total > 0:
                delta_T = H_available / Cp_total  # Changement instantanÃ© de tempÃ©rature
                
                # Ajouter l'inertie thermique - changement plus lent de tempÃ©rature
                # Utiliser un coefficient diffÃ©rent pour la hausse vs. baisse de tempÃ©rature
                if delta_T > 0:
                    # MontÃ©e en tempÃ©rature
                    delta_T_applied = delta_T * (1 - inertia_factor)
                else:
                    # Descente en tempÃ©rature - plus lente
                    delta_T_applied = delta_T * (1 - inertia_factor * 1.1)
                
                # Application directe du changement de tempÃ©rature sans aucune limite
                Tprocess_new = T + delta_T_applied
                
            else:
                Tprocess_new = T  # Pas de changement si pas de capacitÃ© thermique
            
            # Affecter la nouvelle tempÃ©rature calculÃ©e
            Tprocess = Tprocess_new
            
            # Ã‰viter la division par zÃ©ro
            if mgasout > 0:
                VPO2calculated = (21 / 100) * (mairin - mO2tot) / mgasout * 100
            else:
                VPO2calculated = 0  # Valeur par dÃ©faut si mgasout est zÃ©ro
                
            RHO = (PVO / PVSO) * 100
            
            # Calcul du volume des gaz
            if P > PVO:  # Ã‰viter division par zÃ©ro ou nombres nÃ©gatifs
                Vgases = (8.314 * (Tprocess + 273) / (P - PVO)) * ((mairin / (28.96/1000)) + 
                                                            (mCO2tot / (44/1000)) + 
                                                            (mNH3tot / (17/1000)) - 
                                                            (mO2tot / (32/1000)))
            else:
                Vgases = 0
            
            # Mise Ã  jour des variables d'Ã©tat pour le prochain pas de temps
            FS_tot_in = FStotout
            FH_tot_in = FHtotout
            FVS_tot_in = FVStotout
            
            # Ajout des donnÃ©es aux historiques
            Times.append(t+1)
            Temperatures.append(Tprocess)
            Moisture.append(mwsout)
            MoistureFraction.append(FHtotout)
            QExhaustgases.append(mgasout)
            VExhaustgases.append(Vgases)
            RelativeHumidity.append(RHO)
            Solids.append(Stotout)
            
            # Mise Ã  jour des variables d'Ã©tat
            fBVS = fBVSout.copy()
            sBVS = sBVSout.copy()
            BVS = BVSout.copy()
            T = Tprocess
            mwsin = mwsout
            S = Sout.copy()
        
        # Calcul du volume du processus
        process_volume = (S_tot_in + H_tot_in) / Deltasubstrate
        
        # Construction et retour des rÃ©sultats au format attendu par l'interface
        return {
            "Times": np.array(Times),
            "Temperatures": np.array(Temperatures),
            "Moisture": np.array(Moisture),
            "MoistureFraction": np.array(MoistureFraction),
            "QExhaustgases": np.array(QExhaustgases),
            "VExhaustgases": np.array(VExhaustgases),
            "RelativeHumidity": np.array(RelativeHumidity),
            "Solids": np.array(Solids),
            "process_volume": process_volume
        }
    
    @staticmethod
    def plot_results(results):
        """
        MÃ©thode pour afficher les graphiques des rÃ©sultats, compatible avec l'interface
        """
        # Extraction des donnÃ©es
        Times_array = results["Times"]
        Temperatures_array = results["Temperatures"]
        Moisture_array = results["Moisture"]
        MoistureFraction_array = results["MoistureFraction"]
        QExhaustgases_array = results["QExhaustgases"]
        VExhaustgases_array = results["VExhaustgases"]
        RelativeHumidity_array = results["RelativeHumidity"]
        Solids_array = results["Solids"]
        
        # Graphiques
        plt.figure(figsize=(12, 8))
        
        plt.subplot(4, 2, 1)
        plt.plot(Times_array, Temperatures_array, '-')
        plt.title('Temperature Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Temperature (Â°C)')
        plt.grid(True)
        
        plt.subplot(4, 2, 2)
        plt.plot(Times_array, Moisture_array, '-')
        plt.title('Moisture Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Moisture (kg)')
        plt.grid(True)
        
        plt.subplot(4, 2, 3)
        plt.plot(Times_array, MoistureFraction_array, '-')
        plt.title('Moisture Fraction Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Moisture Fraction (%)')
        plt.grid(True)
        
        plt.subplot(4, 2, 4)
        plt.plot(Times_array, QExhaustgases_array, '-')
        plt.title('Exhaust Gases Mass Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Exhaust Gases (kg)')
        plt.grid(True)
        
        plt.subplot(4, 2, 5)
        plt.plot(Times_array, VExhaustgases_array, '-')
        plt.title('Exhaust Gases Volume Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Exhaust Gases (mÂ³)')
        plt.grid(True)
        
        plt.subplot(4, 2, 6)
        plt.plot(Times_array, RelativeHumidity_array, '-')
        plt.title('Relative Humidity Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Relative Humidity (%)')
        plt.grid(True)
        
        plt.subplot(4, 2, 7)
        plt.plot(Times_array, Solids_array, '-')
        plt.title('Solids Over Time')
        plt.xlabel('Time (h)')
        plt.ylabel('Solids (kg)')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

# Si ce script est exÃ©cutÃ© directement, exÃ©cuter un test
if __name__ == "__main__":
    # DonnÃ©es de test similaires Ã  celles gÃ©nÃ©rÃ©es par l'interface
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
        "FBVS": [80, 60],                   # Fraction biodÃ©gradable (%)
        "FfBVS": [70, 50],                  # Fraction rapidement biodÃ©gradable (%)
        "fKT20": [0.05, 0.03],              # Constantes de dÃ©gradation rapide
        "sKT20": [0.005, 0.003],            # Constantes de dÃ©gradation lente
        "Cp": [0.9, 1.34],                  # CapacitÃ©s calorifiques (kJ/kgÂ·Â°C)
        "T": [20, 20],                      # TempÃ©ratures (Â°C)
        "HBVS": 16000,                      # Chaleur de dÃ©gradation (kJ/kg BVS)
        "HRT": 360,                        # DurÃ©e de simulation (heures)
        "air_flow": 15.0,                  # DÃ©bit d'air (mÂ³/h)
        "relative_humidity": 60,           # HumiditÃ© relative de l'air (%)
        "ambient_temp": 20,                # TempÃ©rature ambiante (Â°C)
        "water_flow": 0.0,                 # Pas d'ajout d'eau
        "water_temp": 20,                  # TempÃ©rature de l'eau (Â°C)
        "air_alternance": False            # Pas d'alternance air ON/OFF
    }
    
    # ExÃ©cution de la simulation avec le modÃ¨le
    print("ExÃ©cution de la simulation avec le modÃ¨le vict...")
    results = SimulationModel.run_simulation(data)
    
    # Affichage des rÃ©sultats
    SimulationModel.plot_results(results)
    
    # Affichage des rÃ©sultats finaux
    print("\nRÃ©sultats finaux :")
    print(f"TempÃ©rature finale: {results['Temperatures'][-1]:.2f}Â°C")
    print(f"HumiditÃ© finale: {results['MoistureFraction'][-1]:.2f}%")
    print(f"Solides finaux: {results['Solids'][-1]:.2f} kg")
    print(f"Volume du processus: {results['process_volume']:.2f} mÂ³") 
