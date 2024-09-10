def encrypt(p, k):
    sk = keyGeneration(k)
    for i in range(0, 8):
        p = round(p, sk[i * 6], sk[i * 6 + 1], sk[i * 6 + 2],
                  sk[i * 6 + 3], sk[i * 6 + 4], sk[i * 6 + 5])
        # print(hex(p))
    p = finalRound(p, sk[48], sk[49], sk[50], sk[51])
    return p
