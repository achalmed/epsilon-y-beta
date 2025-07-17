# Este es un ejemplo de un script básico en R

# Comentario de una línea: los comentarios se utilizan para agregar notas o explicaciones al código

# Variables
nombre <- "Juan"  # Variable de tipo texto (cadena de caracteres)
edad <- 25        # Variable numérica

# Imprimir en la consola
cat("Hola,", nombre, "tienes", edad, "años.\n")

# Operaciones aritméticas
suma <- 10 + 5
resta <- 10 - 5
multiplicacion <- 10 * 5
division <- 10 / 5

# Imprimir los resultados
cat("La suma es:", suma, "\n")
cat("La resta es:", resta, "\n")
cat("La multiplicación es:", multiplicacion, "\n")
cat("La división es:", division, "\n")

# Estructuras de control
if (edad >= 18) {
  cat("Eres mayor de edad.\n")
} else {
  cat("Eres menor de edad.\n")
}

# Bucle for
for (i in 1:5) {
  cat("Iteración:", i, "\n")
}

