import sys
import copy
import operator

from queue import Queue

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()        
        self.ac3()
        #print()
        #print("Inicia backtrack")
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable, listaPalabras in self.domains.items():
            listaTemporal = []
            for palabra in listaPalabras:
                if variable.length == len(palabra):
                    listaTemporal.append(palabra) 
            self.domains[variable] = listaTemporal
        #self.print_state("Fin enforce_node_consistency")

    def print_state(self, state):
        """ Imprime las variables junto con 
        su lista de palabras posibles """
        print()
        print(f"Estado:  {state}")
        for var in self.domains.keys():
            print(f"Var: {var}      Posibles: {self.domains[var]}")

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        cruce = self.crossword.overlaps[x, y]
        if cruce == None:
            return revised

        posX, posY = cruce

        palabrasX = self.domains[x].copy()
        for palabraEnX in palabrasX:
            counter = 0
            for palabraEnY in self.domains[y]:
                if palabraEnX[posX] == palabraEnY[posY]:                                
                    counter += 1
                    revised = True
            if counter == 0:
                self.domains[x].remove(palabraEnX)
        return revised
        #raise NotImplementedError

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = Queue()
            for parVariables in self.crossword.overlaps.keys():
                if self.crossword.overlaps[parVariables] != None:
                    arcs.put(parVariables)

        while len(arcs.queue) > 0:
            (x,y) = arcs.get()
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for vecina in self.crossword.neighbors(x) - {y}:
                    arcs.put((vecina, x))
        #self.print_state("Fin ac3")
        return True

        #raise NotImplementedError

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        if len(assignment) < len(self.crossword.variables):
            return False
        return True
        #raise NotImplementedError

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for var in assignment.keys():
            if len(assignment[var]) != var.length:
                return False        

        palabras = assignment.values()
        if len(palabras) != len(set(palabras)):        
            return False

        for var1 in assignment.keys():
            for var2 in assignment.keys():
                if var1 != var2:                    
                    cruce = self.crossword.overlaps[var1, var2]
                    if cruce != None:
                        posX, posY = cruce
                        if assignment[var1][posX] != assignment[var2][posY]:
                            return False

        return True
        # raise NotImplementedError

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        listaPosiblesVar = self.domains[var]
        VecinosAfectados = dict()
        for VarVecina in self.crossword.neighbors(var):
            if VarVecina not in assignment.keys():
                VecinosAfectados[VarVecina] = 0
        dictPalabras = dict()

        for palabra in listaPosiblesVar:
            dictPalabras[palabra] = 0

        for palPosibleVar in listaPosiblesVar:
            for afectado in VecinosAfectados.keys():
                cruce = self.crossword.overlaps[var, afectado]
                posX, posY = cruce
                conteoPosibles = 0
                for palPosible in self.domains[afectado]:
                    if palPosibleVar[posX] == palPosible[posY]:
                        conteoPosibles+=1
                dictPalabras[palPosibleVar] = conteoPosibles
        dictOrdenado = sorted(dictPalabras.items(), key=lambda t: t[::-1])
        lista = []
        for pareja in dictOrdenado:
            pal = pareja[0]
            lista.append(pal)
        listaOrdenada = list(reversed(lista))
        return listaOrdenada
        # raise NotImplementedError 

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        inicial = 10000
        for var in self.domains.keys():
            if var in assignment.keys():
                continue
            if len(self.domains[var]) < inicial:
                inicial = len(self.domains[var])
                varElegida = var
            elif len(self.domains[var]) == inicial:
                if len(self.crossword.neighbors(varElegida)) < len(self.crossword.neighbors(var)):
                    varElegida = var
            
        return varElegida
        # raise NotImplementedError

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # print("Inicia backtracking")        
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        # print(f"{var} no esta asignada todavia")
        for valor in self.order_domain_values(var, assignment):
            assignment[var] = valor
            if self.consistent(assignment):                
                resultado = self.backtrack(assignment)
                if resultado != False:
                    return resultado
            else:
                assignment.pop(var)
        return False                    
        #raise NotImplementedError


def main():

    # Empieza comentarizacion para depurar
    ## Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments    
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None
    # Fin comentarizacion para depurar

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    # empieza la modificacion
    assignment = creator.solve()    

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
