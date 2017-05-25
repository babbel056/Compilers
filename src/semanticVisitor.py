from astVisitor import AstVisitor
from astNode import *
from Exceptions import *
import copy

# Overloaded Ast Visitor for semantic analysis.
class SemanticVisitor(AstVisitor):
    def __init__(self, table, code):
        self.symbolTable = table
        self.mainFunctionFound = False
        self.codeBuilder = code # refers to codeBuilder.py

    def visitProgramNode(self, node:ProgramNode):
        # Check all global variables first (semantically)
        for child in node.children:
            if type(child) == DeclarationNode:
                self.visit(child)

        # Generate the main function and the global variables (code generation)
        self.codeBuilder.visit(node)

        # Further semantic analysis (non declaration nodes)
        for child in node.children:
            if type(child) != DeclarationNode:
                self.visit(child)
                self.symbolTable.resetScopeCounter() # Return to global scope

        # No main function declared in file
        if not self.mainFunctionFound: raise mainException()

        # Generate the code (program node)
        # self.codeBuilder.visit(node)

    def visitStdioNode(self, node:StdioNode):
        self.symbolTable.insertSymbol("printf()", 
            {'idType': "i", 'refCount': 0}, params=[]) 
        self.symbolTable.insertSymbol("scanf()", 
            {'idType': "i", 'refCount': 0}, params=[])    

    def visitFunctionDefinitionNode(self, node:FunctionDefinitionNode):
        # Insert function into symbol table
        parameters = list()
        if node.parameterList:
            parameters = node.parameterList.getParams()
        functionName = node.getID()
        functionType = node.getType()
        # Check if there was a forward function declaration
        if not self.symbolTable.insertSymbol(functionName+"()", functionType, params=parameters):
            item = self.symbolTable.lookupSymbol(functionName+"()")
            if not item.isForwardDecl:
                raise declarationException(functionName, 
                    functionType, True, node.getPosition())
            # Check if parameter types match
            if len(parameters) != len(item.parameters):
                raise conflictingParameterLength(functionName, len(parameters), len(item.parameters), node.getPosition())
            for index, param in enumerate(parameters):
                paramType1 = param.getType()
                paramType2 = item.getType()
                if paramType1 != paramType2:
                    raise parameterTypeError(functionName, paramType1, paramType2, node.getPosition())

        # Check for main function and if it has type integer
        if functionName == "main":
            self.mainFunctionFound = True
            if functionType['idType'] != 'i':
                raise mainTypeException(node.getPosition())

        # Visit the function body
        self.symbolTable.createScope(functionName)

        # Insert parameters into symbol table
        if node.parameterList:
            for paramDecl in node.parameterList.paramDecls:
                self.visit(paramDecl)

        # Iterate the statements in the function body
        for declstat in node.functionBody:
            # Check if the return expression matches the returntype of the function
            if type(declstat) == ReturnNode:
                self.checkType(declstat.expressionNode, functionType['idType'], node.getPosition())

            # Calculate extreme pointer
            print(type(declstat))
            retType = self.visit(declstat)

            # Compare type from return statement
            if retType and 'returnStat' in retType:
                retType.pop('returnStat')
                return

        # Generate the code for this function definition
        self.codeBuilder.visit(node)

    def visitParameterDeclarationNode(self, node:ParameterDeclarationNode):
        identifier = node.declarator
        exprList = identifier.arrayExpressionList
        arraySize = 0
        if len(exprList) != 0:
            arraySize = int(exprList[0].value)
            if len(exprList) != 1:
                raise wrongArrayDimension(node.getID(), node.getPosition())

        if (self.symbolTable.insertSymbol(node.getID(), 
            node.getType(), arraySize=arraySize) == None):
                raise declarationException(node.getID(), 
                    node.getType(), False, node.getPosition())

    def visitAssignmentNode(self, node:AssignmentNode):
        # Compare types
        print("test")
        item = self.symbolTable.lookupSymbol(node.getID(), node.identifier)
        if item == None: raise unknownVariable(node.getID(), node.getPosition())
        arrExprList = node.identifier.arrayExpressionList
        if item.arraySize:
            if len(arrExprList) == 0:
                raise wrongArrayDefinition(node.getPosition())
            if len(arrExprList) > 1:
                raise wrongArrayDimension(node.getID(), node.getPosition())
        exprType = self.visit(node.expression)
        # *b = 5
        declType = copy.deepcopy(item.type)
        if node.dereferenceCount > 0:
            declType['refCount'] -= node.dereferenceCount
        if declType['refCount'] < 0:
            raise deReference(node.getPosition())
        if exprType['idType'] != declType['idType']:
            raise wrongType(exprType['idType'], declType['idType'], node.getPosition())

    def visitIfStatementNode(self, node:IfStatementNode):
        # Check if expression is boolean
        exprType = self.visit(node.condition)
        declType = {'idType': "b", 'refCount': 0}
        if exprType != declType:     
            raise wrongType(exprType['idType'], declType['idType'], "TODO fix line here IF")
        if node.ifBody:
            for declStat in node.ifBody:
                self.visit(declStat)
        if node.elseBody:
            for declStat in node.elseBody:
                self.visit(declStat)

    def visitIterationStatementNode(self, node:IterationStatementNode):
        if node.statementName == "While":
            # Check if while expression is boolean
            exprType = self.visit(node.left)
            declType = {'idType': "b", 'refCount': 0}
            if exprType != declType: raise conditionException(exprType['idType'], node.getPosition())
            # visit function body
            for declStat in node.right:
                self.visit(declStat)
        if node.statementName == "For":
            # TODO deal with semantic errors in for loop here
            # TODO OPTIONAL implement for loop
            # Check if for condition is boolean
            if node.left == None or node.right == None or node.middle1 == None or node.middle2 == None:
                raise wrongForloop(node.getPosition())
            part1 = self.visit(node.left)
            # exprType = self.visit(node.middle1)
            # print(exprType)

    def visitReturnNode(self, node:ReturnNode):
        # Return a expression(identifier, functioncall, binary operation etc)
        if node.expressionNode:
            exprType = self.visit(node.expressionNode)
            return exprType
        # Return nothing
        return {'returnStat': True, 'idType': None, 'refCount': 0}

    def visitBreakNode(self, node:BreakNode):
        pass

    def visitContinueNode(self, node:ContinueNode):
        pass

    def visitDeclarationNode(self, node:DeclarationNode):
        declType = node.getType()
        arrExprList = node.identifier.arrayExpressionList
        arraySize = 0
        if len(arrExprList) > 0:
            arraySize = int(arrExprList[0].value)
            if len(arrExprList) > 1:
                raise wrongArrayDimension(node.getID(), node.getPosition())
            if node.expression and type(node.expression) != InitializerListNode:
                # TODO Raise error: wrong type in initializer, it has to be an initializerlist
                # Error never occurs TODO
                print("Semantic error: attempt to initialize array with wrong type")                
        if node.expression:
            # Compare types
            if isinstance(node.expression, list):
                for elem in node.expression:
                    # Check when index is an identifier:
                    # No reference to an existing variable => Throw unknownVariable exception
                    # Identifier has other type than integer => Throw wrongArrayIndexType exception
                    if type(elem) == IdentifierNode and node.expression.index(elem) != len(node.expression)-1:
                        if self.symbolTable.lookupSymbol(elem.getID()) == None:
                            raise unknownVariable(elem.getID(), elem.getPosition())
                        if self.symbolTable.lookupSymbol(elem.getID()).type['idType'] != 'i':
                            raise wrongArrayIndexType(self.symbolTable.lookupSymbol(elem.getID()).type['idType'], elem.getPosition())
                    if type(elem) == FloatingConstantNode or type(elem) == CharacterConstantNode or type(elem) == StringConstantNode:
                        raise wrongArrayIndexType(elem.getType(), elem.getPosition())
            if type(node.expression) == InitializerListNode:
                exprs = node.expression.expressions
                # Check if all elements in the initializer list are the same type as the declType
                for expr in exprs:
                    curType = self.visit(expr)
                    if curType != declType:
                        raise wrongType(curType['idType'], declType['idType'], expr.getPosition())
            self.checkType(node.expression, declType['idType'], node.getPosition())
        if self.symbolTable.insertSymbol(node.getID(), declType, arraySize=arraySize) == None:
            raise declarationException(node.getID(), 
                declType['idType'], False, node.getPosition())

    def visitBinaryOperationNode(self, node:BinaryOperationNode):
        exprTypeLeft = self.visit(node.left)
        exprTypeRight = self.visit(node.right)
        if (exprTypeRight['refCount'] > 0 or
            exprTypeLeft['refCount'] > 0):
            raise wrongOperation("add/subtract/mul or div", "an address", node.getPosition())
        typeLeft = exprTypeLeft['idType']
        typeRight = exprTypeRight['idType']
        if (node.operator == "&&" and node.operator == "||"):
            if typeLeft == {'idType': "b", 'refCount': 0}:
                # TODO && and || do not have a boolean type
                raise wrongOperation("&& and ||", 
                    typeLeft, node.getPosition(), typeRight)
            if typeLeft != typeRight:
                raise wrongOperation(str(node.operator),
                    typeLeft, node.getPosition(), typeRight)
        if (node.operator != "+" and node.operator != "-" 
            and node.operator != "*" and node.operator != "/"):
            exprTypeLeft = {'idType': "b", 'refCount': 0}
        return exprTypeLeft
            
    def visitExpressionNode(self, node:ExpressionNode):
        exprType = None
        if node.isPostfix:
            item = self.symbolTable.lookupSymbol(node.child.getID(), node.child)
            if item == None: raise unknownVariable(node.child.getID(), node.getPosition())
            # Id++ or Id-- works for all types except for char 
            # TODO Test if it works for floats/addresses
            # Get the type of the identifier
            exprType = self.visit(node.child)
            if exprType['idType'] == "c" and exprType['refCount'] == 0:
                raise incrementError(exprType['idType'],node.getPosition())
        return exprType

    def visitDereferenceExpressionNode(self, node:DereferenceExpressionNode):
        item = self.symbolTable.lookupSymbol(node.child.getID(), node.child)
        if item == None: raise unknownVariable(node.child.getID(), node.getPosition())
        if item.type['refCount'] < node.derefCount:
            raise deReference(node.getPosition())
        # Decrease the reference count of the exprType
        exprType = copy.deepcopy(item.type)
        exprType['refCount'] -= node.derefCount
        return exprType

    def visitReferenceExpressionNode(self, node:ReferenceExpressionNode):
        item = self.symbolTable.lookupSymbol(node.child.getID(), node.child)
        if item == None: raise unknownVariable(node.child.getID(), node.getPosition())
        # Increase the reference count of the exprType
        exprType = copy.deepcopy(item.type)
        exprType['refCount'] += 1
        return exprType  

    def visitFunctionCallNode(self, node:FunctionCallNode):
        item = self.symbolTable.lookupSymbol(node.getID() + "()")
        if (node.getID() == "printf" or node.getID() == "scanf") and item == None:
            # Added specific exception for the inclusion of printf and scanf
            raise includeException(node.getID(), node.getPosition())
        if item == None: raise unknownVariable(node.getID()+"()", node.getPosition(), True)
        if node.getID() == "printf" or node.getID() == "scanf":
            # Handle included printf and scanf functions as inline code.
            args = node.argumentExpressionListNode.argumentExprs
            if len(args) > 0:
                argType = self.visit(args[0])
                # Check if first argument is a Char array
                if argType['idType'] == "c" and argType['refCount'] == 0:
                    if type(args[0]) == IdentifierNode:
                        # TODO Raise exception
                        print(node.getID() + " does not support Identifiers as format argument.")
                        # Argument is an identifier
                        argItem = self.symbolTable.lookupSymbol(args[0].getID(), args[0])
                        if argItem.arraySize > 0:
                            return {'idType': "i", 'refCount': 0}
                    elif argType['isArray']:
                        # Argument is a string literal
                        argsIndex = 1
                        stringLit = str(args[0].value)
                        for index, char in enumerate(stringLit):
                            if char == "%" and index+1 < len(stringLit):
                                if index != 0 and stringLit[index-1] == "%":
                                    continue
                                tempType = self.visit(args[argsIndex])
                                if argsIndex >= len(args):
                                    # TODO Raise exception
                                    print(node.getID() + " has not enough arguments for the given format.")
                                if type(args[argsIndex]) != IdentifierNode:
                                    if node.getID() == "scanf": 
                                        if tempType['refCount'] != 1:
                                            # TODO Raise exception
                                            print("scanf only accepts pointers to basic type variables in the args list parameter.")                                        
                                    else:
                                        # TODO Raise exception

                                        print("printf only accepts identifiers in the args list parameter.")
                                nextChar = stringLit[index+1]
                                if (nextChar == "i" and tempType['idType'] == "i" or
                                    nextChar == "d" and tempType['idType'] == "r" or
                                    nextChar == "c" and tempType['idType'] == "c" or
                                    nextChar == "s" and (tempType['idType'] == "c" and isArray in tempType)
                                    ):
                                    argsIndex += 1
                                    continue
                                # TODO Raise exception
                                print(node.getID() + " has incorrect argument type for the given format.")
                        return {'idType': "i", 'refCount': 0}
            # TODO Raise exception, I'm using a temp dereference error at the moment
            print(node.getID() + " requires an array of characters (make better error msg)")
            raise deReference(0)
        params = item.parameters # List of parameterDeclNode
        args = []
        if node.argumentExpressionListNode:
            args = node.argumentExpressionListNode.argumentExprs
        if len(params) != len(args):
            raise conflictingParameterLength(node.getID(), len(args), len(params), node.getPosition())
        for i in range(len(params)):
            paramType = params[i].getType()
            argType = self.visit(args[i])
            if argType != paramType:
                 raise parameterTypeError(node.getID(), argType['idType'], paramType['idType'], node.getPosition())
            # Type is an array while the parameter is not
            if len(item.parameters[i].declarator.arrayExpressionList) == 0:
                raise parameterTypeError(node.getID(), "array", argType['idType'], node.getPosition())
            paramArraySize = int(item.parameters[i].declarator.arrayExpressionList[0].value)
            argItem = None
            if type(args[i]) == IdentifierNode:
                argItem = self.symbolTable.lookupSymbol(args[i].getID(), args[i])
            if paramArraySize:
                if (type(args[i]) != IdentifierNode or not argItem.arraySize
                    or len(args[i].arrayExpressionList) != 0):
                    raise parameterTypeError(node.getID(), args[i].getType(), "array", node.getPosition())
            if argItem and paramArraySize != argItem.arraySize:
                raise conflictingArgumentLength(node.getID(), node.getPosition())
        return item.type    

    def visitIntegerConstantNode(self, node:IntegerConstantNode):
        return {'idType': "i", 'refCount': 0}

    def visitFloatingConstantNode(self, node:FloatingConstantNode):
        return {'idType': "r", 'refCount': 0}

    def visitCharacterConstantNode(self, node:CharacterConstantNode):
        return {'idType': "c", 'refCount': 0}

    def visitStringConstantNode(self, node:StringConstantNode):
        return {'idType': "c", 'refCount': 0, 'isArray': True}

    def visitDeclarationSpecifierNode(self, node:DeclarationSpecifierNode):
        pass   

    def visitIdentifierNode(self, node:IdentifierNode):
        item = self.symbolTable.lookupSymbol(node.getID(), node)
        if item == None: raise unknownVariable(node.getID(), node.getPosition())
        if len(node.arrayExpressionList) > 0:        
            exprType = self.visit(node.arrayExpressionList[0])
            if exprType['idType'] != "i":
                raise wrongArrayIndexType(exprType['idType'], node.getPosition())
        return item.type

    def visitForwardFunctionDeclarationNode(self, node:ForwardFunctionDeclarationNode):
        parameters = dict()
        if node.parameterList:
            parameters = node.parameterList.getParams()
        if not self.symbolTable.insertSymbol(node.getID()+"()", 
            node.declarationSpecifier.getType(), 
            params=parameters, isForwardDecl=True):
            knownType = self.symbolTable.lookupSymbol(node.getID()+"()").type['idType']
            raise declarationException(node.getID(), knownType, True, node.getPosition())

    # Check if expression has the same type as the correctType
    def checkType(self, declStat, correctType, position):
        if type(declStat) == IdentifierNode:
            if self.symbolTable.lookupSymbol(declStat.getID()) == None:
                raise unknownVariable(declStat.getID(), declStat.getPosition())
            retType = self.symbolTable.lookupSymbol(declStat.getID()).type['idType']
            if retType != correctType:
                raise wrongReturnType(retType, correctType, position)

        # If statement contains a function call
        elif type(declStat) == FunctionCallNode:
            if self.symbolTable.lookupSymbol(declStat.getID() + "()") == None:
                raise unknownVariable(declStat.getID() + "()", declStat.getPosition())
            retType = self.symbolTable.lookupSymbol(declStat.getID() + "()").type['idType']
            if retType != correctType:
                raise wrongReturnType(retType, correctType, position)

        # If statement is an expression
        elif type(declStat) != BinaryOperationNode and declStat.getType() != correctType:
            raise wrongReturnType(declStat.getType(), correctType, position)

        # Check if when the statement is a binary operation,
        # If all the types in the expression match the type
        elif type(declStat) == BinaryOperationNode:
            types = declStat.getType()
            for i in types:
                if type(i) == IdentifierNode:
                    if self.symbolTable.lookupSymbol(i.getID()) == None:
                        raise unknownVariable(i.getID(), i.getPosition())
                    i = self.symbolTable.lookupSymbol(i.getID()).type['idType']
                if type(i) == FunctionCallNode:
                    if self.symbolTable.lookupSymbol(i.getID()+"()") == None:
                        raise unknownVariable(i.getID()+"()", i.getPosition(), True)
                    i = self.symbolTable.lookupSymbol(i.getID() + "()").type['idType']
                if i != correctType:
                    raise wrongReturnExpression(i, correctType, position)
