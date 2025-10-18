from data.readers import selic_years_ahead, di_curve


# =========================
# ===== Survey Method =====
# =========================
exp_selic = selic_years_ahead()
zero_curve = di_curve()
print(zero_curve)



# TODO Parei aqui
#  computar as taxas FRA da curva de DI (Criar uma classe genérica que faz isso para uma curva zero)
#  A classe/função tem ue calcular as taxas forward entre cada vértice para cada data