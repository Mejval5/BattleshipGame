from lisp import parse
expr = parse("(start \"hash\")")
jjj = ""
for item in expr.tokens:
    jjj = jjj + str(type(item)).replace("classes.", "").replace("<class", "").replace("'", "").replace(">", "") + ","
print(jjj)
