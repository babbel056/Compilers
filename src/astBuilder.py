from astNode import *
from CmmVisitor import CmmVisitor
from CmmParser import CmmParser

class astBuilder(CmmVisitor):
    def __init__(self, name):
        self.name = name

    def visitProgram(self, ctx:CmmParser.ProgramContext):
        return ProgramNode(self.visitChildren(ctx))

    def visitExternalDeclaration(self, ctx:CmmParser.ExternalDeclarationContext):
        return self.visitChildren(ctx)

    def visitFunctionDefinition(self, ctx:CmmParser.FunctionDefinitionContext):
        return self.visitChildren(ctx)

    def visitParameterList(self, ctx:CmmParser.ParameterListContext):
        return self.visitChildren(ctx)

    def visitParameterDeclaration(self, ctx:CmmParser.ParameterDeclarationContext):
        return self.visitChildren(ctx)

    def visitDeclaration(self, ctx:CmmParser.DeclarationContext):
        declarationSpec = self.visit(ctx.declarationSpecifier())
        identifier, expression = self.visit(ctx.initDeclarator())
        return DeclarationNode(declarationSpec, identifier, expression)

    def visitDeclarationSpecifier(self, ctx:CmmParser.DeclarationSpecifierContext):
        isConstant = ctx.Const() != None
        idType = ctx.typeSpecifier().getText()
        hasPointer = ctx.Star() != None
        return DeclarationSpecifierNode(isConstant, idType, hasPointer)

    def visitInitDeclarator(self, ctx:CmmParser.InitDeclaratorContext):
        return [self.visit(ctx.declarator()), self.visit(ctx.expression())]

    def visitDeclarator(self, ctx:CmmParser.DeclaratorContext):
        if ctx.getChildCount() == 1:
            return self.visitChildren(ctx)
        # If the declarator is an array element.
        # Recursively fill the arrayExpressionList
        node = self.visit( ctx.declarator() )
        node.arrayExpressionList.append( self.visit(ctx.expression()) )    
        return node

    def visitPrimaryExpression(self, ctx:CmmParser.PrimaryExpressionContext):
        return self.visitChildren(ctx)

    def visitIdentifier(self, ctx:CmmParser.IdentifierContext):
        return IdentifierNode(ctx.getText(), [])

    def visitConstant(self, ctx:CmmParser.ConstantContext):
        return self.visitChildren(ctx)

    def visitIntegerConstant(self, ctx:CmmParser.IntegerConstantContext):
        return IntegerConstantNode(ctx.getText())

    def visitFloatingConstant(self, ctx:CmmParser.FloatingConstantContext):
        return FloatingConstantNode(ctx.getText())

    def visitCharacterConstant(self, ctx:CmmParser.CharacterConstantContext):
        return CharacterConstantNode(ctx.getText())

    def visitExpression(self, ctx:CmmParser.ExpressionContext):
        if ctx.getChildCount() == 1:
            return self.visitChildren(ctx)
        if ctx.getChildCount() == 2:
            if ctx.And() == None:
                return ExpressionNode(ctx.getChild(1).getText(), True, self.visit( ctx.primaryExpression() ))
            return ExpressionNode(ctx.getChild(0).getText(), False, self.visit( ctx.expression(0)) )
        if ctx.getChildCount() == 3:
            return BinaryOperationNode( ctx.binaryOperator().getText(), self.visit( ctx.expression(0) ), self.visit( ctx.expression(1) ) )  
        # Function call not implemented.
        # Rule is array specifier.
        node = self.visit( ctx.expression(0) )
        if isinstance(node, IdentifierNode):
            node.arrayExpressionList.append( self.visit(ctx.expression()) )
        else:
            print("Semantic Error: Cannot select array index of a constant expression.")
        return node        

    def visitArgumentExpressionList(self, ctx:CmmParser.ArgumentExpressionListContext):
        return self.visitChildren(ctx)

    def visitStatement(self, ctx:CmmParser.StatementContext):
        return self.visitChildren(ctx)

    def visitCompoundStatement(self, ctx:CmmParser.CompoundStatementContext):
        return self.visitChildren(ctx)

    def visitIfStatement(self, ctx:CmmParser.IfStatementContext):
        ifBody = self.visit(ctx.statement(0))
        elseBody = None
        if ctx.Else():
            elseBody = self.visit(ctx.statement(1))
        return IfStatementNode(self.visit(ctx.expression()), ifBody, elseBody)

    def visitIterationStatement(self, ctx:CmmParser.IterationStatementContext):
        if ctx.While():
            return IterationStatementNode("While", self.visit(ctx.expression(0)), None, None, self.visit(ctx.statement()))
        left = None
        middle1 = None
        middle2 = None
        right = self.visit(ctx.statement())
        if ctx.declaration():
            left = self.visit(ctx.declaration())
            if ctx.expression(0):
                middle1 = self.visit(ctx.expression(0))
            if ctx.expression(1):
                middle2 = self.visit(ctx.expression(1))
        else:
            if ctx.expression(0):
                left = self.visit(ctx.expression(0))
            if ctx.expression(1):
                middle1 = self.visit(ctx.expression(1))
            if ctx.expression(2):
                middle2 = self.visit(ctx.expression(2))
        return IterationStatementNode("For", left, middle1, middle2, right)

    def visitJumpStatement(self, ctx:CmmParser.JumpStatementContext):
        if ctx.Continue():
            return ContinueNode()
        if ctx.Break():
            return BreakNode()
        if ctx.expression():
            return ReturnNode(self.visit(ctx.expression()))    
        return ReturnNode(None)

    # Overloaded print function for the AST
    # Writes AST tree to a dot file
    def toDot(self, ctx:CmmParser.ProgramContext):
        print("A dot file with name ", self.name, " was created.")
        astStringFormat = 'digraph G { '
        astStringFormat += str(self.visitProgram(ctx))
        astStringFormat += '}'
        output = open(self.name, 'w')
        output.write(astStringFormat)
        output.close()
