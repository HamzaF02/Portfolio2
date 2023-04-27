f = open("src/x.png", 'rb').read()
f = str(f).split()


g = open("new.png", "wb")
m = b''
for i in range(0, len(f)):
    m += f[i].encode()
print(m[3:-1])
g.write(m[3:-1])
