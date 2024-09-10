def decrypt(c, k):
    sk = keyGeneration(k)
    sk = invKeyGeneration(sk)
    for i in range(0, 8):
        c = round(c, sk[i * 6], sk[i * 6 + 1], sk[i * 6 + 2],
                  sk[i * 6 + 3], sk[i * 6 + 4], sk[i * 6 + 5])
        # print(hex(c))
    c = finalRound(c, sk[48], sk[49], sk[50], sk[51])
    return c
