def encrypt(K, k, S, PT):
    PT = [struct.unpack('>I', struct.pack('<I', x))[0] for x in PT]
    R = [PT[i] ^ K[i] for i in range(4)]

    for r in range(ROUNDS):
        NR = [0, 0, 0, 0]
        FR0, FR1 = F(R[0], R[1], r, K, k, S)
        NR[2] = ROR(R[2] ^ FR0, 1)
        NR[3] = ROL(R[3], 1) ^ FR1
        NR[0] = R[0]
        NR[1] = R[1]
        R = NR
        if r < ROUNDS - 1:
            R[0], R[2] = R[2], R[0]
            R[1], R[3] = R[3], R[1]

    R = [R[2], R[3], R[0], R[1]]
    R = [R[(i+2) % 4] ^ K[i+4] for i in range(4)]
    R = [struct.unpack('>I', struct.pack('<I', x))[0] for x in R]
    return R
