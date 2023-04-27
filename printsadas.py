
f = open("x.png", 'rb').read()
print(f)

g = open("new.png", "wb")
g.write(f)
