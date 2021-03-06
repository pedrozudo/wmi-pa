
# variable definitions do not exist in XADD NL

def RealVar(name):
    raise NotImplementedError()

def BooleanVar(name):
    raise NotImplementedError()

def Symbol(name):
    return "({})".format(name)

def formulaIntoEvidence(formula):
    assert(isinstance(formula, str))
    return Ite(formula, Real(1), Real(0))


# constant values
def Real(x):
    return str(float(x))

def Boolean(x):
    return "true" if x else "false"

# if-then-elses
def Ite(cond, then, else_):
    assert(isinstance(cond, str))
    assert(isinstance(then, str))
    assert(isinstance(else_, str))    
    return "(ite {} {} {})".format(cond, then, else_)


# generic n-ary operator
def bOp(a, b, op):
    assert(isinstance(a, str))
    assert(isinstance(b, str))
    assert(isinstance(op, str))
    op = " {} ".format(op.strip())
    return "({} {} {})".format(op, a, b)

# generic n-ary operator
def nOp(vals, op):
    assert(all(map(lambda x : isinstance(x, str), vals)))
    assert(isinstance(op, str))    
    op = " {} ".format(op.strip())
    return "({} {})".format(op, " ".join(vals))

# algebraic operators
            
def Plus(vals):
    return nOp(vals, "+")
    
def Minus(vals):
    return nOp(vals, "-")
    
def Times(vals):
    return nOp(vals, "*")

def Pow(a, b):
    return bOp(a, b, "^")


# boolean operators
    
def And(vals):
    return nOp(vals, "and")
        
def Or(vals):
    return nOp(vals, "or")    

def Not(a):
    return "(not {})".format(a)

def Iff(a, b):
    return bOp(a, b, "<=>")
    
def Implies(a, b):
    return bOp(a, b, "=>")

# theory relations

def LE(a, b):
    return bOp(a, b, "<=")

def LT(a, b):
    return bOp(a, b, "<")

def GE(a, b):
    return bOp(a, b, ">=")

def GT(a, b):
    return bOp(a, b, ">")

def Equals(a, b):
    return bOp(a, b, "==")


def AtMostOne(args):
    excl = []
    for i in xrange(len(args) - 1):
        for j in xrange(i+1, len(args)):
            not_both = Not(And([args[i], args[j]]))
            excl.append(not_both)
    return And(excl)
    
def ExactlyOne(terms):    
    return And([Or(terms), AtMostOne(terms)])
