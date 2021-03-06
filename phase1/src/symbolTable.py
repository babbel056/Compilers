# Symbol table for the compiler
# Based on http://www.newagepublishers.com/samplechapter/001679.pdf

class symbolTableLocal:
    """ Symbol table for a local scope / block"""
    def __init__(self):
        self.table = dict()

    # Return the symbol table in a readable format
    def __str__(self):
        return str(self.table)

    # Insert a key in the symbol table
    def insertSymbol(self, key, token):
        if key in self.table:
            print("Duplicate declaration for ", key)
        else:
            self.table[key] = token

    # Lookup a key in the table if it is present
    def lookupSymbol(self, key):
        if key in self.table:
            return self.table[key]
        print("Symbol not present in current table")
        return None

class generalSymbolTable:
    """ Symbol table for the general program (global and local scopes)"""
    def __init__(self):
        self.globalScope = dict()
        self.localScope = list()
        self.presentScope = -1

    # Print the symbol table
    def __repr__(self):
        returnValue = "Global Scope: " + str(self.globalScope) + "\n"
        for scope in self.localScope:
            returnValue += "Local scope: " + str(scope) + "\n"
        return returnValue

    # Enter a new scope
    def beginScope(self):
        newScope = symbolTableLocal
        self.localScope.append(newScope)
        self.presentScope += 1

    # Close the scope
    def endScope(self):
        self.localScope.pop()
        self.presentScope -= 1

    # Insert a symbol depending on the current scope
    def insertSymbol(self, key, token):
        if self.presentScope == -1:
            if key in self.globalScope: print("Duplicate declaration for ", key)
            self.globalScope[key] = token
        else:
            self.localScope[self.presentScope].insertSymbol(key, token)

    # Lookup a key first in the current local scope and then the surrounding scopes
    def lookupSymbol(self, key):
        temporaryScope = len(self.localScope)-1
        while temporaryScope != 0:
            if self.localScope[temporaryScope].lookupSymbol(key) != None:
                return self.localScope[temporaryScope].lookupSymbol(key)
            temporaryScope -= 1
        if self.globalScope[key] == None: print("Key ", key, "not found in the symbol table")
        return self.globalScope[key]
