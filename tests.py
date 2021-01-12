from lisp import parse
expr = parse("(nick \"foo\" \"salt\")")
for item in expr.tokens:
    jjj = jjj + str(type(item)).replace("classes.", "").replace("<class", "").replace("'", "").replace(">", "") + ","
print(expr._children)



