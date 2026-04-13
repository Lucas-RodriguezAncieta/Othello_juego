# # This is a sample Python script.

# # Press Mayús+F10 to execute it or replace it with your code.
# # Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print_hi('PyCharm')

# # See PyCharm help at https://www.jetbrains.com/help/pycharm/
from Genetico import Genetico
from TableroOthello import TableroOthello
from AgenteIA.AgenteJugador import AgenteJugador
from AgenteIA.AgenteAleatorio import AgenteAleatorio

# =========================
# 1. ENTRENAMIENTO GENÉTICO
# =========================
gen = Genetico(poblacion_size=6, generaciones=5)

mejores_pesos = gen.evolucionar()

print("\n🔥 Mejores pesos encontrados:", mejores_pesos)


# =========================
# 2. PRUEBA FINAL
# =========================
print("\n===== PRUEBA FINAL =====")

tablero = TableroOthello()

ia = AgenteJugador(altura=4)
ia.pesos = mejores_pesos

random_agent = AgenteAleatorio()

tablero.insertar(ia)
tablero.insertar(random_agent)

tablero.run()